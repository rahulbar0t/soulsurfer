import pytest

from app.models.schemas import FrameError, Severity
from app.services.error_aggregator import ErrorAggregator


def _make_error(
    metric: str = "left_knee_angle",
    measured: float = 95.0,
    deviation: float = 15.0,
    frame: int = 0,
    timestamp: float = 0.0,
    severity: Severity = Severity.MEDIUM,
) -> FrameError:
    return FrameError(
        metric=metric,
        measured_value=measured,
        ideal_min=110,
        ideal_max=170,
        deviation=deviation,
        frame_number=frame,
        timestamp_sec=timestamp,
        severity=severity,
    )


class TestAggregate:
    def test_empty_errors(self):
        agg = ErrorAggregator(total_frames_analyzed=100)
        result = agg.aggregate([])
        assert result == []

    def test_single_error_produces_one_aggregated(self):
        agg = ErrorAggregator(total_frames_analyzed=100)
        errors = [_make_error(frame=0, timestamp=0.0)]
        result = agg.aggregate(errors)
        assert len(result) == 1
        assert result[0].metric == "left_knee_angle"
        assert result[0].frame_count == 1
        assert result[0].frequency_pct == 1.0

    def test_100_identical_errors_collapse_to_one(self):
        agg = ErrorAggregator(total_frames_analyzed=100)
        errors = [
            _make_error(frame=i, timestamp=i * 0.2) for i in range(100)
        ]
        result = agg.aggregate(errors)
        assert len(result) == 1
        assert result[0].frame_count == 100
        assert result[0].frequency_pct == 100.0
        assert result[0].duration_sec == pytest.approx(19.8, abs=0.1)

    def test_two_different_metrics_produce_two_aggregated(self):
        agg = ErrorAggregator(total_frames_analyzed=50)
        errors = [
            _make_error(metric="left_knee_angle", frame=i, timestamp=i * 0.2)
            for i in range(30)
        ] + [
            _make_error(metric="spinal_angle", frame=i, timestamp=i * 0.2,
                        measured=45.0, deviation=10.0)
            for i in range(20)
        ]
        result = agg.aggregate(errors)
        assert len(result) == 2

    def test_priority_sorting(self):
        agg = ErrorAggregator(total_frames_analyzed=100)
        # High severity, 90% frequency, 20 deviation -> highest priority
        high_errors = [
            _make_error(metric="left_knee_angle", frame=i, timestamp=i * 0.2,
                        deviation=20.0, severity=Severity.HIGH)
            for i in range(90)
        ]
        # Medium severity, 50% frequency, 10 deviation -> lower priority
        med_errors = [
            _make_error(metric="spinal_angle", frame=i, timestamp=i * 0.2,
                        deviation=10.0, severity=Severity.MEDIUM)
            for i in range(50)
        ]
        result = agg.aggregate(high_errors + med_errors)
        assert result[0].metric == "left_knee_angle"
        assert result[1].metric == "spinal_angle"

    def test_avg_and_max_deviation(self):
        agg = ErrorAggregator(total_frames_analyzed=3)
        errors = [
            _make_error(deviation=10.0, frame=0, timestamp=0.0),
            _make_error(deviation=20.0, frame=1, timestamp=0.2),
            _make_error(deviation=30.0, frame=2, timestamp=0.4),
        ]
        result = agg.aggregate(errors)
        assert result[0].avg_deviation == 20.0
        assert result[0].max_deviation == 30.0

    def test_zero_total_frames(self):
        agg = ErrorAggregator(total_frames_analyzed=0)
        result = agg.aggregate([])
        assert result == []
