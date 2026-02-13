class VideoProcessingError(Exception):
    """Raised when video cannot be opened or processed."""


class PoseEstimationError(Exception):
    """Raised when pose estimation fails."""


class FeedbackGenerationError(Exception):
    """Raised when the LLM feedback call fails."""
