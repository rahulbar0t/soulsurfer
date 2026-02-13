import numpy as np


class AngleCalculator:
    """Calculates biomechanical metrics from MediaPipe pose landmarks."""

    # MediaPipe landmark indices
    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def _to_vec(self, landmark: dict) -> np.ndarray:
        return np.array([landmark["x"], landmark["y"], landmark["z"]])

    def _angle_between_three_points(
        self, a: np.ndarray, b: np.ndarray, c: np.ndarray
    ) -> float:
        """Angle at vertex B formed by points A-B-C. Returns degrees [0, 180]."""
        ba = a - b
        bc = c - b
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_angle)))

    def _midpoint(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return (a + b) / 2.0

    def _angle_from_vertical(self, top: np.ndarray, bottom: np.ndarray) -> float:
        """Angle of line top→bottom relative to vertical. 0=upright, 90=horizontal."""
        direction = top - bottom
        vertical = np.array([0, -1, 0])
        cos_angle = np.dot(direction, vertical) / (np.linalg.norm(direction) + 1e-8)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_angle)))

    def calculate_all(
        self, landmarks: list[dict], use_world: bool = True
    ) -> dict[str, float]:
        """
        Calculate all biomechanical metrics from 33 landmarks.

        Args:
            landmarks: List of 33 dicts with x, y, z, visibility.
            use_world: True if landmarks are world coordinates (preferred).

        Returns:
            Dict mapping metric name to measured value.
        """
        lm = landmarks
        metrics: dict[str, float] = {}

        # Joint angles (3-point)
        # Knee: HIP → KNEE → ANKLE
        metrics["left_knee_angle"] = self._angle_between_three_points(
            self._to_vec(lm[self.LEFT_HIP]),
            self._to_vec(lm[self.LEFT_KNEE]),
            self._to_vec(lm[self.LEFT_ANKLE]),
        )
        metrics["right_knee_angle"] = self._angle_between_three_points(
            self._to_vec(lm[self.RIGHT_HIP]),
            self._to_vec(lm[self.RIGHT_KNEE]),
            self._to_vec(lm[self.RIGHT_ANKLE]),
        )

        # Hip: SHOULDER → HIP → KNEE
        metrics["left_hip_angle"] = self._angle_between_three_points(
            self._to_vec(lm[self.LEFT_SHOULDER]),
            self._to_vec(lm[self.LEFT_HIP]),
            self._to_vec(lm[self.LEFT_KNEE]),
        )
        metrics["right_hip_angle"] = self._angle_between_three_points(
            self._to_vec(lm[self.RIGHT_SHOULDER]),
            self._to_vec(lm[self.RIGHT_HIP]),
            self._to_vec(lm[self.RIGHT_KNEE]),
        )

        # Elbow: SHOULDER → ELBOW → WRIST
        metrics["left_elbow_angle"] = self._angle_between_three_points(
            self._to_vec(lm[self.LEFT_SHOULDER]),
            self._to_vec(lm[self.LEFT_ELBOW]),
            self._to_vec(lm[self.LEFT_WRIST]),
        )
        metrics["right_elbow_angle"] = self._angle_between_three_points(
            self._to_vec(lm[self.RIGHT_SHOULDER]),
            self._to_vec(lm[self.RIGHT_ELBOW]),
            self._to_vec(lm[self.RIGHT_WRIST]),
        )

        # Arm raise / shoulder abduction: HIP → SHOULDER → ELBOW
        metrics["left_arm_raise"] = self._angle_between_three_points(
            self._to_vec(lm[self.LEFT_HIP]),
            self._to_vec(lm[self.LEFT_SHOULDER]),
            self._to_vec(lm[self.LEFT_ELBOW]),
        )
        metrics["right_arm_raise"] = self._angle_between_three_points(
            self._to_vec(lm[self.RIGHT_HIP]),
            self._to_vec(lm[self.RIGHT_SHOULDER]),
            self._to_vec(lm[self.RIGHT_ELBOW]),
        )

        # Shoulder tilt: angle of shoulder line from horizontal (2D projection)
        l_sh = self._to_vec(lm[self.LEFT_SHOULDER])
        r_sh = self._to_vec(lm[self.RIGHT_SHOULDER])
        shoulder_vec = r_sh - l_sh
        horizontal = np.array([1.0, 0.0])
        cos_tilt = np.dot(shoulder_vec[:2], horizontal) / (
            np.linalg.norm(shoulder_vec[:2]) + 1e-8
        )
        cos_tilt = np.clip(cos_tilt, -1.0, 1.0)
        metrics["shoulder_tilt"] = float(np.degrees(np.arccos(cos_tilt)))

        # Spinal angle: mid-shoulder to mid-hip deviation from vertical
        mid_shoulder = self._midpoint(l_sh, r_sh)
        mid_hip = self._midpoint(
            self._to_vec(lm[self.LEFT_HIP]),
            self._to_vec(lm[self.RIGHT_HIP]),
        )
        metrics["spinal_angle"] = self._angle_from_vertical(mid_shoulder, mid_hip)

        # Head forward offset: Z-distance of nose from mid-shoulder (world coords)
        nose = self._to_vec(lm[self.NOSE])
        head_offset_vec = nose - mid_shoulder
        if use_world:
            metrics["head_forward_offset"] = float(head_offset_vec[2])
        else:
            metrics["head_forward_offset"] = float(head_offset_vec[1])

        # Stance width ratio: ankle distance / hip width
        l_ankle = self._to_vec(lm[self.LEFT_ANKLE])
        r_ankle = self._to_vec(lm[self.RIGHT_ANKLE])
        l_hip = self._to_vec(lm[self.LEFT_HIP])
        r_hip = self._to_vec(lm[self.RIGHT_HIP])
        hip_width = np.linalg.norm(l_hip - r_hip) + 1e-8
        ankle_width = np.linalg.norm(l_ankle - r_ankle)
        metrics["stance_width_ratio"] = float(ankle_width / hip_width)

        return metrics
