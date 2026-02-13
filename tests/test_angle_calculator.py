import math

import numpy as np
import pytest

from app.services.angle_calculator import AngleCalculator


@pytest.fixture
def calc():
    return AngleCalculator()


class TestAngleBetweenThreePoints:
    def test_straight_line_returns_180(self, calc):
        a = np.array([0.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        c = np.array([2.0, 0.0, 0.0])
        angle = calc._angle_between_three_points(a, b, c)
        assert abs(angle - 180.0) < 0.1

    def test_right_angle_returns_90(self, calc):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 0.0, 0.0])
        c = np.array([0.0, 1.0, 0.0])
        angle = calc._angle_between_three_points(a, b, c)
        assert abs(angle - 90.0) < 0.1

    def test_acute_angle(self, calc):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 0.0, 0.0])
        c = np.array([1.0, 1.0, 0.0])
        angle = calc._angle_between_three_points(a, b, c)
        assert abs(angle - 45.0) < 0.1

    def test_obtuse_angle(self, calc):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 0.0, 0.0])
        c = np.array([-1.0, 0.001, 0.0])
        angle = calc._angle_between_three_points(a, b, c)
        assert angle > 170.0

    def test_3d_angle(self, calc):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 0.0, 0.0])
        c = np.array([0.0, 0.0, 1.0])
        angle = calc._angle_between_three_points(a, b, c)
        assert abs(angle - 90.0) < 0.1

    def test_degenerate_points_does_not_crash(self, calc):
        a = np.array([0.0, 0.0, 0.0])
        b = np.array([0.0, 0.0, 0.0])
        c = np.array([0.0, 0.0, 0.0])
        angle = calc._angle_between_three_points(a, b, c)
        assert 0 <= angle <= 180


class TestCalculateAll:
    def test_returns_all_expected_metrics(self, calc, sample_landmarks):
        landmarks = sample_landmarks["good_stance"]
        metrics = calc.calculate_all(landmarks, use_world=True)

        expected_keys = {
            "left_knee_angle",
            "right_knee_angle",
            "left_hip_angle",
            "right_hip_angle",
            "left_elbow_angle",
            "right_elbow_angle",
            "left_arm_raise",
            "right_arm_raise",
            "shoulder_tilt",
            "spinal_angle",
            "head_forward_offset",
            "stance_width_ratio",
        }
        assert set(metrics.keys()) == expected_keys

    def test_all_metrics_are_finite(self, calc, sample_landmarks):
        landmarks = sample_landmarks["good_stance"]
        metrics = calc.calculate_all(landmarks, use_world=True)
        for key, value in metrics.items():
            assert math.isfinite(value), f"{key} is not finite: {value}"

    def test_locked_knees_have_higher_angle(self, calc, sample_landmarks):
        good = sample_landmarks["good_stance"]
        locked = sample_landmarks["locked_knees"]

        good_metrics = calc.calculate_all(good, use_world=True)
        locked_metrics = calc.calculate_all(locked, use_world=True)

        # Locked knees (straight legs) should have angles closer to 180
        assert locked_metrics["left_knee_angle"] > good_metrics["left_knee_angle"]
        assert locked_metrics["right_knee_angle"] > good_metrics["right_knee_angle"]

    def test_angle_values_in_valid_range(self, calc, sample_landmarks):
        landmarks = sample_landmarks["good_stance"]
        metrics = calc.calculate_all(landmarks, use_world=True)

        angle_metrics = [
            "left_knee_angle", "right_knee_angle",
            "left_hip_angle", "right_hip_angle",
            "left_elbow_angle", "right_elbow_angle",
            "left_arm_raise", "right_arm_raise",
            "shoulder_tilt", "spinal_angle",
        ]
        for key in angle_metrics:
            assert 0 <= metrics[key] <= 180, f"{key} = {metrics[key]} out of [0, 180]"

    def test_stance_width_ratio_positive(self, calc, sample_landmarks):
        landmarks = sample_landmarks["good_stance"]
        metrics = calc.calculate_all(landmarks, use_world=True)
        assert metrics["stance_width_ratio"] > 0
