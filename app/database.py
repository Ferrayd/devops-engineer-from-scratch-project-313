import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# Получаем строку подключения из переменных окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@db:5432/shortener"
)

logger.info(f"Initializing database with URL: {DATABASE_URL}")

# Для асинхронной работы используем asyncpg
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Для синхронной работы (если нужна)
if "asyncpg" in DATABASE_URL:
    # Преобразуем asyncpg URL в обычный PostgreSQL URL для синхронного engine
    sync_database_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
else:
    sync_database_url = DATABASE_URL

engine = create_engine(sync_database_url)

# Создаем SessionLocal для асинхронной работы
async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Создаем Base для моделей
Base = declarative_base()


async def init_db():
    """Инициализация базы данных"""
    try:
        logger.info("Starting database initialization")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


async def get_db():
    """Получить асинхронную сессию БД"""
    async with async_session_maker() as session:
        try:
            logger.debug("Creating new database session")
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            logger.debug("Closing database session")
            await session.close()