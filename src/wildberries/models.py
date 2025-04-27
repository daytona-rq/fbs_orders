import aiohttp
import aiofiles
import asyncio
import json
from datetime import date
from pathlib import Path

from src.database.queries.orm import db
from src.redis import redis

jsons_path = Path(__file__).parent / "jsons"

class WB_APIclient:

    new_orders: str = 'https://marketplace-api.wildberries.ru/api/v3/orders/new'
    commission: str = 'https://common-api.wildberries.ru/api/v1/tariffs/commission'
    card_list: str = 'https://content-api.wildberries.ru/content/v2/get/cards/list'
    price: str = 'https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter'
    box_logistics: str = 'https://common-api.wildberries.ru/api/v1/tariffs/box'

    async def check_response_status(self, status_code: int):
        if status_code == 400:
            print('<400> Проверьте синтаксис запроса')

        if status_code == 401:
            print('<401> Пользователь не авторизован')

        if status_code == 403:
            print('<403> Доступ запрещён')

        if status_code == 429:
            print('<429> Слишком много запросов') 

    async def _request(
                self,
                session: aiohttp.ClientSession, 
                link: str, 
                file_name: str = '',
                params: dict = {},
                save_file: bool = False
                ) -> dict:
        async with await session.get(link, params=params) as response:
            await self.check_response_status(response.status)
            response_text: str = await response.text()
            temp: dict = json.loads(response_text)
            if save_file:
                async with aiofiles.open(jsons_path / f"{file_name}.json", 'w') as fp:
                    await fp.write(json.dumps(temp))
        return temp

    async def upd_logistic_cost_json(self, session: aiohttp.ClientSession) -> None:
        params = {'date': f'{date.today()}'}
        await self._request(
                            session=session,
                            link=self.box_logistics,
                            file_name='logistics',
                            params=params, 
                            save_file=True
                            )
        
    async def upd_group_commission_json(self, session: aiohttp.ClientSession) -> None:
        await self._request(
                            session=session, 
                            link=self.commission, 
                            file_name='commission',
                            save_file=True
                            )

    async def item_price(self, session: aiohttp.ClientSession, order: dict) -> float:
        params: dict = {
            'limit': 10,
            'filterNmID': order['nmId']
        }
        response = await self._request(session, self.price, 'price', params)
        item_price = response['data']['listGoods'][0]['sizes'][0]['discountedPrice']
        await asyncio.sleep(0.6)
        return float(item_price)
    
    async def get_new_orders(self, session: aiohttp.ClientSession) -> list:
        orders: dict = await self._request(session, self.new_orders)
        return orders['orders']
    

wb_client = WB_APIclient()


class Card:

    tax = 7 
    
    def __init__(self):
        self.volume = 0
        self.article = ""
        self.subject_id = 0
        self.price_before_spp: float = 0.0
        self.wb_commission: float = 0.0
        self.cost_tax: float = 0.0
        self.logistic_cost: float = 0.0
        self.profit: float = 0.0
        self.selfcost: float = 0.0

    @classmethod
    async def create(cls, session: aiohttp.ClientSession, order:dict, chat_id: int):
        self = cls()

        nmId = order.get('nmId')
        params = {
            'settings': {
                'filter': {"withPhoto": -1, 'textSearch': str(nmId)}}}
        async with session.post(wb_client.card_list, json=params) as response:
            data = await response.json()
            self.cur_card = data.get('cards', [{}])[0]

            dimensions: dict = self.cur_card.get('dimensions')
            self.volume = await self.calculate_volume(**dimensions)
            self.article = self.cur_card.get('vendorCode')

            self.selfcost = await db.selfcost_by_article(self.article, chat_id)

            self.subject_id = self.cur_card.get('subjectID')

            self.price_before_spp = await wb_client.item_price(session, order)
        
            self.wb_commission = await self.calc_wb_commission(self.subject_id, self.price_before_spp)

            self.cost_tax = round(self.price_before_spp * Card.tax / 100, 2)

            self.logistic_cost = await self.calc_logistic_cost()
            self.profit = round(
                self.price_before_spp - self.wb_commission - self.logistic_cost - self.cost_tax - self.selfcost, 2)
        
        return self

    async def calc_logistic_cost(self) -> float:
        logistic_file_path = jsons_path / "logistics.json"
        async with aiofiles.open(logistic_file_path, "r", encoding="utf-8") as file:
            content = await file.read()
            logistic_data = json.loads(content)['response']['data']['warehouseList'][0]
            base_delivery = float(logistic_data['boxDeliveryBase'].replace(',', '.'))
            liter_delivery = float(logistic_data['boxDeliveryLiter'].replace(',', '.'))
            logistic_cost = round(base_delivery + (self.volume - 1) * liter_delivery, 2)
        return logistic_cost

    async def calc_wb_commission(self, subject_id: int, price_before_spp: float) -> float:
        commission_file_path = jsons_path / "commission.json"

        async with aiofiles.open(commission_file_path, 'r') as file:
            content = await file.read()
            commission_list = json.loads(content)['report']

            commission_item = next((item for item in commission_list if item['subjectID'] == subject_id), None)
            if commission_item is None:
                raise ValueError(f"subject_id {subject_id} не найден в файле")

            commission_coef = commission_item['kgvpMarketplace']
            cost_commission = (commission_coef * price_before_spp) / 100
            return round(cost_commission, 2)

    @staticmethod
    async def calculate_volume(length: int,
                     width: int,
                     height: int,
                     **kwargs) -> float:
        volume = length * width * height / 1000
        return max(volume, 1)

    async def get_daily_profit(self, chat_id: int) -> float:
        today = date.today().isoformat()
        stats_key = f"user_stats:{chat_id}:{today}"

        day_profit = await redis.hget(stats_key, "daily_profit")
        return round(float(day_profit), 2) if day_profit else 0.0

    async def create_report(self, chat_id: int) -> str:
        
        report = f"""Поступил <b>новый заказ</b> по системе Маркетплейс (FBS)
        <b>Артикул продавца:</b> {self.article}
        <b>Цена продажи до СПП:</b> {self.price_before_spp}₽
        <b>Себестоимость:</b> {self.selfcost}₽
        <b>Комиссия Wildberries:</b> {self.wb_commission}₽
        <b>Логистика:</b> {self.logistic_cost}₽
        <b>Налог:</b> {self.cost_tax}₽
        <b>Ожидаемая прибыль с продажи:</b> {self.profit}₽
        <b>Приблизительная прибыль за день:</b> {await self.get_daily_profit(chat_id)}₽"""
    
        return report