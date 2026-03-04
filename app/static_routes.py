from pathlib import Path

from fastapi import HTTPException, status
from fastapi.responses import FileResponse


async def serve_static_or_spa(full_path: str):
    public_path = Path(__file__).parent.parent / "public"

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

    index_file = public_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Not found",
    )