from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MetricName(str, Enum):
    LEFT_KNEE_ANGLE = "left_knee_angle"
    RIGHT_KNEE_ANGLE = "right_knee_angle"
    LEFT_HIP_ANGLE = "left_hip_angle"
    RIGHT_HIP_ANGLE = "right_hip_angle"
    LEFT_ELBOW_ANGLE = "left_elbow_angle"
    RIGHT_ELBOW_ANGLE = "right_elbow_angle"
    LEFT_ARM_RAISE = "left_arm_raise"
    RIGHT_ARM_RAISE = "right_arm_raise"
    SHOULDER_TILT = "shoulder_tilt"
    SPINAL_ANGLE = "spinal_angle"
    HEAD_FORWARD_OFFSET = "head_forward_offset"
    STANCE_WIDTH_RATIO = "stance_width_ratio"


# --- Frame-level data ---


class FrameMetrics(BaseModel):
    frame_number: int
    timestamp_sec: float
    landmarks_detected: bool
    avg_visibility: float
    metrics: dict[str, float]


# --- Error models ---


class FrameError(BaseModel):
    """A single metric error on a single frame (pre-aggregation)."""

    metric: str
    measured_value: float
    ideal_min: float
    ideal_max: float
    deviation: float
    frame_number: int
    timestamp_sec: float
    severity: Severity


class AggregatedError(BaseModel):
    """An error collapsed across multiple frames into one finding."""

    metric: str
    severity: Severity
    avg_measured_value: float
    ideal_min: float
    ideal_max: float
    avg_deviation: float
    max_deviation: float
    frame_count: int
    total_frames_analyzed: int
    frequency_pct: float
    first_timestamp_sec: float
    last_timestamp_sec: float
    duration_sec: float
    # Worst frame data for clip extraction
    worst_frame_number: int
    worst_timestamp_sec: float
    worst_measured_value: float
    clip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None


# --- Session models ---


class SessionResponse(BaseModel):
    session_id: str
    status: SessionStatus
    created_at: datetime
    video_filename: str
    surfer_name: Optional[str] = None
    skill_level: Optional[str] = None


class SessionReport(BaseModel):
    session_id: str
    status: SessionStatus
    total_frames: int
    analyzed_frames: int
    skipped_frames: int
    video_duration_sec: float
    video_fps: float
    aggregated_errors: list[AggregatedError]
    coaching_feedback: str
    created_at: datetime
    processing_time_sec: float


# --- Chat models ---


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    timestamp: datetime
