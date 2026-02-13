from dataclasses import dataclass

import mediapipe as mp
import numpy as np


@dataclass
class PoseResult:
    landmarks: list[dict]
    world_landmarks: list[dict]
    avg_visibility: float
    detected: bool


class PoseEstimator:
    def __init__(
        self,
        model_complexity: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        min_landmark_visibility: float = 0.6,
    ):
        self.min_landmark_visibility = min_landmark_visibility
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            smooth_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process_frame(self, rgb_image: np.ndarray) -> PoseResult:
        result = self.pose.process(rgb_image)

        if not result.pose_landmarks:
            return PoseResult(
                landmarks=[], world_landmarks=[], avg_visibility=0.0, detected=False
            )

        landmarks = []
        for lm in result.pose_landmarks.landmark:
            landmarks.append(
                {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
            )

        world_landmarks = []
        for wlm in result.pose_world_landmarks.landmark:
            world_landmarks.append(
                {"x": wlm.x, "y": wlm.y, "z": wlm.z, "visibility": wlm.visibility}
            )

        avg_vis = float(np.mean([lm["visibility"] for lm in landmarks]))
        detected = avg_vis >= self.min_landmark_visibility

        return PoseResult(
            landmarks=landmarks,
            world_landmarks=world_landmarks,
            avg_visibility=avg_vis,
            detected=detected,
        )

    def close(self):
        self.pose.close()
