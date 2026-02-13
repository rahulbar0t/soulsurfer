import logging

from google import genai
from google.genai import types

from app.core.exceptions import FeedbackGenerationError
from app.models.schemas import AggregatedError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are SoulSurfer's AI surf coach — a friendly, encouraging, and \
knowledgeable guide who helps surfers improve through clear, plain-language \
advice. You are reviewing the results of a video analysis session where \
computer vision tracked the surfer's body positions and flagged areas that \
need attention.

IMPORTANT RULES:

1. KEEP IT SIMPLE: Write the way a great coach talks on the beach — warm, \
direct, easy to understand. Avoid technical jargon, biomechanical terms, or \
scientific language. Say "bend your knees more" not "increase knee flexion."

2. DO NOT REPEAT NUMBERS: The surfer can see all the detailed measurements, \
angles, and percentages in a data section below your feedback. Never cite \
specific degree values, ranges, or statistics. Focus entirely on WHAT to \
feel, WHY it matters for their surfing, and HOW to fix it.

3. USE BODY-FEEL LANGUAGE: Describe corrections in terms of what the surfer \
should feel in their body. "You want to feel your weight low and centered, \
like you're sitting in an invisible chair" is much better than referencing \
knee angles.

4. PRIORITIZE: Address the most important issues first. Something that \
happens frequently and has a big impact matters more than a rare, minor issue.

5. GIVE PRACTICAL DRILLS: For each issue, suggest 1-2 simple exercises the \
surfer can do on the beach, at home, or in the water. Describe them in \
plain terms.

6. BE ENCOURAGING: Always start with what the surfer is doing well. Frame \
improvements as opportunities, not failures. End on a motivating note.

7. ADAPT TO SKILL LEVEL: If skill level is provided, adjust your tone:
   - Beginner: Extra encouraging, focus on safety and having fun, simple tips
   - Intermediate: More specific coaching, focus on building consistency
   - Advanced: Nuanced feedback, focus on fine-tuning and flow

Format your response as:

## Quick Take
[1-2 sentences summarizing the session in an encouraging way]

## Nice Work
[What the surfer is doing well — be specific about which body movements look good]

## Things to Work On

### 1. [Issue name in plain language, e.g. "Getting Lower on Your Board"]
- **What's happening:** [plain description of what their body is doing]
- **Why it matters:** [how it affects their surfing — speed, balance, power, style]
- **Try this:** [simple correction to focus on]
- **Practice drill:** [1-2 easy exercises]

### 2. [Next issue]
...

## Your Next Session
[2-3 simple things to focus on next time they paddle out]
"""

CHAT_SYSTEM_PROMPT = """\
You are SoulSurfer's AI surf coach. You previously analyzed this surfer's \
video session and provided coaching feedback. Now the surfer is asking you \
follow-up questions.

Keep the same warm, encouraging, plain-language coaching style. The surfer \
can see their detailed biomechanical measurements in a separate section, so \
don't cite specific numbers or ranges. Focus on practical advice, body-feel \
cues, and simple drills.

