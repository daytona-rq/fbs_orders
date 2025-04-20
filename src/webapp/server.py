from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from decimal import Decimal, ROUND_HALF_UP
import hmac
import hashlib
import os
from pathlib import Path
from contextlib import asynccontextmanager

from src.database.models import UsersArticles, Base
from src.database.database import engine, async_session_maker
from src.wildberries.upd_articles import update_user_article
from src.yookassa_dir.yookassa_ import router as yookassa_router

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(yookassa_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

class ArticleResponse(BaseModel):
    id: int
    article_code: str
    cost: float = Field(..., ge=0, json_schema_extra={"example": 123.45})

class ArticleUpdate(BaseModel):
    cost: float = Field(..., ge=0, description="Цена должна быть ≥ 0")

    @field_validator('cost', mode='before')
    @classmethod
    def ensure_float(cls, v) -> float:
        if isinstance(v, str):
            v = v.replace(',', '.')  # Поддержка обоих разделителей
        try:
            return float(Decimal(str(v)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))
        except (TypeError, ValueError):
            raise ValueError("Цена должна быть числом")

def verify_telegram_webapp(data_check_string: str, hash: str) -> bool:
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

async def get_db():
    async with async_session_maker() as session:
        yield session

@app.get("/", include_in_schema=False)
async def serve_webapp(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "static_url_path": "/static"}
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
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")
    
    await update_user_article(chat_id)
    
    try:
        query = select(UsersArticles).where(UsersArticles.chat_id == chat_id)
        if search:
            query = query.where(UsersArticles.article_code.ilike(f"%{search}%"))
        
        result = await db.execute(query.order_by(UsersArticles.article_code))
        articles = result.scalars().all()
        # Гарантируем двузначное отображение
        for article in articles:
            article.cost = float(Decimal(str(article.cost)).quantize(Decimal('0.00')))
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Явное преобразование с округлением
        cost_value = float(Decimal(str(data.cost)).quantize(Decimal('0.00')))
        
        stmt = (
            update(UsersArticles)
            .where(UsersArticles.id == article_id)
            .values(cost=cost_value)
            .returning(UsersArticles)
        )
        
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        await db.commit()
        # Возвращаем отформатированное значение
        article.cost = float(Decimal(str(article.cost)).quantize(Decimal('0.00')))
        return article
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))