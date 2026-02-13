import pytest

from app.models.schemas import FrameMetrics, Severity
from app.services.biomechanical_analyzer import BiomechanicalAnalyzer


@pytest.fixture
def analyzer(ideal_ranges):
    return BiomechanicalAnalyzer(ideal_ranges)


class TestAnalyzeFrame:
    def test_all_in_range_returns_no_errors(self, analyzer):
        frame = FrameMetrics(
            frame_number=0,
            timestamp_sec=0.0,
            landmarks_detected=True,
            avg_visibility=0.9,
            metrics={
                "left_knee_angle": 140.0,
                "right_knee_angle": 140.0,
                "spinal_angle": 15.0,
                "shoulder_tilt": 90.0,
            },
        )
        errors = analyzer.analyze_frame(frame)
        assert len(errors) == 0

    def test_one_metric_out_of_range(self, analyzer):
        frame = FrameMetrics(
            frame_number=5,
            timestamp_sec=1.0,
            landmarks_detected=True,
            avg_visibility=0.9,
            metrics={
                "left_knee_angle": 95.0,  # Below min of 110
                "right_knee_angle": 140.0,
            },
        )
        errors = analyzer.analyze_frame(frame)
        assert len(errors) == 1
        assert errors[0].metric == "left_knee_angle"
        assert errors[0].measured_value == 95.0
        assert errors[0].deviation == 15.0
        assert errors[0].ideal_min == 110

    def test_above_max_range(self, analyzer):
        frame = FrameMetrics(
            frame_number=10,
            timestamp_sec=2.0,
            landmarks_detected=True,
            avg_visibility=0.9,
            metrics={"spinal_angle": 50.0},  # Above max of 35
        )
        errors = analyzer.analyze_frame(frame)
        assert len(errors) == 1
        assert errors[0].metric == "spinal_angle"
        assert errors[0].deviation == 15.0

    def test_severity_low(self, analyzer):
        frame = FrameMetrics(
            frame_number=0,
            timestamp_sec=0.0,
            landmarks_detected=True,
            avg_visibility=0.9,
            metrics={"left_knee_angle": 105.0},  # 5 degrees below min (110)
        )
        errors = analyzer.analyze_frame(frame)
        assert len(errors) == 1
        assert errors[0].severity == Severity.LOW

    def test_severity_medium(self, analyzer):
        frame = FrameMetrics(
            frame_number=0,
            timestamp_sec=0.0,
            landmarks_detected=True,
            avg_visibility=0.9,
            metrics={"left_knee_angle": 90.0},  # 20 degrees below min (110)
        )
        errors = analyzer.analyze_frame(frame)
        assert len(errors) == 1
        assert errors[0].severity == Severity.MEDIUM

    def test_severity_high(self, analyzer):
        frame = FrameMetrics(
            frame_number=0,
            timestamp_sec=0.0,
            landmarks_detected=True,
            avg_visibility=0.9,
            metrics={"left_knee_angle": 70.0},  # 40 degrees below min (110)
        )
        errors = analyzer.analyze_frame(frame)
        assert len(errors) == 1
        assert errors[0].severity == Severity.HIGH

    def test_unknown_metric_ignored(self, analyzer):
        frame = FrameMetrics(
            frame_number=0,
            timestamp_sec=0.0,
            landmarks_detected=True,
            avg_visibility=0.9,
            metrics={"unknown_metric": 999.0},
        )
        errors = analyzer.analyze_frame(frame)
        assert len(errors) == 0

    def test_boundary_value_no_error(self, analyzer):
        frame = FrameMetrics(
            frame_number=0,
            timestamp_sec=0.0,
            landmarks_detected=True,
            avg_visibility=0.9,
            metrics={"left_knee_angle": 110.0},  # Exactly at min boundary
        )
        errors = analyzer.analyze_frame(frame)
        assert len(errors) == 0
