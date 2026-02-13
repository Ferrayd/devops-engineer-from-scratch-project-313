from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool
from sqlmodel import SQLModel, func, select

from config import settings
from models import Link


def get_async_database_url(database_url: str) -> str:
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

print(f"Using database: {async_database_url[:50]}...")

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
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


async def get_link_by_id(session: AsyncSession, link_id: int) -> Link | None:
    statement = select(Link).where(Link.id == link_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_link_by_short_name(session: AsyncSession, short_name: str) -> Link | None:
    statement = select(Link).where(Link.short_name == short_name)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_all_links(session: AsyncSession) -> list[Link]:
    statement = select(Link).order_by(Link.id)
    result = await session.execute(statement)
    return result.scalars().all()


async def get_paginated_links(
    session: AsyncSession, start: int = 0, end: int = 10
) -> tuple[list[Link], int]:
    count_statement = select(func.count(Link.id))
    count_result = await session.execute(count_statement)
    total = count_result.scalar() or 0

    statement = (
        select(Link)
        .order_by(Link.id)
        .offset(start)
        .limit(end - start)
    )
    result = await session.execute(statement)
    links = result.scalars().all()

    return links, total


async def create_link(session: AsyncSession, link: Link) -> Link:
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


async def update_link(
    session: AsyncSession, link_id: int, original_url: str, short_name: str
) -> Link | None:
    link = await get_link_by_id(session, link_id)
    if not link:
        return None

    link.original_url = original_url
    link.short_name = short_name
    await session.commit()
    await session.refresh(link)
    return link


async def delete_link(session: AsyncSession, link_id: int) -> bool:
    link = await get_link_by_id(session, link_id)
    if not link:
        return False

    await session.delete(link)
    await session.commit()
    return True
