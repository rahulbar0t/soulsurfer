import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.config import settings
from app.core.exceptions import FeedbackGenerationError
from app.models.schemas import ChatRequest, ChatResponse, SessionResponse, SessionStatus
from app.services.feedback_generator import FeedbackGenerator
from app.services.pipeline import AnalysisPipeline
from app.storage.session_store import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])

store = SessionStore()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

# Shared feedback generator for chat (reuses the same Gemini client)
_feedback_gen = FeedbackGenerator(
    api_key=settings.gemini_api_key,
    model=settings.gemini_model,
)


def _run_pipeline(
    session_id: str,
    video_path: str,
    surfer_name: str | None,
    skill_level: str | None,
):
    """Run the analysis pipeline synchronously (called as a background task)."""
    store.update_status(session_id, SessionStatus.PROCESSING)
    try:
        pipeline = AnalysisPipeline()
        report = pipeline.run(video_path, session_id, surfer_name, skill_level)
        store.save_report(session_id, report)
        logger.info("Session %s completed successfully", session_id)
    except Exception:
        logger.exception("Session %s failed", session_id)
        store.update_status(session_id, SessionStatus.FAILED, error_message=str(Exception))
    finally:
        # Clean up the uploaded video file
        try:
            Path(video_path).unlink(missing_ok=True)
        except OSError:
            pass


@router.post("/", status_code=202, response_model=SessionResponse)
async def create_session(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    surfer_name: str | None = Form(None),
    skill_level: str | None = Form(None),
):
    """Upload a surf video and start analysis."""
    # Validate file extension
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate skill level
    valid_levels = {"beginner", "intermediate", "advanced"}
    if skill_level and skill_level.lower() not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid skill_level '{skill_level}'. Must be one of: {', '.join(valid_levels)}",
        )
    if skill_level:
        skill_level = skill_level.lower()

    # Save upload to disk
    session_id = str(uuid.uuid4())
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    video_path = upload_dir / f"{session_id}{suffix}"

    with open(video_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    # Check file size
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    if file_size_mb > settings.max_video_size_mb:
        video_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=413,
            detail=f"Video too large ({file_size_mb:.1f} MB). Max: {settings.max_video_size_mb} MB",
        )

    session = store.create(
        session_id, video.filename or "unknown", surfer_name, skill_level
    )

    background_tasks.add_task(
        _run_pipeline, session_id, str(video_path), surfer_name, skill_level
    )

    return session


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get session status or full report if processing is complete."""
    record = store.get(session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")

    if record["report"] is not None:
        return record["report"]

    return SessionResponse(
        session_id=record["session_id"],
        status=record["status"],
        created_at=record["created_at"],
        video_filename=record["video_filename"],
        surfer_name=record["surfer_name"],
        skill_level=record["skill_level"],
    )


@router.post("/{session_id}/chat", response_model=ChatResponse)
async def chat_with_coach(session_id: str, body: ChatRequest):
    """Send a follow-up message to the AI coach about a completed session."""
    record = store.get(session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")

    if record["status"] != SessionStatus.COMPLETED or record["report"] is None:
        raise HTTPException(
            status_code=400,
            detail="Chat is only available after analysis is complete",
        )

    report = record["report"]
    chat_history = store.get_chat_history(session_id)

    # Convert ChatMessage objects to dicts for the feedback generator
    history_dicts = [
        {"role": msg.role, "content": msg.content} for msg in chat_history
    ]

    try:
        reply = _feedback_gen.chat(
            errors=report.aggregated_errors,
            coaching_feedback=report.coaching_feedback,
            chat_history=history_dicts,
            new_message=body.message,
            surfer_name=record.get("surfer_name"),
            skill_level=record.get("skill_level"),
        )
    except FeedbackGenerationError as e:
        logger.error("Chat failed for session %s: %s", session_id, e)
        raise HTTPException(
            status_code=502,
            detail="Failed to get a response from the AI coach. Please try again.",
        ) from e

    # Store the conversation
    store.append_chat(session_id, body.message, reply)

    return ChatResponse(reply=reply, timestamp=datetime.now(timezone.utc))
