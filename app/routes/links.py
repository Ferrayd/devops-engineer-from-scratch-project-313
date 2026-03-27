import logging
import string
import random
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from app.database import (
    get_session,
    get_link_by_short_name,
    get_link_by_id,
    get_all_links,
    create_link,
    update_link,
    delete_link,
)
from app.models import ShortenedLink

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateLinkRequest(BaseModel):
    """Модель для создания сокращенной ссылки"""
    original_url: str = Field(..., min_length=1)  # Обязательное поле
    short_name: Optional[str] = Field(None, min_length=1, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_url": "https://www.example.com/very/long/url",
                "short_name": "abc123"
            }
        }


class UpdateLinkRequest(BaseModel):
    """Модель для обновления ссылки"""
    original_url: str = Field(..., min_length=1)
    short_name: str = Field(..., min_length=1, max_length=255)


class LinkResponse(BaseModel):
    """Модель ответа со ссылкой"""
    id: int
    short_name: str
    original_url: str
    short_url: str
    
    class Config:
        from_attributes = True


def generate_short_name(length: int = 8) -> str:
    """Генерирует случайное короткое имя"""
    characters = string.ascii_letters + string.digits
    short_name = ''.join(random.choice(characters) for _ in range(length))
    logger.debug(f"Generated short_name: {short_name}")
    return short_name


@router.get("/links")
async def get_links(session: AsyncSession = Depends(get_session)):
    """Получить все сокращенные ссылки"""
    try:
        links = await get_all_links(session)
        return [
            LinkResponse(
                id=link.id,
                short_name=link.short_name,
                original_url=link.original_url,
                short_url=f"/r/{link.short_name}"
            )
            for link in links
        ]
    except Exception as e:
        logger.error(f"Failed to fetch links: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch links"
        ) from e


@router.post("/links", status_code=201)
async def create_short_link(
    request: CreateLinkRequest,
    session: AsyncSession = Depends(get_session)
):
    """Создать сокращенную ссылку"""
    logger.info(f"Creating short link for URL: {request.original_url}")
    
    # Генерируем короткое имя если не указано
    short_name = request.short_name or generate_short_name()
    
    # Проверяем, не занято ли имя
    while await get_link_by_short_name(session, short_name):
        short_name = generate_short_name()
        logger.debug("Short name already exists, generating new one")
    
    try:
        link = ShortenedLink(
            short_name=short_name,
            original_url=request.original_url
        )
        created_link = await create_link(session, link)
        
        return LinkResponse(
            id=created_link.id,
            short_name=created_link.short_name,
            original_url=created_link.original_url,
            short_url=f"/r/{created_link.short_name}"
        )
    except Exception as e:
        logger.error(f"Failed to create short link: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to create short link"
        ) from e


@router.get("/links/{link_id}")
async def get_link(link_id: int, session: AsyncSession = Depends(get_session)):
    """Получить информацию о ссылке по ID"""
    logger.info(f"Fetching link with id: {link_id}")
    
    try:
        link = await get_link_by_id(session, link_id)
        
        if not link:
            logger.warning(f"Link not found: {link_id}")
            raise HTTPException(
                status_code=404,
                detail="Link not found"
            )
        
        return LinkResponse(
            id=link.id,
            short_name=link.short_name,
            original_url=link.original_url,
            short_url=f"/r/{link.short_name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch link: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch link"
        ) from e


@router.put("/links/{link_id}")
async def update_link_endpoint(
    link_id: int,
    request: UpdateLinkRequest,
    session: AsyncSession = Depends(get_session)
):
    """Обновить ссылку"""
    logger.info(f"Updating link {link_id}")
    
    try:
        updated = await update_link(
            session,
            link_id,
            request.original_url,
            request.short_name
        )
        
        if not updated:
            logger.warning(f"Link not found: {link_id}")
            raise HTTPException(
                status_code=404,
                detail="Link not found"
            )
        
        return LinkResponse(
            id=updated.id,
            short_name=updated.short_name,
            original_url=updated.original_url,
            short_url=f"/r/{updated.short_name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update link: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to update link"
        ) from e


@router.delete("/links/{link_id}", status_code=204)
async def delete_link_endpoint(link_id: int, session: AsyncSession = Depends(get_session)):
    """Удалить ссылку"""
    logger.info(f"Deleting link: {link_id}")
    
    try:
        link = await get_link_by_id(session, link_id)
        
        if not link:
            logger.warning(f"Link not found: {link_id}")
            raise HTTPException(
                status_code=404,
                detail="Link not found"
            )
        
        await delete_link(session, link_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete link: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to delete link"
        ) from e