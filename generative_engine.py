import os
from typing import Dict, List

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


# Character limits per platform (hard limits enforced by each network).
# Keys include common aliases so lookups work regardless of how the frontend
# labels the platform (e.g. "Twitter" vs "Twitter/X").
PLATFORM_LIMITS: Dict[str, int] = {
    "Twitter":    280,
    "Twitter/X":  280,
    "Bluesky":    300,
    "Threads":    500,
    "LinkedIn":   3000,
    "Reddit":     40000,
}

SYSTEM_PROMPT = """You are an expert social media content strategist.

You take a base idea that a user wants to post online and turn it into
platform-optimized content tailored to each platform's unique culture,
audience, and hard character limits.

Guidelines per platform:
- Twitter  : Punchy, max 280 chars (HARD LIMIT). No filler, use 1-2 focused hashtags.
- Bluesky  : Conversational, max 300 chars (HARD LIMIT). Dev/tech-friendly tone.
- Threads  : Casual Meta feel, max 500 chars (HARD LIMIT). Relatable, light emojis ok.
- LinkedIn : Professional, 150-1300 chars optimal. Insight-driven, structured paragraphs.
- Reddit   : Community-native tone, no corporate spin. Self-post body; first line = title.
             Keep text genuine and add value to the subreddit.

Rules:
- Strictly respect each platform's character limit — never exceed it.
- Keep factual content faithful to the original idea.
- Avoid hashtag spam; 1-3 focused hashtags max, none for LinkedIn/Reddit.
- Return ONLY a valid JSON object — no markdown fences, no explanation outside JSON.

You will return a JSON object mapping platform names to their post text."""

USER_PROMPT = """Base idea for the post:
\"\"\"{idea}\"\"\"

Platforms requested (JSON keys):
{platforms}

Character limits to STRICTLY respect:
{limits}

Return a single JSON object where:
- Keys are EXACTLY the platform names listed above.
- Values are strings with the final post text for that platform.
- Do NOT include any text outside the JSON object.
"""


def _get_groq_client() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment.")

    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        streaming=False,
        temperature=0.7,
        max_tokens=2048,
    )


def _build_limits_text(platforms: List[str]) -> str:
    lines = []
    for p in platforms:
        limit = PLATFORM_LIMITS.get(p)
        if limit:
            lines.append(f"- {p}: max {limit} characters (HARD LIMIT — never exceed)")
        else:
            lines.append(f"- {p}: no strict limit, but be concise and platform-appropriate")
    return "\n".join(lines)


def generate_platform_posts(idea: str, platforms: List[str]) -> Dict[str, str]:
    """
    Generate platform-optimized post variants as a JSON dict.

    Args:
        idea:      Base idea / content the user wants to share.
        platforms: List of platform labels (e.g. ["Twitter", "LinkedIn"]).

    Returns:
        Dict mapping platform label → generated post text.
    """
    if not idea.strip():
        raise ValueError("Idea text cannot be empty.")
    if not platforms:
        raise ValueError("At least one platform must be specified.")

    llm = _get_groq_client()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT),
        ]
    )
    parser = JsonOutputParser()
    chain = prompt | llm | parser

    result = chain.invoke(
        {
            "idea":      idea,
            "platforms": ", ".join(platforms),
            "limits":    _build_limits_text(platforms),
        }
    )

    # Normalise — always return plain str values.
    # The LLM may return variant key names (e.g. "Twitter" instead of "Twitter/X"),
    # so build a case-insensitive lookup from the raw result.
    _lower_result = {k.lower(): v for k, v in result.items()}
    _ALIASES: Dict[str, List[str]] = {
        "twitter/x": ["twitter/x", "twitter", "x"],
        "bluesky":   ["bluesky"],
        "threads":   ["threads"],
        "linkedin":  ["linkedin"],
        "reddit":    ["reddit"],
    }

    normalized: Dict[str, str] = {}
    for p in platforms:
        value = result.get(p, "")
        if not value:
            for alias in _ALIASES.get(p.lower(), [p.lower()]):
                value = _lower_result.get(alias, "")
                if value:
                    break
        if isinstance(value, dict):
            value = value.get("text", "")
        normalized[p] = str(value).strip()

    # Safety truncation for hard-limit platforms (LLM safety net)
    for p, limit in PLATFORM_LIMITS.items():
        if p in normalized and len(normalized[p]) > limit:
            normalized[p] = normalized[p][: limit - 1] + "…"

    return normalized
