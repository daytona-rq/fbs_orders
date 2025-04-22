from sqlalchemy import and_, update
from sqlalchemy.future import select
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from dateutil.relativedelta import relativedelta

from src.database.models import UsersOrm, UsersArticles
from src.database.database import engine, Base, session_factory, connection
from src.telegram.bot import bot

class Orm:
    async def create_tables(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @connection
    async def user_in_db(self, chat_id: int, session):
        result = await session.execute(
            select(UsersOrm.chat_id).where(UsersOrm.chat_id == chat_id)
        )
        user_in_db = result.scalar_one_or_none()
        return user_in_db

    async def check_sub_status(self, chat_id: int, session=None) -> bool:
        """
        Проверяет статус подписки пользователя.

        Args:
            chat_id: ID чата пользователя
            session: Опциональная сессия БД (если None, создается новая)

        Returns:
            True если подписка активна, False если нет
        """
        async def _check(session):
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            result = await session.execute(
                select(UsersOrm.subscription_until).where(UsersOrm.chat_id == chat_id)
            )
            sub_data = result.scalar_one_or_none()
            return sub_data and sub_data > now_utc

        if session is not None:
            return await _check(session)

        async with session_factory() as session:
            return await _check(session)

    @connection
    async def subscribe(self, chat_id: int, session):
        chat_id = int(chat_id)
        sub_until = datetime.now(timezone.utc).replace(tzinfo=None) + relativedelta(months=1)
        await session.execute(
            update(UsersOrm)
            .where(UsersOrm.chat_id == chat_id)
            .values(subscription_until=sub_until)
        )
        await session.commit()

    @connection
    async def add_user(self, chat_id: int, session):
        user = UsersOrm(chat_id=chat_id)
        session.add(user)
        await session.commit()

    async def get_user_wb_token(self, chat_id: int) -> str:
        async with session_factory() as session:
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            
            sub_status = await self.check_sub_status(chat_id, session)

            if sub_status:
                user_token = await session.execute(
                select(UsersOrm.wb_token).where(
                    and_(
                        UsersOrm.send_notifications == True,
                        UsersOrm.subscription_until > now_utc,
                        UsersOrm.chat_id == chat_id
                        )
                    )
                )
                user_token = user_token.scalar_one_or_none()
                return user_token
            
            bot.send_message(chat_id, 'Подписка неактивна')

    @connection
    async def sub_users_list(self, session) -> List[Tuple[str, str]]:
        """
        Выбирает пользователей с активной подпиской и включёнными уведомлениями.

        Returns:
            List of tuples: Список кортежей, где каждый кортеж содержит chat_id (str) и wb_token (str).
        """
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        active_users = await session.execute(
            select(UsersOrm.chat_id, UsersOrm.wb_token).where(
                and_(
                    UsersOrm.send_notifications == True,
                    UsersOrm.subscription_until > now_utc
                    )
                )
            )
        return active_users.all()

    @connection
    async def check_trial(self, chat_id: int, session):
        user_trial_status = await session.execute(
            select(UsersOrm.trial).where(UsersOrm.chat_id == chat_id)
            )
        return user_trial_status.scalar()

    @connection
    async def base_activate_trial(self, chat_id: int, session):
        user = await session.execute(select(UsersOrm).where(UsersOrm.chat_id == chat_id))
        user = user.scalar()
        user.trial = False
        date_to = (datetime.now(timezone.utc) + relativedelta(weeks=1)).replace(tzinfo=None)
        user.subscription_until = date_to
        await session.commit()
        return date_to
    
    @connection
    async def get_notifications_status(self, chat_id: int, session) -> bool:
        notification_status = await session.execute(
            select(UsersOrm.send_notifications).where(UsersOrm.chat_id == chat_id)
        )
        return notification_status.scalar_one()
    
    @connection
    async def toggle_notifications(self, chat_id: int, session) -> None:
        await session.execute(
            update(UsersOrm)
            .where(UsersOrm.chat_id == chat_id)
            .values(send_notifications=~UsersOrm.send_notifications)
        )
        await session.commit()

    @connection
    async def upd_wb_token(self, chat_id: int, new_token: str, session) -> None:
        await session.execute(
            update(UsersOrm)
            .where(UsersOrm.chat_id == chat_id)
            .values(wb_token=new_token)
        )
        await session.commit()

    @connection
    async def insert_new_article(self, chat_id: int, article_code: str, session) -> None:
        result = await session.execute(
            select(UsersArticles).
            where(UsersArticles.article_code == article_code)
        )
        existing_article = result.scalar_one_or_none()
        if existing_article is None:
            new_article = UsersArticles(
                chat_id=chat_id,
                article_code=article_code
            )
            session.add(new_article)
            await session.commit()
    
    @connection
    async def selfcost_by_article(self, article: str, chat_id: int, session) -> int:
        result = await session.execute(
            select(UsersArticles.cost).
            where(
                and_(UsersArticles.article_code == article,
                     UsersArticles.chat_id == chat_id)
            )
        )
        result = result.scalar_one_or_none()
        return 0 if result is None else result

db = Orm()