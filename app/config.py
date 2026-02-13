import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-2.5-flash", alias="GEMINI_MODEL")
    max_video_size_mb: int = Field(100, alias="MAX_VIDEO_SIZE_MB")
    frame_extraction_fps: float = Field(5.0, alias="FRAME_EXTRACTION_FPS")
    pose_model_complexity: int = Field(2, alias="POSE_MODEL_COMPLEXITY")
    min_detection_confidence: float = Field(0.5, alias="MIN_DETECTION_CONFIDENCE")
    min_tracking_confidence: float = Field(0.5, alias="MIN_TRACKING_CONFIDENCE")
    min_landmark_visibility: float = Field(0.6, alias="MIN_LANDMARK_VISIBILITY")

    # Frame enhancement
    enable_frame_enhancement: bool = Field(True, alias="ENABLE_FRAME_ENHANCEMENT")
    enhancement_zoom_enabled: bool = Field(True, alias="ENHANCEMENT_ZOOM_ENABLED")
    enhancement_zoom_crop_ratio: float = Field(0.6, alias="ENHANCEMENT_ZOOM_CROP_RATIO")
    enhancement_sharpen_enabled: bool = Field(True, alias="ENHANCEMENT_SHARPEN_ENABLED")
    enhancement_sharpen_kernel_size: int = Field(5, alias="ENHANCEMENT_SHARPEN_KERNEL_SIZE")
    enhancement_sharpen_sigma: float = Field(1.0, alias="ENHANCEMENT_SHARPEN_SIGMA")
    enhancement_sharpen_strength: float = Field(1.5, alias="ENHANCEMENT_SHARPEN_STRENGTH")
    enhancement_contrast_enabled: bool = Field(False, alias="ENHANCEMENT_CONTRAST_ENABLED")
    enhancement_clahe_clip_limit: float = Field(2.0, alias="ENHANCEMENT_CLAHE_CLIP_LIMIT")
    enhancement_clahe_tile_grid_size: int = Field(8, alias="ENHANCEMENT_CLAHE_TILE_GRID_SIZE")

    upload_dir: str = Field("./uploads", alias="UPLOAD_DIR")

    # Clip extraction
    clips_dir: str = Field("./clips", alias="CLIPS_DIR")
    clip_duration_sec: float = Field(2.0, alias="CLIP_DURATION_SEC")

    model_config = {"env_file": ".env", "extra": "ignore"}


def load_ideal_ranges(path: str | None = None) -> dict:
    if path is None:
        path = str(Path(__file__).parent.parent / "config" / "ideal_ranges.json")
    with open(path) as f:
        return json.load(f)


settings = Settings()
