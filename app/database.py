import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool
from sqlmodel import SQLModel, func, select

from app.config import settings
from app.models import ShortenedLink

logger = logging.getLogger(__name__)


def get_async_database_url(database_url: str) -> str:
    """Преобразует URL БД в асинхронный формат"""
    if database_url.startswith("sqlite"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

    if database_url.startswith("postgresql://"):
        url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        url = database_url.replace("postgres://", "postgresql+asyncpg://")
    else:
        return database_url

    if "?sslmode=" in url:
        url = url.split("?sslmode=")[0]
    elif "&sslmode=" in url:
        url = url.replace("&sslmode=disable", "")
        url = url.replace("&sslmode=require", "")

    return url


async_database_url = get_async_database_url(settings.database_url)

logger.info(f"Using database: {async_database_url[:50]}...")

if async_database_url.startswith("sqlite"):
    engine = create_async_engine(
        async_database_url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_async_engine(
        async_database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        poolclass=NullPool,
    )


async def init_db():
    """Инициализация базы данных"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получить асинхронную сессию БД"""
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session


async def get_link_by_short_code(session: AsyncSession, short_code: str) -> ShortenedLink | None:
    """Получить ссылку по короткому коду"""
    logger.debug(f"Fetching link with short code: {short_code}")
    statement = select(ShortenedLink).where(ShortenedLink.short_code.ilike(short_code))
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_link_by_id(session: AsyncSession, link_id: int) -> ShortenedLink | None:
    """Получить ссылку по ID"""
    logger.debug(f"Fetching link with id: {link_id}")
    statement = select(ShortenedLink).where(ShortenedLink.id == link_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_all_links(session: AsyncSession) -> list[ShortenedLink]:
    """Получить все ссылки"""
    logger.info("Fetching all links")
    statement = select(ShortenedLink).order_by(ShortenedLink.id)
    result = await session.execute(statement)
    return result.scalars().all()


async def get_paginated_links(
    session: AsyncSession, start: int = 0, end: int = 10
) -> tuple[list[ShortenedLink], int]:
    """Получить ссылки с пагинацией"""
    logger.info(f"Fetching paginated links: start={start}, end={end}")
    count_statement = select(func.count(ShortenedLink.id))
    count_result = await session.execute(count_statement)
    total = count_result.scalar() or 0

    statement = select(ShortenedLink).order_by(ShortenedLink.id).offset(start).limit(end - start)
    result = await session.execute(statement)
    links = result.scalars().all()

    logger.info(f"Found {len(links)} links out of {total} total")
    return links, total


async def create_link(session: AsyncSession, link: ShortenedLink) -> ShortenedLink:
    """Создать новую ссылку"""
    logger.info(f"Creating link with short code: {link.short_code}")
    try:
        session.add(link)
        await session.commit()
        await session.refresh(link)
        logger.info(f"Link created successfully: {link.short_code}")
        return link
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to create link: {e}", exc_info=True)
        raise


async def update_link(
    session: AsyncSession, link_id: int, original_url: str, short_code: str
) -> ShortenedLink | None:
    """Обновить ссылку"""
    logger.info(f"Updating link {link_id}")
    try:
        link = await get_link_by_id(session, link_id)
        if not link:
            logger.warning(f"Link not found: {link_id}")
            return None

        link.original_url = original_url
        link.short_code = short_code
        await session.commit()
        await session.refresh(link)
        logger.info(f"Link updated successfully: {link_id}")
        return link
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to update link: {e}", exc_info=True)
        raise


async def delete_link(session: AsyncSession, link_id: int) -> bool:
    """Удалить ссылку"""
    logger.info(f"Deleting link: {link_id}")
    try:
        link = await get_link_by_id(session, link_id)
        if not link:
            logger.warning(f"Link not found: {link_id}")
            return False

        await session.delete(link)
        await session.commit()
        logger.info(f"Link deleted successfully: {link_id}")
        return True
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to delete link: {e}", exc_info=True)
        raise