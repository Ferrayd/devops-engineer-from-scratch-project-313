import logging
import random
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import (
    create_link,
    delete_link,
    get_all_links,
    get_link_by_short_code,
    get_session,
)
from app.models import ShortenedLink


logger = logging.getLogger(__name__)

router = APIRouter()


class CreateLinkRequest(BaseModel):
    original_url: HttpUrl

    class Config:
        json_schema_extra = {"example": {"original_url": "https://www.example.com/very/long/url"}}


class LinkResponse(BaseModel):
    id: int
    short_code: str
    original_url: str
    short_url: str
    created_at: str

    class Config:
        from_attributes = True


def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    short_code = "".join(random.choice(characters) for _ in range(length))
    logger.debug(f"Generated short code: {short_code}")
    return short_code


@router.post("/shorten", response_model=LinkResponse, status_code=201)
async def create_short_link(
    request: CreateLinkRequest, session: AsyncSession = Depends(get_session)
):
    original_url = str(request.original_url)
    logger.info(f"Creating short link for URL: {original_url}")

    short_code = generate_short_code()

    while await get_link_by_short_code(session, short_code):
        short_code = generate_short_code()
        logger.debug("Short code already exists, generating new one")

    try:
        link = ShortenedLink(short_code=short_code, original_url=original_url)
        created_link = await create_link(session, link)

        return LinkResponse(
            id=created_link.id,
            short_code=created_link.short_code,
            original_url=created_link.original_url,
            short_url=f"http://localhost:8080/{created_link.short_code}",
            created_at=created_link.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to create short link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create short link") from e


@router.get("/links", response_model=list[LinkResponse])
async def get_all_links_endpoint(session: AsyncSession = Depends(get_session)):
    try:
        links = await get_all_links(session)
        return [
            LinkResponse(
                id=link.id,
                short_code=link.short_code,
                original_url=link.original_url,
                short_url=f"http://localhost:8080/{link.short_code}",
                created_at=link.created_at.isoformat(),
            )
            for link in links
        ]
    except Exception as e:
        logger.error(f"Failed to fetch links: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch links") from e


@router.get("/links/{short_code}", response_model=LinkResponse)
async def get_link_info(short_code: str, session: AsyncSession = Depends(get_session)):
    logger.info(f"Fetching info for short code: {short_code}")

    try:
        link = await get_link_by_short_code(session, short_code)

        if not link:
            logger.warning(f"Short code not found: {short_code}")
            raise HTTPException(status_code=404, detail="Short link not found")

        return LinkResponse(
            id=link.id,
            short_code=link.short_code,
            original_url=link.original_url,
            short_url=f"http://localhost:8080/{short_code}",
            created_at=link.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch link") from e


@router.delete("/links/{short_code}", status_code=204)
async def delete_link_endpoint(short_code: str, session: AsyncSession = Depends(get_session)):
    logger.info(f"Deleting short link: {short_code}")

    try:
        link = await get_link_by_short_code(session, short_code)

        if not link:
            logger.warning(f"Short code not found: {short_code}")
            raise HTTPException(status_code=404, detail="Short link not found")

        await delete_link(session, link.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete link") from e