Be conversational — answer their specific question directly, then offer \
a related tip if appropriate. Keep responses focused and not too long.
"""

MAX_FEEDBACK_TOKENS = 8192
MAX_CHAT_TOKENS = 4096
MAX_RETRIES = 2


class FeedbackGenerator:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def _format_errors_for_prompt(
        self,
        errors: list[AggregatedError],
        surfer_name: str | None = None,
        skill_level: str | None = None,
    ) -> str:
        lines: list[str] = []
        if surfer_name:
            lines.append(f"Surfer: {surfer_name}")
        if skill_level:
            lines.append(f"Skill Level: {skill_level}")
        lines.append("")
        lines.append("=== DETECTED FORM ERRORS (ranked by priority) ===")
        lines.append("")

        for i, err in enumerate(errors, 1):
            lines.append(f"Error #{i}: {err.metric}")
            lines.append(f"  Severity: {err.severity.value}")
            lines.append(f"  Average measured value: {err.avg_measured_value}")
            lines.append(f"  Ideal range: {err.ideal_min} - {err.ideal_max}")
            lines.append(f"  Average deviation from range: {err.avg_deviation}")
            lines.append(f"  Max deviation: {err.max_deviation}")
            lines.append(
                f"  Frequency: {err.frequency_pct}% of frames "
                f"({err.frame_count}/{err.total_frames_analyzed})"
            )
            lines.append(
                f"  Time span: {err.first_timestamp_sec}s - "
                f"{err.last_timestamp_sec}s "
                f"(duration: {err.duration_sec}s)"
            )
            lines.append("")

        if not errors:
            lines.append(
                "No significant form errors detected! "
                "All metrics within ideal ranges."
            )

        return "\n".join(lines)

    def _format_errors_summary(self, errors: list[AggregatedError]) -> str:
        """Create a brief error summary for chat context (no raw numbers)."""
        if not errors:
            return "No significant form errors were detected in the session."
        summaries = []
        for err in errors:
            metric_name = err.metric.replace("_", " ").title()
            summaries.append(f"- {metric_name} ({err.severity.value} severity)")
        return "Issues found:\n" + "\n".join(summaries)

    def _call_gemini(
        self,
        contents,
        system_instruction: str,
        max_tokens: int,
    ) -> str:
        """Call Gemini API with retry logic and truncation detection."""
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        max_output_tokens=max_tokens,
                    ),
                )

                # Check for empty response
                text = response.text
                if not text or not text.strip():
                    logger.warning(
                        "Gemini returned empty response (attempt %d/%d)",
                        attempt + 1,
                        MAX_RETRIES,
                    )
                    last_error = "empty response"
                    continue

                # Check for truncation
                if (
                    response.candidates
                    and response.candidates[0].finish_reason == "MAX_TOKENS"
                ):
                    logger.warning("Gemini response was truncated (MAX_TOKENS)")
                    text += (
                        "\n\n---\n*Your coach had more to say! "
                        "Ask a follow-up question below to continue the conversation.*"
                    )

                return text

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        "Gemini API error (attempt %d/%d): %s",
                        attempt + 1,
                        MAX_RETRIES,
                        e,
                    )
                    last_error = str(e)
                    continue
                raise FeedbackGenerationError(f"Gemini API error: {e}") from e

        raise FeedbackGenerationError(
            f"Gemini returned {last_error} after {MAX_RETRIES} attempts"
        )

    def generate_feedback(
        self,
        errors: list[AggregatedError],
        surfer_name: str | None = None,
        skill_level: str | None = None,
    ) -> str:
        """Generate initial coaching feedback from error analysis."""
        user_message = self._format_errors_for_prompt(errors, surfer_name, skill_level)

        return self._call_gemini(
            contents=user_message,
            system_instruction=SYSTEM_PROMPT,
            max_tokens=MAX_FEEDBACK_TOKENS,
        )

    def chat(
        self,
        errors: list[AggregatedError],
        coaching_feedback: str,
        chat_history: list[dict],
        new_message: str,
        surfer_name: str | None = None,
        skill_level: str | None = None,
    ) -> str:
        """Handle a follow-up chat message with session context."""
        # Build context-aware system instruction
        error_summary = self._format_errors_summary(errors)
        context_parts = [CHAT_SYSTEM_PROMPT, ""]
        if surfer_name:
            context_parts.append(f"Surfer: {surfer_name}")
        if skill_level:
            context_parts.append(f"Skill Level: {skill_level}")
        context_parts.append("")
        context_parts.append(f"Session analysis summary:\n{error_summary}")
        system_instruction = "\n".join(context_parts)

        # Build multi-turn conversation
        contents = []

        # First turn: the original coaching feedback as assistant context
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text="Please analyze my surf session.")],
            )
        )
        contents.append(
            types.Content(
                role="model",
                parts=[types.Part(text=coaching_feedback)],
            )
        )

        # Previous chat history
        for msg in chat_history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])],
                )
            )

        # New user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=new_message)],
            )
        )

        return self._call_gemini(
            contents=contents,
            system_instruction=system_instruction,
            max_tokens=MAX_CHAT_TOKENS,
        )
