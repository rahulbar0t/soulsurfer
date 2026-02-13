from app.models.schemas import FrameError, FrameMetrics, Severity


class BiomechanicalAnalyzer:
    def __init__(self, ideal_ranges: dict):
        """
        Args:
            ideal_ranges: Dict loaded from ideal_ranges.json. Each key is a metric
                name mapping to {"min", "max", "severity_thresholds": {"medium", "high"}}.
        """
        self.ideal_ranges = ideal_ranges

    def _classify_severity(self, deviation: float, thresholds: dict) -> Severity:
        if deviation >= thresholds.get("high", 30):
            return Severity.HIGH
        if deviation >= thresholds.get("medium", 15):
            return Severity.MEDIUM
        return Severity.LOW

    def analyze_frame(self, frame_metrics: FrameMetrics) -> list[FrameError]:
        errors: list[FrameError] = []

        for metric_name, value in frame_metrics.metrics.items():
            if metric_name not in self.ideal_ranges:
                continue

            ideal = self.ideal_ranges[metric_name]
            ideal_min = ideal["min"]
            ideal_max = ideal["max"]

            if value < ideal_min:
                deviation = ideal_min - value
            elif value > ideal_max:
                deviation = value - ideal_max
            else:
                continue

            severity = self._classify_severity(
                deviation, ideal.get("severity_thresholds", {})
            )

            errors.append(
                FrameError(
                    metric=metric_name,
                    measured_value=round(value, 1),
                    ideal_min=ideal_min,
                    ideal_max=ideal_max,
                    deviation=round(deviation, 1),
                    frame_number=frame_metrics.frame_number,
                    timestamp_sec=round(frame_metrics.timestamp_sec, 2),
                    severity=severity,
                )
            )

        return errors
