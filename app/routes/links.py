import logging
import random
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
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
    original_url: str
    short_name: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "original_url": "https://www.example.com/very/long/url",
                "short_name": "abc123",
            }
        }


class UpdateLinkRequest(BaseModel):
    original_url: str
    short_name: str


class LinkResponse(BaseModel):
    id: int
    short_name: str
    original_url: str
    created_at: str

    class Config:
        from_attributes = True


def generate_short_name(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    short_name = "".join(random.choice(characters) for _ in range(length))
    logger.debug(f"Generated short_name: {short_name}")
    return short_name


@router.get("/links")
async def get_links(session: AsyncSession = Depends(get_session)):
    try:
        links = await get_all_links(session)
        return [
            LinkResponse(
                id=link.id,
                short_name=link.short_name,
                original_url=link.original_url,
                created_at=link.created_at.isoformat(),
            )
            for link in links
        ]
    except Exception as e:
        logger.error(f"Failed to fetch links: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch links") from e


@router.post("/links")
async def create_short_link(
    request: CreateLinkRequest, session: AsyncSession = Depends(get_session)
):
    logger.info(f"Creating short link for URL: {request.original_url}")

    short_name = request.short_name or generate_short_name()

    while await get_link_by_short_name(session, short_name):
        short_name = generate_short_name()
        logger.debug("Short name already exists, generating new one")

    try:
        link = ShortenedLink(short_name=short_name, original_url=request.original_url)
        created_link = await create_link(session, link)

        return LinkResponse(
            id=created_link.id,
            short_name=created_link.short_name,
            original_url=created_link.original_url,
            created_at=created_link.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to create short link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create short link") from e


@router.get("/links/{link_id}")
async def get_link(link_id: int, session: AsyncSession = Depends(get_session)):
    logger.info(f"Fetching link with id: {link_id}")

    try:
        link = await get_link_by_id(session, link_id)

        if not link:
            logger.warning(f"Link not found: {link_id}")
            raise HTTPException(status_code=404, detail="Link not found")

        return LinkResponse(
            id=link.id,
            short_name=link.short_name,
            original_url=link.original_url,
            created_at=link.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch link") from e


@router.put("/links/{link_id}")
async def update_link_endpoint(
    link_id: int, request: UpdateLinkRequest, session: AsyncSession = Depends(get_session)
):
    logger.info(f"Updating link {link_id}")

    try:
        updated = await update_link(session, link_id, request.original_url, request.short_name)

        if not updated:
            logger.warning(f"Link not found: {link_id}")
            raise HTTPException(status_code=404, detail="Link not found")

        return LinkResponse(
            id=updated.id,
            short_name=updated.short_name,
            original_url=updated.original_url,
            created_at=updated.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update link") from e


@router.delete("/links/{link_id}")
async def delete_link_endpoint(link_id: int, session: AsyncSession = Depends(get_session)):
    logger.info(f"Deleting link: {link_id}")

    try:
        link = await get_link_by_id(session, link_id)

        if not link:
            logger.warning(f"Link not found: {link_id}")
            raise HTTPException(status_code=404, detail="Link not found")

        await delete_link(session, link_id)
        return {"detail": "Link deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete link") from e
