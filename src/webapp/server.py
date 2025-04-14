from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List
import hmac
import hashlib
import os
from pathlib import Path
from contextlib import asynccontextmanager

# Импорты из вашего проекта
from src.database.models import UsersArticles, Base
from src.database.database import engine, async_session_maker
from src.wildberries.upd_articles import update_user_article

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

# Получаем абсолютный путь к директории static
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для теста. В продакшене укажите домен бота
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы (теперь с правильным путем)
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

# Шаблоны
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Модели Pydantic
class ArticleResponse(BaseModel):
    id: int
    article_code: str
    cost: int

class ArticleUpdate(BaseModel):
    cost: int

# Вспомогательные функции
def verify_telegram_webapp(data_check_string: str, hash: str) -> bool:
    """Валидация данных Telegram WebApp"""
    secret_key = hmac.new(
        key="WebAppData".encode(),
        msg=BOT_TOKEN.encode(),
        digestmod=hashlib.sha256
    ).digest()
    
    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return computed_hash == hash

# Зависимости
async def get_db():
    """Генератор сессий БД"""
    async with async_session_maker() as session:
        yield session

# Роуты
@app.get("/", include_in_schema=False)
async def serve_webapp(request: Request):
    """Главная страница WebApp"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "static_url_path": "/static"
        }
    )

@app.get("/api/products", response_model=List[ArticleResponse])
async def get_products_alias(
    search: str = "", 
    chat_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    return await get_articles(search=search, chat_id=chat_id, db=db)

@app.post("/api/auth/validate")
async def validate_webapp(request: Request):
    """Валидация Telegram WebApp"""
    form_data = await request.form()
    try:
        if not verify_telegram_webapp(
            form_data.get("_auth", ""),
            form_data.get("hash", "")
        ):
            raise ValueError("Invalid Telegram WebApp data")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.get("/api/articles", response_model=List[ArticleResponse])
async def get_articles(
    search: str = "", 
    chat_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """Получение списка товаров"""
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")
    
    await update_user_article(chat_id)
    
    try:
        query = select(UsersArticles).where(UsersArticles.chat_id == chat_id)
        if search:
            query = query.where(UsersArticles.article_code.ilike(f"%{search}%"))
        
        result = await db.execute(query.order_by(UsersArticles.article_code))
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление себестоимости товара"""
    try:
        stmt = (
            update(UsersArticles)
            .where(UsersArticles.id == article_id)
            .values(cost=data.cost)
            .returning(UsersArticles)
        )
        
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        await db.commit()
        return article
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))