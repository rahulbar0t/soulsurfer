import pytest
from unittest.mock import MagicMock, patch

from app.core.exceptions import FeedbackGenerationError
from app.models.schemas import AggregatedError, Severity
from app.services.feedback_generator import (
    FeedbackGenerator,
    MAX_FEEDBACK_TOKENS,
    MAX_CHAT_TOKENS,
    SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT,
)


def _make_agg_error(**kwargs) -> AggregatedError:
    defaults = {
        "metric": "left_knee_angle",
        "severity": Severity.HIGH,
        "avg_measured_value": 95.0,
        "ideal_min": 110,
        "ideal_max": 170,
        "avg_deviation": 15.0,
        "max_deviation": 25.0,
        "frame_count": 80,
        "total_frames_analyzed": 100,
        "frequency_pct": 80.0,
        "first_timestamp_sec": 0.0,
        "last_timestamp_sec": 16.0,
        "duration_sec": 16.0,
        # Worst frame data for clip extraction
        "worst_frame_number": 50,
        "worst_timestamp_sec": 8.0,
        "worst_measured_value": 90.0,
    }
    defaults.update(kwargs)
    return AggregatedError(**defaults)


class TestFormatErrors:
    def test_format_with_errors(self):
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        errors = [_make_agg_error()]
        text = gen._format_errors_for_prompt(
            errors, surfer_name="John", skill_level="intermediate"
        )
        assert "Surfer: John" in text
        assert "Skill Level: intermediate" in text
        assert "left_knee_angle" in text
        assert "95.0" in text
        assert "110" in text
        assert "80.0%" in text

    def test_format_empty_errors(self):
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        text = gen._format_errors_for_prompt([])
        assert "No significant form errors detected" in text

    def test_format_no_metadata(self):
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        errors = [_make_agg_error()]
        text = gen._format_errors_for_prompt(errors)
        assert "Surfer:" not in text
        assert "Skill Level:" not in text
        assert "left_knee_angle" in text

    def test_format_multiple_errors(self):
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        errors = [
            _make_agg_error(metric="left_knee_angle"),
            _make_agg_error(metric="spinal_angle", avg_measured_value=45.0),
        ]
        text = gen._format_errors_for_prompt(errors)
        assert "Error #1: left_knee_angle" in text
        assert "Error #2: spinal_angle" in text


class TestSystemPrompt:
    def test_prompt_is_non_technical(self):
        """The prompt should instruct the model to keep language simple."""
        assert "KEEP IT SIMPLE" in SYSTEM_PROMPT
        assert "DO NOT REPEAT NUMBERS" in SYSTEM_PROMPT
        assert "BODY-FEEL LANGUAGE" in SYSTEM_PROMPT

    def test_prompt_has_soulsurfer_branding(self):
        assert "SoulSurfer" in SYSTEM_PROMPT

    def test_prompt_uses_simplified_sections(self):
        assert "## Quick Take" in SYSTEM_PROMPT
        assert "## Nice Work" in SYSTEM_PROMPT
        assert "## Things to Work On" in SYSTEM_PROMPT
        assert "## Your Next Session" in SYSTEM_PROMPT

    def test_chat_prompt_exists(self):
        assert "SoulSurfer" in CHAT_SYSTEM_PROMPT
        assert "follow-up" in CHAT_SYSTEM_PROMPT


class TestTokenLimits:
    def test_feedback_token_limit(self):
        assert MAX_FEEDBACK_TOKENS == 8192

    def test_chat_token_limit(self):
        assert MAX_CHAT_TOKENS == 4096


class TestErrorsSummary:
    def test_format_errors_summary_with_errors(self):
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        errors = [
            _make_agg_error(metric="left_knee_angle", severity=Severity.HIGH),
            _make_agg_error(metric="spinal_angle", severity=Severity.MEDIUM),
        ]
        summary = gen._format_errors_summary(errors)
        assert "Left Knee Angle" in summary
        assert "high" in summary
        assert "Spinal Angle" in summary
        assert "medium" in summary

    def test_format_errors_summary_empty(self):
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        summary = gen._format_errors_summary([])
        assert "No significant form errors" in summary


