from aiogram import Router
from src.telegram.handlers import (
    start, 
    trial, 
    user_settings,
    menu,
    guide,
    subscription
)


def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(trial.router)
    router.include_router(menu.router)
    router.include_router(user_settings.router)
    router.include_router(guide.router)
    router.include_router(subscription.router)
    return router