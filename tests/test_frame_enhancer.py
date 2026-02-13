import numpy as np
import pytest

from app.services.frame_enhancer import EnhancementConfig, FrameEnhancer


@pytest.fixture
def sample_image():
    """A simple 100x200 RGB test image with a white rectangle in the center."""
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    img[30:70, 60:140] = 200
    return img


@pytest.fixture
def default_enhancer():
    return FrameEnhancer()


@pytest.fixture
def zoom_only():
    return FrameEnhancer(EnhancementConfig(
        enable_zoom=True, zoom_crop_ratio=0.5,
        enable_sharpen=False, enable_contrast=False,
    ))


@pytest.fixture
def sharpen_only():
    return FrameEnhancer(EnhancementConfig(
        enable_zoom=False, enable_sharpen=True, enable_contrast=False,
    ))


@pytest.fixture
def contrast_only():
    return FrameEnhancer(EnhancementConfig(
        enable_zoom=False, enable_sharpen=False, enable_contrast=True,
    ))


@pytest.fixture
def all_disabled():
    return FrameEnhancer(EnhancementConfig(
        enable_zoom=False, enable_sharpen=False, enable_contrast=False,
    ))


class TestOutputFormat:
    def test_output_shape_matches_input(self, default_enhancer, sample_image):
        result = default_enhancer.enhance(sample_image)
        assert result.shape == sample_image.shape

    def test_output_dtype_is_uint8(self, default_enhancer, sample_image):
        result = default_enhancer.enhance(sample_image)
        assert result.dtype == np.uint8

    def test_input_not_mutated(self, default_enhancer, sample_image):
        original = sample_image.copy()
        default_enhancer.enhance(sample_image)
        np.testing.assert_array_equal(sample_image, original)

    def test_various_resolutions(self, default_enhancer):
        for h, w in [(480, 640), (720, 1280), (1080, 1920), (50, 50)]:
            img = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
            result = default_enhancer.enhance(img)
            assert result.shape == (h, w, 3)
            assert result.dtype == np.uint8


class TestZoom:
    def test_preserves_dimensions(self, zoom_only, sample_image):
        result = zoom_only.enhance(sample_image)
        assert result.shape == sample_image.shape

    def test_changes_content(self, zoom_only, sample_image):
        result = zoom_only.enhance(sample_image)
        assert not np.array_equal(result, sample_image)

    def test_ratio_1_is_identity(self, sample_image):
        enhancer = FrameEnhancer(EnhancementConfig(
            enable_zoom=True, zoom_crop_ratio=1.0,
            enable_sharpen=False, enable_contrast=False,
        ))
        result = enhancer.enhance(sample_image)
        np.testing.assert_array_equal(result, sample_image)

    def test_center_content_preserved(self, sample_image):
        enhancer = FrameEnhancer(EnhancementConfig(
            enable_zoom=True, zoom_crop_ratio=0.5,
            enable_sharpen=False, enable_contrast=False,
        ))
        result = enhancer.enhance(sample_image)
        # Center of the white rectangle should still be non-black
        assert result[50, 100].sum() > 0


class TestSharpen:
    def test_preserves_dimensions(self, sharpen_only, sample_image):
        result = sharpen_only.enhance(sample_image)
        assert result.shape == sample_image.shape

    def test_enhances_edges(self, sharpen_only, sample_image):
        result = sharpen_only.enhance(sample_image)
        assert not np.array_equal(result, sample_image)

    def test_uniform_image_unchanged(self, sharpen_only):
        uniform = np.full((100, 200, 3), 128, dtype=np.uint8)
        result = sharpen_only.enhance(uniform)
        np.testing.assert_array_equal(result, uniform)


class TestContrast:
    def test_preserves_dimensions(self, contrast_only, sample_image):
        result = contrast_only.enhance(sample_image)
        assert result.shape == sample_image.shape

    def test_expands_histogram(self, contrast_only):
        low_contrast = np.full((100, 200, 3), 120, dtype=np.uint8)
        low_contrast[::2] = 130
        result = contrast_only.enhance(low_contrast)
        assert result.std() >= low_contrast.std()


class TestDisabled:
    def test_all_disabled_is_identity(self, all_disabled, sample_image):
        result = all_disabled.enhance(sample_image)
        np.testing.assert_array_equal(result, sample_image)

    def test_none_config_uses_defaults(self, sample_image):
        enhancer = FrameEnhancer(None)
        result = enhancer.enhance(sample_image)
        assert result.shape == sample_image.shape
        assert result.dtype == np.uint8


class TestConfig:
    def test_default_values(self):
        config = EnhancementConfig()
        assert config.enable_zoom is True
        assert config.zoom_crop_ratio == 0.6
        assert config.enable_sharpen is True
        assert config.sharpen_strength == 1.5
        assert config.enable_contrast is False

    def test_custom_values(self):
        config = EnhancementConfig(
            enable_zoom=False, zoom_crop_ratio=0.8, sharpen_strength=2.0,
        )
        assert config.enable_zoom is False
        assert config.zoom_crop_ratio == 0.8
        assert config.sharpen_strength == 2.0
