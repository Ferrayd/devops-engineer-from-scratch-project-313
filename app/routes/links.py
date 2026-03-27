import logging
import random
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ShortenedLink


logger = logging.getLogger(__name__)

router = APIRouter()


class CreateLinkRequest(BaseModel):
    original_url: HttpUrl

    class Config:
        json_schema_extra = {"example": {"original_url": "https://www.example.com/very/long/url"}}


class LinkResponse(BaseModel):
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
async def create_short_link(request: CreateLinkRequest, db: Session = Depends(get_db)):
    original_url = str(request.original_url)
    logger.info(f"Creating short link for URL: {original_url}")

    existing_link = (
        db.query(ShortenedLink).filter(ShortenedLink.original_url == original_url).first()
    )

    if existing_link:
        logger.info(f"Link already exists with short code: {existing_link.short_code}")
        return LinkResponse(
            short_code=existing_link.short_code,
            original_url=existing_link.original_url,
            short_url=f"http://localhost:8000/{existing_link.short_code}",
            created_at=existing_link.created_at.isoformat(),
        )

    short_code = generate_short_code()

    while db.query(ShortenedLink).filter(ShortenedLink.short_code == short_code).first():
        short_code = generate_short_code()
        logger.debug("Short code already exists, generating new one")

    try:
        new_link = ShortenedLink(short_code=short_code, original_url=original_url)
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        logger.info(f"Short link created successfully: {short_code}")

        return LinkResponse(
            short_code=short_code,
            original_url=original_url,
            short_url=f"http://localhost:8000/{short_code}",
            created_at=new_link.created_at.isoformat(),
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create short link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create short link") from e


@router.get("/links", response_model=list[LinkResponse])
async def get_all_links(db: Session = Depends(get_db)):
    logger.info("Fetching all shortened links")
    try:
        links = db.query(ShortenedLink).all()
        logger.info(f"Found {len(links)} links")
        return [
            LinkResponse(
                short_code=link.short_code,
                original_url=link.original_url,
                short_url=f"http://localhost:8000/{link.short_code}",
                created_at=link.created_at.isoformat(),
            )
            for link in links
        ]
    except Exception as e:
        logger.error(f"Failed to fetch links: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch links") from e


@router.get("/links/{short_code}", response_model=LinkResponse)
async def get_link_info(short_code: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching info for short code: {short_code}")

    link = db.query(ShortenedLink).filter(ShortenedLink.short_code == short_code).first()

    if not link:
        logger.warning(f"Short code not found: {short_code}")
        raise HTTPException(status_code=404, detail="Short link not found")

    return LinkResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=f"http://localhost:8000/{short_code}",
        created_at=link.created_at.isoformat(),
    )


@router.delete("/links/{short_code}", status_code=204)
async def delete_link(short_code: str, db: Session = Depends(get_db)):
    logger.info(f"Deleting short link: {short_code}")

    link = db.query(ShortenedLink).filter(ShortenedLink.short_code == short_code).first()

    if not link:
        logger.warning(f"Short code not found: {short_code}")
        raise HTTPException(status_code=404, detail="Short link not found")

    try:
        db.delete(link)
        db.commit()
        logger.info(f"Short link deleted successfully: {short_code}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete link") from e
