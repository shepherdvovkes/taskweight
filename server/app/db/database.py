import os
import asyncio
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки подключения к базе данных
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://taskweight_user:taskweight_password@localhost:5432/taskweight"
)

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем синхронный движок для миграций
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    echo=os.getenv("DEBUG", "False").lower() == "true"
)

# Создаем асинхронный движок для работы приложения
async_engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=os.getenv("DEBUG", "False").lower() == "true",
    pool_pre_ping=True,
    pool_recycle=300
)

# Создаем фабрику сессий
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Метаданные для создания таблиц
metadata = MetaData()

async def get_db_session() -> AsyncSession:
    """Получает сессию базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Инициализирует базу данных"""
    async with async_engine.begin() as conn:
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Закрывает соединения с базой данных"""
    await async_engine.dispose()

def check_db_connection():
    """Проверяет подключение к базе данных"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return False
