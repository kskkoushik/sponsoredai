"""
Cost Calculator for Sponsored AI
Computes GPT-5.2 API costs and savings from sponsored org mentions.
"""

import re
from ads_data import get_all_ads

# ──────────────────────────────────────────────
# GPT-5.2 estimated pricing (USD per 1M tokens)
# ──────────────────────────────────────────────
GPT52_PRICING = {
    "model": "GPT-5.2",
    "input_per_1m_tokens": 2.50,   # $2.50 per 1M input tokens
    "output_per_1m_tokens": 10.00, # $10.00 per 1M output tokens
}

# Revenue per sponsored organisation shown in the response
REVENUE_PER_ORG_USD = 0.005  # $0.005 = half cent

# Build a set of all known company names (lowercase) for matching
_ALL_COMPANIES: list[str] = [ad["company"] for ad in get_all_ads()]


# ──────────────────────────────────────────────
# Token counting helpers
# ──────────────────────────────────────────────

def count_tokens(text: str) -> int:
    """
    Approximate token count.
    Uses word-count * 1.35 ratio (tiktoken not yet available for GPT-5.2).
    """
    if not text:
        return 0
    words = len(text.split())
    return max(1, round(words * 1.35))


# ──────────────────────────────────────────────
# Org extraction from sponsored blocks
# ──────────────────────────────────────────────

def extract_sponsored_orgs(response_text: str) -> list[str]:
    """
    Extract company/org names that appear inside [SPONSORED]...[/SPONSORED] blocks.

    Returns a deduplicated list of matched company names.
    """
    # Pull out everything inside sponsored tags
    pattern = r'\[SPONSORED\](.*?)\[/SPONSORED\]'
    sponsored_sections = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)

    if not sponsored_sections:
        return []

    combined = " ".join(sponsored_sections).lower()

    found = []
    for company in _ALL_COMPANIES:
        if company.lower() in combined and company not in found:
            found.append(company)

    return found


# ──────────────────────────────────────────────
# Main cost calculation
# ──────────────────────────────────────────────

def calculate_message_cost(
    prompt: str,
    response: str,
    system_prompt_approx: str = "",
    injected_ad_companies: list[str] | None = None,
) -> dict:
    """
    Calculate the full cost breakdown for one query-response pair.

    Args:
        prompt:                 The user's question / input text.
        response:               The full AI response text.
        system_prompt_approx:   Optional system prompt text for more accurate token counts.
        injected_ad_companies:  Companies from ads that were retrieved via RAG and
                                injected into the prompt.  These are the definitive
                                sponsored orgs for this interaction — we use them as
                                the primary source so analytics always reflect which
                                sponsors were actually shown, regardless of how the
                                LLM chose to word the response.

    Returns a dict with keys:
        input_tokens        – estimated tokens sent to the model
        output_tokens       – estimated tokens in the response
        original_cost_usd   – raw API cost at GPT-5.2 prices
        orgs_featured       – deduplicated list of sponsored company names
        revenue_earned_usd  – $0.005 × number of unique orgs featured
        your_cost_usd       – max(0, original_cost - revenue_earned)
        savings_usd         – amount saved / revenue offset
        savings_pct         – percentage saved vs original cost (0–100)
    """
    input_text = system_prompt_approx + " " + prompt
    input_tokens = count_tokens(input_text)
    output_tokens = count_tokens(response)

    # Raw API cost
    input_cost = (input_tokens / 1_000_000) * GPT52_PRICING["input_per_1m_tokens"]
    output_cost = (output_tokens / 1_000_000) * GPT52_PRICING["output_per_1m_tokens"]
    original_cost_usd = input_cost + output_cost

    # ── Sponsored org detection ───────────────────────────────────────────────
    # Primary source: companies whose ads were retrieved by RAG and injected
    # into the system prompt.  These are definitively the sponsors for this
    # response, irrespective of how the LLM phrased the recommendation.
    if injected_ad_companies:
        orgs_featured = list(dict.fromkeys(injected_ad_companies))  # deduplicate, preserve order
    else:
        orgs_featured = []

    # Secondary source: any additional company names found inside the
    # [SPONSORED]…[/SPONSORED] blocks that weren't in the injected list.
    for org in extract_sponsored_orgs(response):
        if org not in orgs_featured:
            orgs_featured.append(org)

    # ── Revenue & net cost ────────────────────────────────────────────────────
    revenue_earned_usd = len(orgs_featured) * REVENUE_PER_ORG_USD

    your_cost_usd = max(0.0, original_cost_usd - revenue_earned_usd)
    savings_usd = min(revenue_earned_usd, original_cost_usd)

    # Savings percentage
    if original_cost_usd > 0:
        savings_pct = round((savings_usd / original_cost_usd) * 100, 1)
    else:
        savings_pct = 0.0

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "original_cost_usd": round(original_cost_usd, 6),
        "orgs_featured": orgs_featured,
        "revenue_earned_usd": round(revenue_earned_usd, 6),
        "your_cost_usd": round(your_cost_usd, 6),
        "savings_usd": round(savings_usd, 6),
        "savings_pct": savings_pct,
    }


def format_usd(amount: float, decimals: int = 4) -> str:
    """Format a USD amount as a readable string."""
    if amount < 0.0001 and amount > 0:
        return f"${amount:.6f}"
    return f"${amount:.{decimals}f}"
