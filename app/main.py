import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info("Surf Coach API starting up")
    yield
    logging.getLogger(__name__).info("Surf Coach API shutting down")


app = FastAPI(
    title="Virtual Surf Coach API",
    description="Upload surf videos for AI-powered biomechanical analysis and coaching feedback.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# Mount static directories for clips and reference images
clips_path = Path(settings.clips_dir)
clips_path.mkdir(parents=True, exist_ok=True)
app.mount("/clips", StaticFiles(directory=str(clips_path)), name="clips")

references_path = Path("./references")
references_path.mkdir(parents=True, exist_ok=True)
app.mount("/references", StaticFiles(directory=str(references_path)), name="references")
