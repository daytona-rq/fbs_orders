import aiohttp

from src.database.queries.orm import db
from src.database.models import UsersArticles
from src.wildberries.models import wb_client

async def update_user_article(chat_id: int):
    wb_token = await db.get_user_wb_token(chat_id)
    print(wb_token)
    headers = {'Authorization': wb_token}
    async with aiohttp.ClientSession(headers=headers) as session:
        payload = {
              "settings": {                      
                "cursor": {
                  "limit": 100
                },
                "filter": {
                  "withPhoto": -1
                }
              }
            }

        total = 100
        while total == 100:
            async with session.post(wb_client.card_list, json=payload) as response:
                temp: dict = await response.json()
                cursor: dict = temp.get('cursor')
                payload['settings']['cursor']['updatedAt'] = cursor['updatedAt']
                payload['settings']['cursor']['nmID'] = cursor['nmID']
                cards = temp.get('cards')
                for card in cards:
                    card_article = card.get('vendorCode')
                    await db.insert_new_article(chat_id, card_article)
                total = cursor['total']