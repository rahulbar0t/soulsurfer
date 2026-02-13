from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class EnhancementConfig:
    """Configuration for frame enhancement operations."""

    enable_zoom: bool = True
    zoom_crop_ratio: float = 0.6  # Keep center 60% of frame

    enable_sharpen: bool = True
    sharpen_kernel_size: int = 5  # Gaussian blur kernel (must be odd)
    sharpen_sigma: float = 1.0
    sharpen_strength: float = 1.5  # Unsharp mask weight

    enable_contrast: bool = False  # CLAHE — off by default
    clahe_clip_limit: float = 2.0
    clahe_tile_grid_size: int = 8


class FrameEnhancer:
    """Enhances video frames for improved pose detection.

    Applies configurable zoom (center crop), sharpening (unsharp mask),
    and optional contrast enhancement (CLAHE) to RGB frames.
    """

    def __init__(self, config: EnhancementConfig | None = None):
        self.config = config or EnhancementConfig()
        self._clahe = None  # Lazy-initialized

    def enhance(self, image: np.ndarray) -> np.ndarray:
        """Apply all enabled enhancements to an RGB uint8 image.

        Args:
            image: RGB uint8 numpy array of shape (H, W, 3).

        Returns:
            Enhanced RGB uint8 numpy array of same dimensions as input.
        """
        result = image
        if self.config.enable_zoom:
            result = self._apply_zoom(result)
        if self.config.enable_contrast:
            result = self._apply_clahe(result)
        if self.config.enable_sharpen:
            result = self._apply_sharpen(result)
        return result

    def _apply_zoom(self, image: np.ndarray) -> np.ndarray:
        """Center-crop to zoom_crop_ratio of the frame, then resize back.

        This effectively zooms into the center of the frame where the
        surfer is typically located in surf footage.
        """
        h, w = image.shape[:2]
        ratio = self.config.zoom_crop_ratio

        # Ratio of 1.0 means no crop at all
        if ratio >= 1.0:
            return image

        # Calculate crop boundaries
        crop_h = int(h * ratio)
        crop_w = int(w * ratio)
        y_start = (h - crop_h) // 2
        x_start = (w - crop_w) // 2

        # Crop center region
        cropped = image[y_start : y_start + crop_h, x_start : x_start + crop_w]

        # Resize back to original dimensions
        resized = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
        return resized

    def _apply_sharpen(self, image: np.ndarray) -> np.ndarray:
        """Unsharp mask sharpening to enhance edges.

        Uses Gaussian blur to create a mask, then blends with the
        original to enhance edges. Helps MediaPipe detect landmarks
        more clearly in distant/blurry surf footage.
        """
        ksize = self.config.sharpen_kernel_size
        sigma = self.config.sharpen_sigma
        alpha = self.config.sharpen_strength

        blurred = cv2.GaussianBlur(image, (ksize, ksize), sigma)
        sharpened = cv2.addWeighted(image, alpha, blurred, 1.0 - alpha, 0)
        return sharpened

    def _apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE on the L channel of LAB color space.

        Improves contrast in challenging outdoor lighting by equalizing
        the luminance channel adaptively.
        """
        if self._clahe is None:
            tile = self.config.clahe_tile_grid_size
            self._clahe = cv2.createCLAHE(
                clipLimit=self.config.clahe_clip_limit,
                tileGridSize=(tile, tile),
            )

        # RGB → LAB
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Apply CLAHE to luminance
        l_enhanced = self._clahe.apply(l_channel)

        # Merge and convert back
        lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
        result = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)
        return result