class TestCallGemini:
    def _make_gen(self):
        """Create a FeedbackGenerator with a mocked client."""
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        gen.client = MagicMock()
        gen.model = "gemini-2.5-flash"
        return gen

    def _mock_response(self, text="Great feedback!", finish_reason="STOP"):
        """Create a mock Gemini response."""
        response = MagicMock()
        response.text = text
        candidate = MagicMock()
        candidate.finish_reason = finish_reason
        response.candidates = [candidate]
        return response

    def test_successful_response(self):
        gen = self._make_gen()
        gen.client.models.generate_content.return_value = self._mock_response(
            "Great coaching feedback!"
        )
        result = gen._call_gemini("test prompt", "system", 8192)
        assert result == "Great coaching feedback!"

    def test_truncation_detection(self):
        gen = self._make_gen()
        gen.client.models.generate_content.return_value = self._mock_response(
            "Partial feedback...", finish_reason="MAX_TOKENS"
        )
        result = gen._call_gemini("test prompt", "system", 8192)
        assert "Partial feedback..." in result
        assert "follow-up question" in result

    def test_empty_response_retries(self):
        gen = self._make_gen()
        # First call returns empty, second returns valid
        gen.client.models.generate_content.side_effect = [
            self._mock_response(""),
            self._mock_response("Valid feedback after retry"),
        ]
        result = gen._call_gemini("test prompt", "system", 8192)
        assert result == "Valid feedback after retry"
        assert gen.client.models.generate_content.call_count == 2

    def test_none_response_retries(self):
        gen = self._make_gen()
        gen.client.models.generate_content.side_effect = [
            self._mock_response(None),
            self._mock_response("Valid feedback after retry"),
        ]
        result = gen._call_gemini("test prompt", "system", 8192)
        assert result == "Valid feedback after retry"

    def test_persistent_empty_raises(self):
        gen = self._make_gen()
        gen.client.models.generate_content.return_value = self._mock_response("")
        with pytest.raises(FeedbackGenerationError, match="empty response"):
            gen._call_gemini("test prompt", "system", 8192)

    def test_api_error_retries_then_raises(self):
        gen = self._make_gen()
        gen.client.models.generate_content.side_effect = Exception("API down")
        with pytest.raises(FeedbackGenerationError, match="Gemini API error"):
            gen._call_gemini("test prompt", "system", 8192)


class TestGenerateFeedback:
    def test_generate_feedback_calls_gemini(self):
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        gen.client = MagicMock()
        gen.model = "gemini-2.5-flash"

        response = MagicMock()
        response.text = "Your session looked great!"
        candidate = MagicMock()
        candidate.finish_reason = "STOP"
        response.candidates = [candidate]
        gen.client.models.generate_content.return_value = response

        result = gen.generate_feedback([_make_agg_error()], "Alice", "beginner")
        assert result == "Your session looked great!"
        gen.client.models.generate_content.assert_called_once()

        # Verify max_output_tokens is 8192
        call_kwargs = gen.client.models.generate_content.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        assert config.max_output_tokens == 8192


class TestChat:
    def test_chat_builds_conversation(self):
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        gen.client = MagicMock()
        gen.model = "gemini-2.5-flash"

        response = MagicMock()
        response.text = "Sure, try bending your knees more!"
        candidate = MagicMock()
        candidate.finish_reason = "STOP"
        response.candidates = [candidate]
        gen.client.models.generate_content.return_value = response

        errors = [_make_agg_error()]
        result = gen.chat(
            errors=errors,
            coaching_feedback="Original feedback here.",
            chat_history=[
                {"role": "user", "content": "What about my arms?"},
                {"role": "assistant", "content": "Your arms look good!"},
            ],
            new_message="How do I improve my pop-up?",
            surfer_name="Bob",
            skill_level="intermediate",
        )

        assert result == "Sure, try bending your knees more!"
        gen.client.models.generate_content.assert_called_once()

        # Verify conversation structure
        call_args = gen.client.models.generate_content.call_args
        contents = call_args.kwargs.get("contents") or call_args[1].get("contents")
        # Should have: initial user + model + 2 history + new user = 5 turns
        assert len(contents) == 5
        assert contents[0].role == "user"
        assert contents[1].role == "model"
        assert contents[-1].role == "user"
        assert "pop-up" in contents[-1].parts[0].text

    def test_chat_with_empty_history(self):
        gen = FeedbackGenerator.__new__(FeedbackGenerator)
        gen.client = MagicMock()
        gen.model = "gemini-2.5-flash"

        response = MagicMock()
        response.text = "Good question!"
        candidate = MagicMock()
        candidate.finish_reason = "STOP"
        response.candidates = [candidate]
        gen.client.models.generate_content.return_value = response

        result = gen.chat(
            errors=[],
            coaching_feedback="No issues found.",
            chat_history=[],
            new_message="Any tips for beginners?",
        )

        assert result == "Good question!"
        call_args = gen.client.models.generate_content.call_args
        contents = call_args.kwargs.get("contents") or call_args[1].get("contents")
        # Should have: initial user + model + new user = 3 turns
        assert len(contents) == 3
