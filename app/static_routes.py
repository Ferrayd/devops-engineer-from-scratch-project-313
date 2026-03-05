from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_link_by_short_name, get_session


EXCLUDED_PATHS = {
    "api",
    "docs",
    "redoc",
    "openapi.json",
    "assets",
    "ping",
}


async def serve_static_or_spa(
    full_path: str,
    session: AsyncSession = Depends(get_session),
):
    public_path = Path(__file__).parent.parent / "public"

    first_segment = full_path.split("/")[0] if full_path else ""
    if first_segment in EXCLUDED_PATHS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    if full_path == "" or full_path == "/":
        index_file = public_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file, media_type="text/html")
        return {"message": "Welcome to Short Links API"}

    file_path = public_path / full_path

    try:
        file_path = file_path.resolve()
        public_path = public_path.resolve()

        if file_path.is_relative_to(public_path) and file_path.is_file():
            return FileResponse(file_path)
    except (ValueError, RuntimeError):
        pass

    short_code = first_segment
    if short_code and "." not in short_code:
        link = await get_link_by_short_name(session, short_code)

        if link:
            return RedirectResponse(
                url=link.original_url,
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            )

    index_file = public_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Not found",
    )
