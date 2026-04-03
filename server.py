"""
Sponsored AI — Flask backend.
Replaces Streamlit with a beautiful HTML/JS frontend served from this server.
"""

import json
import os
from datetime import datetime, date

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(32)


# ── Deep-safe JSON helper ──────────────────────────────────────────────────
# Pydantic v2 model_dump() can return AnyUrl / HttpUrl objects that Python's
# json module cannot serialize. Recursively coerce everything to plain
# JSON-compatible primitives BEFORE passing to jsonify().
def _deep_safe(obj):
    if isinstance(obj, dict):
        return {str(k): _deep_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_deep_safe(v) for v in obj]
    if isinstance(obj, bool):        # must be before int check
        return obj
    if isinstance(obj, (int, float)):
        return obj
    if isinstance(obj, str):
        return obj
    if obj is None:
        return None
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    # AnyUrl, HttpUrl, UUID, Decimal, Enum, custom types → stringify
    return str(obj)


def safe_json(data, status=200):
    """jsonify() after deep-converting all values to JSON-safe primitives."""
    return jsonify(_deep_safe(data)), status

# ── In-memory per-session stores ───────────────────────────────────────────
_cost_history: dict[str, list] = {}       # session_id → list[cost_entry]
_session_profiles: dict[str, str] = {}    # session_id → zernio profile_id

# ── Lazy-initialised services ──────────────────────────────────────────────
_llm_service = None
_vector_store_ready = False


def _get_llm_service():
    global _llm_service
    if _llm_service is None:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            from llm_service import create_llm_service
            _llm_service = create_llm_service(api_key)
    return _llm_service


def _ensure_vector_store():
    global _vector_store_ready
    if not _vector_store_ready:
        from vector_store import get_vector_store
        get_vector_store()
        _vector_store_ready = True


# ═══════════════════════════════════════════════════════════════════════════
# STATIC / SPA
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


# ═══════════════════════════════════════════════════════════════════════════
# STATUS
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/api/status")
def api_status():
    return jsonify({
        "groq":   bool(os.getenv("GROQ_API_KEY")),
        "zernio": bool(os.getenv("ZERNIO_API_KEY")),
    })


# ═══════════════════════════════════════════════════════════════════════════
# CHAT  (Server-Sent Events streaming)
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data      = request.get_json(force=True)
    prompt    = (data.get("prompt") or "").strip()
    session_id = data.get("session_id", "default")

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    llm = _get_llm_service()
    if llm is None:
        return jsonify({"error": "LLM service not initialised. Check GROQ_API_KEY."}), 503

    _ensure_vector_store()

    from vector_store import search_ads
    from cost_calculator import calculate_message_cost

    relevant_ads       = search_ads(prompt, n_results=2)
    injected_companies = [ad["company"] for ad in relevant_ads]

    @stream_with_context
    def generate():
        full_response = ""
        try:
            for chunk in llm.generate_stream(prompt, relevant_ads):
                full_response += chunk
                payload = json.dumps({"type": "chunk", "content": chunk})
                yield f"data: {payload}\n\n"

            cost = calculate_message_cost(
                prompt, full_response, injected_ad_companies=injected_companies
            )

            entry = {
                "prompt_snippet": prompt[:80] + ("…" if len(prompt) > 80 else ""),
                "timestamp":      datetime.now().isoformat(timespec="seconds"),
                "cost":           cost,
            }
            _cost_history.setdefault(session_id, []).append(entry)

            done_payload = json.dumps({
                "type": "done",
                "cost": cost,
                "ads":  relevant_ads,
            })
            yield f"data: {done_payload}\n\n"

        except Exception as exc:
            err_payload = json.dumps({"type": "error", "message": str(exc)})
            yield f"data: {err_payload}\n\n"

        # Generator ends here — Flask closes the response, unblocking the client reader.

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ═══════════════════════════════════════════════════════════════════════════
# ADS
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/api/ads")
def api_ads():
    from ads_data import get_all_ads
    return jsonify(get_all_ads())


# ═══════════════════════════════════════════════════════════════════════════
# COST HISTORY
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/api/cost-history")
def api_cost_history():
    session_id = request.args.get("session_id", "default")
    return jsonify(_cost_history.get(session_id, []))


@app.route("/api/clear-history", methods=["POST"])
def api_clear_history():
    session_id = (request.get_json(force=True) or {}).get("session_id", "default")
    _cost_history[session_id] = []
    return jsonify({"success": True})


# ═══════════════════════════════════════════════════════════════════════════
# GEO — Generative Engine Optimisation
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/api/geo/accounts")
def api_geo_accounts():
    session_id = request.args.get("session_id", "default")
    try:
        from geo_service import get_or_create_profile, list_connected_accounts
        cached_profile = _session_profiles.get(session_id)
        profile_id     = get_or_create_profile(cached_profile)
        _session_profiles[session_id] = profile_id
        connected = list_connected_accounts()
        return safe_json({"profile_id": profile_id, "connected": connected})
    except Exception as exc:
        return safe_json({"error": str(exc)}, 500)


@app.route("/api/geo/connect-oauth", methods=["POST"])
def api_geo_connect_oauth():
    data       = request.get_json(force=True)
    platform   = data.get("platform", "")
    profile_id = data.get("profile_id", "")
    try:
        from geo_service import get_oauth_url
        url = get_oauth_url(platform, profile_id)
        return safe_json({"url": str(url)})
    except Exception as exc:
        return safe_json({"error": str(exc)}, 500)


@app.route("/api/geo/connect-bluesky", methods=["POST"])
def api_geo_connect_bluesky():
    data       = request.get_json(force=True)
    profile_id = data.get("profile_id", "")
    identifier = data.get("identifier", "")
    password   = data.get("password", "")
    try:
        from geo_service import connect_bluesky_account
        connect_bluesky_account(profile_id, identifier, password)
        return safe_json({"success": True})
    except Exception as exc:
        return safe_json({"error": str(exc)}, 500)


@app.route("/api/geo/generate", methods=["POST"])
def api_geo_generate():
    data      = request.get_json(force=True)
    idea      = (data.get("idea") or "").strip()
    platforms = data.get("platforms", [])
    if not idea:
        return safe_json({"error": "Idea text cannot be empty."}, 400)
    if not platforms:
        return safe_json({"error": "At least one platform required."}, 400)
    try:
        from generative_engine import generate_platform_posts
        posts = generate_platform_posts(idea, platforms)
        return safe_json(posts)
    except Exception as exc:
        return safe_json({"error": str(exc)}, 500)


@app.route("/api/geo/publish", methods=["POST"])
def api_geo_publish():
    data             = request.get_json(force=True)
    platform_targets = data.get("platform_targets", [])
    if not platform_targets:
        return safe_json({"error": "No platform targets provided."}, 400)
    try:
        from geo_service import publish_post
        result = publish_post(platform_targets)
        return safe_json(result)
    except Exception as exc:
        return safe_json({"error": str(exc)}, 500)


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Starting Sponsored AI Flask server on http://localhost:5000")
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        threaded=True,
        use_reloader=True,
        reloader_type="stat",
    )
