from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import (
    create_link,
    delete_link,
    get_link_by_id,
    get_link_by_short_name,
    get_paginated_links,
    get_session,
    init_db,
    update_link,
)
from models import Link
from schemas import LinkCreate, LinkResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("✓ Database initialized")
    print(f"✓ CORS enabled for origins: {settings.cors_origins}")
    yield
    print("✓ Application shutting down")


app = FastAPI(
    title="Short Links API",
    description="API для создания и управления короткими ссылками",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


def parse_range_header(range_header: Optional[str]) -> tuple[int, int]:
    if not range_header:
        return 0, 10
    
    try:
        cleaned = range_header.strip("[]")
        parts = cleaned.split(",")
        if len(parts) != 2:
            return 0, 10
        
        start = int(parts[0].strip())
        end = int(parts[1].strip())
        
        if start < 0:
            start = 0
        if end <= start:
            end = start + 10
        
        return start, end
    except (ValueError, IndexError):
        return 0, 10


def format_link_response(link: Link) -> dict:
    return {
        "id": link.id,
        "original_url": link.original_url,
        "short_name": link.short_name,
        "short_url": f"{settings.short_url_base}/{link.short_name}",
    }


@app.get("/ping")
async def ping():
    return "pong"


@app.get("/api/links")
async def list_links(
    range: Optional[str] = Query(None, description="Диапазон в формате [start,end]"),
    session: AsyncSession = Depends(get_session),
):

    start, end = parse_range_header(range)
    
    links, total = await get_paginated_links(session, start, end)
    
    response_data = [format_link_response(link) for link in links]
    
    if total > 0:
        actual_end = min(end - 1, total - 1)
    else:
        actual_end = start
    
    content_range = f"links {start}-{actual_end}/{total}"
    
    return JSONResponse(
        content=response_data,
        headers={
            "Content-Range": content_range,
            "Accept-Ranges": "links",
        },
    )


@app.post("/api/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(
    link_data: LinkCreate, session: AsyncSession = Depends(get_session)
):
    existing = await get_link_by_short_name(session, link_data.short_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Short name already exists",
        )
    
    new_link = Link(
        original_url=str(link_data.original_url),
        short_name=link_data.short_name,
    )
    
    try:
        created_link = await create_link(session, new_link)
        return LinkResponse(
            id=created_link.id,
            original_url=created_link.original_url,
            short_name=created_link.short_name,
            short_url=f"{settings.short_url_base}/{created_link.short_name}",
            created_at=created_link.created_at,
        )
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Short name already exists",
        )


@app.get("/api/links/{link_id}", response_model=LinkResponse)
async def get_link(link_id: int, session: AsyncSession = Depends(get_session)):
    link = await get_link_by_id(session, link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )
    
    return LinkResponse(
        id=link.id,
        original_url=link.original_url,
        short_name=link.short_name,
        short_url=f"{settings.short_url_base}/{link.short_name}",
        created_at=link.created_at,
    )


@app.put("/api/links/{link_id}", response_model=LinkResponse)
async def update_short_link(
    link_id: int,
    link_data: LinkCreate,
    session: AsyncSession = Depends(get_session),
):
    existing_link = await get_link_by_id(session, link_id)
    if not existing_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )
    
    if link_data.short_name != existing_link.short_name:
        conflicting = await get_link_by_short_name(session, link_data.short_name)
        if conflicting:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Short name already exists",
            )
    
    try:
        updated_link = await update_link(
            session,
            link_id,
            str(link_data.original_url),
            link_data.short_name,
        )
        return LinkResponse(
            id=updated_link.id,
            original_url=updated_link.original_url,
            short_name=updated_link.short_name,
            short_url=f"{settings.short_url_base}/{updated_link.short_name}",
            created_at=updated_link.created_at,
        )
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Short name already exists",
        )


@app.delete("/api/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_short_link(link_id: int, session: AsyncSession = Depends(get_session)):
    success = await delete_link(session, link_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found",
        )