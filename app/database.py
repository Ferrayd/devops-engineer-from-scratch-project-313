import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# Получаем строку подключения из переменных окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./shortener.db"
)

logger.info(f"Initializing database with URL: {DATABASE_URL}")

# Создаем engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Создаем SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем Base для моделей
Base = declarative_base()


async def init_db():
    """Инициализация базы данных"""
    try:
        logger.info("Starting database initialization")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def get_db() -> Session:
    """Получить сессию БД"""
    db = SessionLocal()
    try:
        logger.debug("Creating new database session")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        logger.debug("Closing database session")
        db.close()