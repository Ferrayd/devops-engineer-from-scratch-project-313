import logging
import random
import string

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import (
    create_link,
    delete_link,
    get_all_links,
    get_link_by_id,
    get_link_by_short_name,
    get_session,
    update_link,
)
from app.models import ShortenedLink


logger = logging.getLogger(__name__)

router = APIRouter()


class CreateLinkRequest(BaseModel):
    """Модель для создания сокращенной ссылки"""

    original_url: str = Field(..., min_length=1)
    short_name: str = Field(..., min_length=1, max_length=255)

    class Config:
        json_schema_extra = {
            "example": {
                "original_url": "https://www.example.com/very/long/url",
                "short_name": "abc123",
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
    short_name = "".join(random.choice(characters) for _ in range(length))
    logger.debug(f"Generated short_name: {short_name}")
    return short_name


# РЕДИРЕКТ - ПЕРВЫЙ ENDPOINT!
@router.get("/r/{short_name}")
async def redirect_to_original(short_name: str, session: AsyncSession = Depends(get_session)):
    """Редирект по короткой ссылке на оригинальный URL"""
    logger.info(f"GET /r/{short_name}")

    try:
        link = await get_link_by_short_name(session, short_name)

        if not link:
            logger.warning(f"Short link not found: {short_name}")
            raise HTTPException(status_code=404, detail="Short link not found")

        logger.info(f"Redirecting {short_name} to {link.original_url}")
        return RedirectResponse(url=link.original_url, status_code=301)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to redirect {short_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to redirect") from e


@router.get("/links")
async def get_links(
    session: AsyncSession = Depends(get_session),
    range: str = Query(None),
    filter: str = Query(None),
    sort: str = Query(None),
):
    """Получить все сокращенные ссылки с поддержкой пагинации"""
    try:
        logger.debug(f"GET /api/links - range: {range}, filter: {filter}, sort: {sort}")

        links = await get_all_links(session)
        logger.debug(f"Total links fetched: {len(links)}")

        total = len(links)

        start = 0
        end = total

        if range:
            try:
                range_str = range.strip("[]")
                start, end = map(int, range_str.split(","))
                logger.debug(f"Parsed range: start={start}, end={end}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse range '{range}': {e}")
                pass

        paginated_links = links[start:end]
        logger.debug(f"Paginated links count: {len(paginated_links)}")

        response_data = []
        for link in paginated_links:
            try:
                response_data.append(
                    LinkResponse(
                        id=link.id,
                        short_name=link.short_name,
                        original_url=link.original_url,
                        short_url=f"/r/{link.short_name}",
                    )
                )
            except Exception as e:
                logger.error(f"Failed to map link {link.id}: {e}", exc_info=True)

        logger.info(
            f"Returning {len(response_data)} links with range=[{start},{end}], total={total}"
        )

        from fastapi.responses import JSONResponse

        return JSONResponse(
            content=[link.model_dump() for link in response_data],
            headers={"Content-Range": f"items {start}-{end}/{total}"},
        )
    except Exception as e:
        logger.error(f"Failed to fetch links: {e}", exc_info=True)
        import traceback

        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch links: {str(e)}") from e


@router.post("/links", status_code=201)
async def create_short_link(
    request: CreateLinkRequest, session: AsyncSession = Depends(get_session)
):
    """Создать сокращенную ссылку"""
    try:
        logger.info(
            f"POST /api/links - original_url: {request.original_url}, short_name: {request.short_name}"
        )

        original_url = request.original_url
        short_name = request.short_name

        logger.info(f"Creating short link: {short_name} -> {original_url}")

        # Проверяем, не занято ли имя
        existing = await get_link_by_short_name(session, short_name)
        if existing:
            logger.warning(f"Short name already exists: {short_name}")
            raise HTTPException(status_code=400, detail=f"Short name '{short_name}' already exists")

        link = ShortenedLink(short_name=short_name, original_url=original_url)
        created_link = await create_link(session, link)

        response = LinkResponse(
            id=created_link.id,
            short_name=created_link.short_name,
            original_url=created_link.original_url,
            short_url=f"/r/{created_link.short_name}",
        )

        logger.info(f"Link created successfully: id={created_link.id}, short_name={short_name}")
        return response

    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=e.errors()) from e
    except Exception as e:
        logger.error(f"Failed to create short link: {e}", exc_info=True)
        import traceback

        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create short link: {str(e)}") from e


@router.get("/links/{link_id}")
async def get_link(link_id: int, session: AsyncSession = Depends(get_session)):
    """Получить информацию о ссылке по ID"""
    logger.info(f"GET /api/links/{link_id}")

    try:
        link = await get_link_by_id(session, link_id)

        if not link:
            logger.warning(f"Link not found: {link_id}")
            raise HTTPException(status_code=404, detail="Link not found")

        return LinkResponse(
            id=link.id,
            short_name=link.short_name,
            original_url=link.original_url,
            short_url=f"/r/{link.short_name}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch link {link_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch link") from e


@router.put("/links/{link_id}")
async def update_link_endpoint(
    link_id: int, request: UpdateLinkRequest, session: AsyncSession = Depends(get_session)
):
    """Обновить ссылку"""
    logger.info(f"PUT /api/links/{link_id}")

    try:
        logger.debug(
            f"Request: original_url={request.original_url}, short_name={request.short_name}"
        )

        original_url = request.original_url
        short_name = request.short_name

        updated = await update_link(session, link_id, original_url, short_name)

        if not updated:
            logger.warning(f"Link not found: {link_id}")
            raise HTTPException(status_code=404, detail="Link not found")

        return LinkResponse(
            id=updated.id,
            short_name=updated.short_name,
            original_url=updated.original_url,
            short_url=f"/r/{updated.short_name}",
        )
    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=e.errors()) from e
    except Exception as e:
        logger.error(f"Failed to update link {link_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update link") from e


@router.delete("/links/{link_id}", status_code=204)
async def delete_link_endpoint(link_id: int, session: AsyncSession = Depends(get_session)):
    """Удалить ссылку"""
    logger.info(f"DELETE /api/links/{link_id}")

    try:
        link = await get_link_by_id(session, link_id)

        if not link:
            logger.warning(f"Link not found: {link_id}")
            raise HTTPException(status_code=404, detail="Link not found")

        await delete_link(session, link_id)
        logger.info(f"Link deleted: {link_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete link {link_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete link") from e
