from dataclasses import dataclass
from typing import Generator

import cv2
import numpy as np

from app.core.exceptions import VideoProcessingError
from app.services.frame_enhancer import FrameEnhancer


@dataclass
class VideoFrame:
    image: np.ndarray  # RGB image
    frame_number: int
    timestamp_sec: float


@dataclass
class VideoMetadata:
    fps: float
    total_frames: int
    width: int
    height: int
    duration_sec: float


class VideoProcessor:
    def __init__(self, target_fps: float = 5.0, enhancer: FrameEnhancer | None = None):
        self.target_fps = target_fps
        self.enhancer = enhancer

    def get_metadata(self, video_path: str) -> VideoMetadata:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise VideoProcessingError(f"Cannot open video: {video_path}")
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total / fps if fps > 0 else 0.0
            return VideoMetadata(
                fps=fps, total_frames=total, width=w, height=h, duration_sec=duration
            )
        finally:
            cap.release()

    def extract_frames(self, video_path: str) -> Generator[VideoFrame, None, None]:
        metadata = self.get_metadata(video_path)
        if metadata.fps <= 0:
            raise VideoProcessingError(f"Invalid FPS ({metadata.fps}) in video")

        frame_skip = max(1, int(metadata.fps / self.target_fps))
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise VideoProcessingError(f"Cannot open video: {video_path}")

        frame_number = 0
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_number % frame_skip == 0:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    if self.enhancer is not None:
                        rgb = self.enhancer.enhance(rgb)
                    timestamp = frame_number / metadata.fps
                    yield VideoFrame(
                        image=rgb,
                        frame_number=frame_number,
                        timestamp_sec=timestamp,
                    )
                frame_number += 1
        finally:
            cap.release()
