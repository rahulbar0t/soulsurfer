from collections import defaultdict

from app.models.schemas import AggregatedError, FrameError, Severity


class ErrorAggregator:
    SEVERITY_WEIGHT = {"low": 1, "medium": 2, "high": 3}

    def __init__(self, total_frames_analyzed: int):
        self.total_frames = total_frames_analyzed

    def aggregate(self, frame_errors: list[FrameError]) -> list[AggregatedError]:
        if not frame_errors or self.total_frames == 0:
            return []

        by_metric: dict[str, list[FrameError]] = defaultdict(list)
        for err in frame_errors:
            by_metric[err.metric].append(err)

        aggregated: list[AggregatedError] = []

        for metric, errors in by_metric.items():
            errors.sort(key=lambda e: e.frame_number)

            deviations = [e.deviation for e in errors]
            timestamps = [e.timestamp_sec for e in errors]

            # Find the frame with maximum deviation (for clip extraction)
            max_dev_idx = deviations.index(max(deviations))
            worst_error = errors[max_dev_idx]

            # Determine overall severity: highest severity appearing in >25% of
            # error frames for this metric
            severity_counts: dict[Severity, int] = defaultdict(int)
            for e in errors:
                severity_counts[e.severity] += 1

            overall_severity = Severity.LOW
            for sev in [Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
                if severity_counts[sev] / len(errors) > 0.25:
                    overall_severity = sev
                    break

            agg = AggregatedError(
                metric=metric,
                severity=overall_severity,
                avg_measured_value=round(
                    sum(e.measured_value for e in errors) / len(errors), 1
                ),
                ideal_min=errors[0].ideal_min,
                ideal_max=errors[0].ideal_max,
                avg_deviation=round(sum(deviations) / len(deviations), 1),
                max_deviation=round(max(deviations), 1),
                frame_count=len(errors),
                total_frames_analyzed=self.total_frames,
                frequency_pct=round(len(errors) / self.total_frames * 100, 1),
                first_timestamp_sec=round(min(timestamps), 2),
                last_timestamp_sec=round(max(timestamps), 2),
                duration_sec=round(max(timestamps) - min(timestamps), 2),
                # Worst frame data for clip extraction
                worst_frame_number=worst_error.frame_number,
                worst_timestamp_sec=round(worst_error.timestamp_sec, 2),
                worst_measured_value=round(worst_error.measured_value, 1),
            )
            aggregated.append(agg)

        # Sort by priority: severity_weight * frequency * avg_deviation
        aggregated.sort(
            key=lambda a: (
                self.SEVERITY_WEIGHT[a.severity.value]
                * a.frequency_pct
                * a.avg_deviation
            ),
            reverse=True,
        )

        return aggregated
