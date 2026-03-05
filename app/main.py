from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routes import (
    create_short_link,
    delete_short_link,
    get_link,
    list_links,
    ping,
    update_short_link,
    redirect_short_link,
)
from app.schemas import LinkResponse
from app.static_routes import serve_static_or_spa


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("✓ Database initialized")
    print(f"✓ CORS enabled for origins: {settings.cors_origins}")
    yield
    print("✓ Application shutting down")


app = FastAPI(
    title="Short Links API",
    description="REST API для создания и управления короткими ссылками",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


public_path = Path(__file__).parent.parent / "public"
if public_path.exists():
    app.mount("/assets", StaticFiles(directory=str(public_path / "assets")), name="assets")


app.get("/ping")(ping)

app.get("/api/links")(list_links)

app.post("/api/links", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)(
    create_short_link
)

app.get("/api/links/{link_id}", response_model=LinkResponse)(get_link)

app.put("/api/links/{link_id}", response_model=LinkResponse)(update_short_link)

app.delete("/api/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)(
    delete_short_link
)

app.get("/{short_code}")(redirect_short_link)

app.get("/{full_path:path}")(serve_static_or_spa)