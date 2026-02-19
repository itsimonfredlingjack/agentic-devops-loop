"""System and user prompts for Ollama intent extraction.

The system prompt instructs the LLM to act as a senior business analyst
and extract structured Jira ticket information from voice input.
"""

SYSTEM_PROMPT = """You are a senior Business Analyst. Your task is to extract structured Jira ticket information from a user's voice description.

The user has spoken a feature request, bug report, or task description. Extract the following fields and respond ONLY with valid JSON — no markdown fences, no explanation.

Required JSON fields:
- "summary": Short one-line summary (max 255 chars). In Swedish if the user spoke Swedish.
- "description": Detailed description. Expand the user's intent clearly.
- "acceptance_criteria": Gherkin-style acceptance criteria (Given/When/Then format).
- "issue_type": One of: "Story", "Bug", "Task", "Sub-task"
- "priority": One of: "Highest", "High", "Medium", "Low", "Lowest"
- "ambiguity_score": Float 0.0-1.0 (0.0 = crystal clear, 1.0 = completely unclear)
- "clarification_questions": Array of strings. If ambiguity_score > 0.3, list 1-3 specific questions that would help clarify the request. If clear, use empty array [].
- "labels": Array of relevant label strings

If the request is clear (ambiguity_score <= 0.3), produce a full ticket with empty clarification_questions.
If ambiguous (ambiguity_score > 0.3), set the score accordingly and provide specific clarification_questions to ask the user.

Example (clear request):
{
  "summary": "Bygg login-sida med Google OAuth",
  "description": "Implementera en login-sida som tillåter användare att autentisera sig via Google OAuth 2.0.",
  "acceptance_criteria": "Given en ej autentiserad användare\\nWhen de klickar 'Logga in med Google'\\nThen omdirigeras de till Google OAuth",
  "issue_type": "Story",
  "priority": "High",
  "ambiguity_score": 0.1,
  "clarification_questions": [],
  "labels": ["auth", "frontend", "oauth"]
}

Example (ambiguous request):
{
  "summary": "Fixa grejen",
  "description": "Användaren vill fixa något men det är oklart vad.",
  "acceptance_criteria": "",
  "issue_type": "Task",
  "priority": "Medium",
  "ambiguity_score": 0.8,
  "clarification_questions": ["Vilken del av systemet gäller det?", "Vad är det för problem eller önskat beteende?", "Hur brådskande är det?"],
  "labels": []
}"""


def build_extraction_prompt(voice_text: str) -> str:
    """Build the user message for initial intent extraction.

    The voice_text has already been sanitized and wrapped in protective
    XML tags by the security module before this function is called.

    Args:
        voice_text: Sanitized voice transcription (XML-encoded).

    Returns:
        User message to send to Ollama.
    """
    return f"""Extract Jira ticket information from this voice recording:

{voice_text}

Respond with JSON only."""


def build_clarification_prompt(
    original_text: str,
    questions: list[str],
    answer_text: str,
) -> str:
    """Build a follow-up prompt incorporating the user's clarification answer.

    Args:
        original_text: The original sanitized voice transcription.
        questions: The clarification questions that were asked.
        answer_text: The user's sanitized answer to those questions.

    Returns:
        User message to send to Ollama for re-extraction.
    """
    questions_formatted = "\n".join(f"- {q}" for q in questions)

    return f"""The user's original voice request was:

{original_text}

You asked these clarification questions:
{questions_formatted}

The user responded with:

{answer_text}

Now extract the complete Jira ticket information using both the original request and the clarification. Respond with JSON only."""
