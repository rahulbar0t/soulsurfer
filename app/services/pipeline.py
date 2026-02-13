import logging
import time
from datetime import datetime, timezone

from app.config import load_ideal_ranges, settings
from app.core.exceptions import VideoProcessingError
from app.models.schemas import FrameError, FrameMetrics, SessionReport, SessionStatus
from app.services.angle_calculator import AngleCalculator
from app.services.biomechanical_analyzer import BiomechanicalAnalyzer
from app.services.clip_extractor import ClipExtractor
from app.services.error_aggregator import ErrorAggregator
from app.services.feedback_generator import FeedbackGenerator
from app.services.frame_enhancer import EnhancementConfig, FrameEnhancer
from app.services.pose_estimator import PoseEstimator
from app.services.video_processor import VideoProcessor

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    def __init__(self):
        # Build frame enhancer from settings (if enabled)
        enhancer = None
        if settings.enable_frame_enhancement:
            enhancer = FrameEnhancer(
                EnhancementConfig(
                    enable_zoom=settings.enhancement_zoom_enabled,
                    zoom_crop_ratio=settings.enhancement_zoom_crop_ratio,
                    enable_sharpen=settings.enhancement_sharpen_enabled,
                    sharpen_kernel_size=settings.enhancement_sharpen_kernel_size,
                    sharpen_sigma=settings.enhancement_sharpen_sigma,
                    sharpen_strength=settings.enhancement_sharpen_strength,
                    enable_contrast=settings.enhancement_contrast_enabled,
                    clahe_clip_limit=settings.enhancement_clahe_clip_limit,
                    clahe_tile_grid_size=settings.enhancement_clahe_tile_grid_size,
                )
            )
            logger.info("Frame enhancement enabled (zoom=%s, sharpen=%s, contrast=%s)",
                settings.enhancement_zoom_enabled,
                settings.enhancement_sharpen_enabled,
                settings.enhancement_contrast_enabled,
            )

        self.video_processor = VideoProcessor(
            target_fps=settings.frame_extraction_fps,
            enhancer=enhancer,
        )
        self.angle_calculator = AngleCalculator()
        self.analyzer = BiomechanicalAnalyzer(load_ideal_ranges())
        self.feedback_gen = FeedbackGenerator(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
        self.clip_extractor = ClipExtractor(
            clip_duration_sec=settings.clip_duration_sec,
            output_dir=settings.clips_dir,
        )

    def run(
        self,
        video_path: str,
        session_id: str,
        surfer_name: str | None = None,
        skill_level: str | None = None,
    ) -> SessionReport:
        start_time = time.time()

        # Step 0: Video metadata
        metadata = self.video_processor.get_metadata(video_path)
        logger.info(
            "Processing video: %.1fs, %d frames, %.0f FPS",
            metadata.duration_sec,
            metadata.total_frames,
            metadata.fps,
        )

        # Step 1: Extract frames → pose estimation → angle calculation
        pose_estimator = PoseEstimator(
            model_complexity=settings.pose_model_complexity,
            min_detection_confidence=settings.min_detection_confidence,
            min_tracking_confidence=settings.min_tracking_confidence,
            min_landmark_visibility=settings.min_landmark_visibility,
        )

        all_frame_metrics: list[FrameMetrics] = []
        all_frame_errors: list[FrameError] = []
        landmarks_by_frame: dict[int, list[dict]] = {}  # For clip extraction
        skipped = 0

        try:
            for video_frame in self.video_processor.extract_frames(video_path):
                pose_result = pose_estimator.process_frame(video_frame.image)

                if not pose_result.detected:
                    skipped += 1
                    continue

                # Store landmarks for clip extraction (normalized coords)
                landmarks_by_frame[video_frame.frame_number] = pose_result.landmarks

                metrics = self.angle_calculator.calculate_all(
                    pose_result.world_landmarks, use_world=True
                )

                frame_metrics = FrameMetrics(
                    frame_number=video_frame.frame_number,
                    timestamp_sec=video_frame.timestamp_sec,
                    landmarks_detected=True,
                    avg_visibility=pose_result.avg_visibility,
                    metrics=metrics,
                )
                all_frame_metrics.append(frame_metrics)

                # Step 2: Compare against ideal ranges
                errors = self.analyzer.analyze_frame(frame_metrics)
                all_frame_errors.extend(errors)
        finally:
            pose_estimator.close()

        logger.info(
            "Pose analysis complete: %d frames analyzed, %d skipped, %d raw errors",
            len(all_frame_metrics),
            skipped,
            len(all_frame_errors),
        )

        # Step 2b: Aggregate errors
        aggregator = ErrorAggregator(total_frames_analyzed=len(all_frame_metrics))
        aggregated_errors = aggregator.aggregate(all_frame_errors)

        logger.info("Aggregated into %d findings", len(aggregated_errors))

        # Step 2c: Extract video clips with spotlight highlighting
        if aggregated_errors:
            aggregated_errors = self.clip_extractor.extract_all_clips(
                video_path, session_id, aggregated_errors, landmarks_by_frame
            )
            logger.info("Extracted %d error clips", len(aggregated_errors))

        # Step 3: Generate coaching feedback via Gemini
        coaching_feedback = self.feedback_gen.generate_feedback(
            aggregated_errors, surfer_name, skill_level
        )

        elapsed = time.time() - start_time

        return SessionReport(
            session_id=session_id,
            status=SessionStatus.COMPLETED,
            total_frames=metadata.total_frames,
            analyzed_frames=len(all_frame_metrics),
            skipped_frames=skipped,
            video_duration_sec=metadata.duration_sec,
            video_fps=metadata.fps,
            aggregated_errors=aggregated_errors,
            coaching_feedback=coaching_feedback,
            created_at=datetime.now(timezone.utc),
            processing_time_sec=round(elapsed, 2),
        )
