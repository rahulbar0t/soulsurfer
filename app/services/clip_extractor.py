"""
Video clip extraction service with spotlight overlay.
Extracts 1-2 second clips around error frames and draws spotlight on joints.
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.models.schemas import AggregatedError

logger = logging.getLogger(__name__)


@dataclass
class SpotlightConfig:
    """Configuration for spotlight overlay effect."""

    radius: int = 40  # Spotlight radius in pixels
    color: tuple = (0, 255, 255)  # Yellow in BGR
    thickness: int = 3  # Circle line thickness
    glow_radius: int = 60  # Outer glow radius
    glow_alpha: float = 0.3  # Glow transparency


# Mapping from metric name to primary landmark index(es) for spotlight
# Based on MediaPipe pose landmark indices
METRIC_LANDMARK_MAP: dict[str, list[int]] = {
    "left_knee_angle": [25],  # LEFT_KNEE
    "right_knee_angle": [26],  # RIGHT_KNEE
    "left_hip_angle": [23],  # LEFT_HIP
    "right_hip_angle": [24],  # RIGHT_HIP
    "left_elbow_angle": [13],  # LEFT_ELBOW
    "right_elbow_angle": [14],  # RIGHT_ELBOW
    "left_arm_raise": [11],  # LEFT_SHOULDER
    "right_arm_raise": [12],  # RIGHT_SHOULDER
    "shoulder_tilt": [11, 12],  # Both shoulders
    "spinal_angle": [11, 12, 23, 24],  # Shoulder and hip midpoints
    "head_forward_offset": [0],  # NOSE
    "stance_width_ratio": [27, 28],  # Both ankles
}


class ClipExtractor:
    """Extracts video clips with spotlight overlay for error visualization."""

    def __init__(
        self,
        clip_duration_sec: float = 2.0,
        output_dir: str = "./clips",
        spotlight_config: Optional[SpotlightConfig] = None,
    ):
        self.clip_duration_sec = clip_duration_sec
        self.output_dir = Path(output_dir)
        self.spotlight_config = spotlight_config or SpotlightConfig()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_landmark_pixel_coords(
        self,
        landmarks: list[dict],
        landmark_indices: list[int],
        frame_width: int,
        frame_height: int,
    ) -> list[tuple[int, int]]:
        """Convert normalized landmark coords to pixel coordinates."""
        coords = []
        for idx in landmark_indices:
            if idx < len(landmarks):
                lm = landmarks[idx]
                x = int(lm["x"] * frame_width)
                y = int(lm["y"] * frame_height)
                coords.append((x, y))
        return coords

    def _compute_spotlight_coords(
        self,
        landmarks: list[dict],
        metric: str,
        frame_width: int,
        frame_height: int,
    ) -> list[tuple[int, int]]:
        """Get spotlight coordinates for a metric, handling special cases."""
        indices = METRIC_LANDMARK_MAP.get(metric, [])
        if not indices:
            return []

        # Special case: spinal_angle uses midpoints
        if metric == "spinal_angle" and len(indices) == 4:
            l_sh = landmarks[indices[0]]
            r_sh = landmarks[indices[1]]
            l_hip = landmarks[indices[2]]
            r_hip = landmarks[indices[3]]

            mid_shoulder_x = int((l_sh["x"] + r_sh["x"]) / 2 * frame_width)
            mid_shoulder_y = int((l_sh["y"] + r_sh["y"]) / 2 * frame_height)
            mid_hip_x = int((l_hip["x"] + r_hip["x"]) / 2 * frame_width)
            mid_hip_y = int((l_hip["y"] + r_hip["y"]) / 2 * frame_height)

            return [(mid_shoulder_x, mid_shoulder_y), (mid_hip_x, mid_hip_y)]

        return self._get_landmark_pixel_coords(
            landmarks, indices, frame_width, frame_height
        )

    def _draw_spotlight(
        self,
        frame: np.ndarray,
        landmark_coords: list[tuple[int, int]],
    ) -> np.ndarray:
        """Draw spotlight circles on the frame at landmark positions."""
        cfg = self.spotlight_config
        result = frame.copy()

        for x, y in landmark_coords:
            # Draw outer glow (semi-transparent)
            overlay = result.copy()
            cv2.circle(overlay, (x, y), cfg.glow_radius, cfg.color, -1)
            result = cv2.addWeighted(
                overlay, cfg.glow_alpha, result, 1 - cfg.glow_alpha, 0
            )

            # Draw main spotlight ring
            cv2.circle(result, (x, y), cfg.radius, cfg.color, cfg.thickness)

            # Draw inner dot
            cv2.circle(result, (x, y), 5, cfg.color, -1)

        return result

    def extract_clip(
        self,
        video_path: str,
        session_id: str,
        error: AggregatedError,
        landmarks_by_frame: dict[int, list[dict]],
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Extract a clip around the worst frame with spotlight overlay.

        Args:
            video_path: Path to source video
            session_id: Session ID for naming
            error: AggregatedError with worst_frame_number and worst_timestamp_sec
            landmarks_by_frame: Dict mapping frame_number to landmarks list

        Returns:
            Tuple of (clip_relative_path, thumbnail_relative_path) or (None, None)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video: {video_path}")
            return None, None

        writer = None
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_sec = total_frames / fps if fps > 0 else 0

            # Calculate clip boundaries (half duration before, half after worst frame)
            half_duration = self.clip_duration_sec / 2
            center_time = error.worst_timestamp_sec
            start_time = max(0, center_time - half_duration)
            end_time = min(duration_sec, center_time + half_duration)

            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)

            # Setup output paths
            clip_filename = f"{session_id}_{error.metric}_clip.mp4"
            thumb_filename = f"{session_id}_{error.metric}_thumb.jpg"
            clip_path = self.output_dir / clip_filename
            thumb_path = self.output_dir / thumb_filename

            # Setup video writer (try H.264 first, fallback to mp4v)
            fourcc = cv2.VideoWriter_fourcc(*"avc1")
            writer = cv2.VideoWriter(str(clip_path), fourcc, fps, (width, height))
            if not writer.isOpened():
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(clip_path), fourcc, fps, (width, height))

            if not writer.isOpened():
                logger.error(f"Cannot create video writer for {clip_path}")
                return None, None

            thumbnail_saved = False
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            current_frame = start_frame
            while current_frame <= end_frame:
                ret, frame = cap.read()
                if not ret:
                    break

                # Apply spotlight if we have landmarks for this frame
                if current_frame in landmarks_by_frame:
                    landmarks = landmarks_by_frame[current_frame]
                    coords = self._compute_spotlight_coords(
                        landmarks, error.metric, width, height
                    )
                    if coords:
                        frame = self._draw_spotlight(frame, coords)

                writer.write(frame)

                # Save thumbnail at the worst frame
                if current_frame == error.worst_frame_number and not thumbnail_saved:
                    cv2.imwrite(str(thumb_path), frame)
                    thumbnail_saved = True

                current_frame += 1

            # If we didn't hit exact worst frame, save thumbnail from middle of clip
            if not thumbnail_saved:
                cap.set(cv2.CAP_PROP_POS_FRAMES, (start_frame + end_frame) // 2)
                ret, frame = cap.read()
                if ret:
                    # Apply spotlight to thumbnail too
                    middle_frame = (start_frame + end_frame) // 2
                    if middle_frame in landmarks_by_frame:
                        landmarks = landmarks_by_frame[middle_frame]
                        coords = self._compute_spotlight_coords(
                            landmarks, error.metric, width, height
                        )
                        if coords:
                            frame = self._draw_spotlight(frame, coords)
                    cv2.imwrite(str(thumb_path), frame)

            logger.info(
                f"Extracted clip for {error.metric}: frames {start_frame}-{end_frame}"
            )

            # Return relative paths for storage
            return f"/clips/{clip_filename}", f"/clips/{thumb_filename}"

        except Exception as e:
            logger.exception(f"Error extracting clip for {error.metric}: {e}")
            return None, None

        finally:
            if writer is not None:
                writer.release()
            cap.release()

    def extract_all_clips(
        self,
        video_path: str,
        session_id: str,
        errors: list[AggregatedError],
        landmarks_by_frame: dict[int, list[dict]],
    ) -> list[AggregatedError]:
        """
        Extract clips for all errors and return updated errors with clip paths.
        """
        updated_errors = []

        for error in errors:
            clip_path, thumb_path = self.extract_clip(
                video_path, session_id, error, landmarks_by_frame
            )

            # Create a new error with clip paths set
            error_dict = error.model_dump()
            error_dict["clip_path"] = clip_path
            error_dict["thumbnail_path"] = thumb_path
            updated_errors.append(AggregatedError(**error_dict))

        return updated_errors
