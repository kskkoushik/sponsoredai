"""
Generative Engine Optimization – Sponsored AI
Powered by Zernio (zernio.com) for multi-platform social posting.

Flow:
  1. Set ZERNIO_API_KEY + GROQ_API_KEY in .env
  2. Connect each platform once via OAuth (Bluesky uses app-password credentials)
  3. Write your idea → AI generates platform-optimized drafts
  4. Hit Generate & Auto-Post — Zernio publishes everywhere at once
"""

import json
import os
from typing import Any, Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

from generative_engine import generate_platform_posts

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Zernio SDK import
# ─────────────────────────────────────────────────────────────────────────────
try:
    from zernio import Zernio as _Zernio  # pip install zernio-sdk
    _ZERNIO_AVAILABLE = True
except ImportError:
    _Zernio = None  # type: ignore[assignment,misc]
    _ZERNIO_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# Platform definitions
# ─────────────────────────────────────────────────────────────────────────────
PLATFORMS: List[Dict[str, Any]] = [
    {"slug": "twitter",  "label": "Twitter/X",  "icon": "🐦", "oauth": True,  "char_limit": 280},
    {"slug": "linkedin", "label": "LinkedIn",    "icon": "💼", "oauth": True,  "char_limit": 3000},
    {"slug": "reddit",   "label": "Reddit",      "icon": "🟠", "oauth": True,  "char_limit": 40000},
    {"slug": "bluesky",  "label": "Bluesky",     "icon": "🦋", "oauth": False, "char_limit": 300},
    {"slug": "threads",  "label": "Threads",     "icon": "🧵", "oauth": True,  "char_limit": 500},
]
SLUG_TO_PLATFORM  = {p["slug"]:  p for p in PLATFORMS}
LABEL_TO_PLATFORM = {p["label"]: p for p in PLATFORMS}
PLATFORM_LABELS   = [p["label"] for p in PLATFORMS]

_PROFILE_CACHE_FILE = os.path.join(
    os.path.dirname(__file__), "..", ".zernio_profile.json"
)


# ─────────────────────────────────────────────────────────────────────────────
# Zernio client (cached — it's just configuration, no mutable state)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def _get_zernio_client() -> Any:
    if not _ZERNIO_AVAILABLE or _Zernio is None:
        raise RuntimeError(
            "zernio-sdk not installed. Run: pip install zernio-sdk"
        )
    api_key = os.getenv("ZERNIO_API_KEY")
    if not api_key:
        raise RuntimeError("ZERNIO_API_KEY is not set in your .env file.")
    return _Zernio(api_key=api_key)


# ─────────────────────────────────────────────────────────────────────────────
# SDK object helpers — Zernio SDK returns typed objects, not plain dicts
# ─────────────────────────────────────────────────────────────────────────────

def _obj_to_dict(obj: Any) -> Dict:
    """
    Convert a Zernio SDK Pydantic object to a plain dict with JSON-alias keys.

    The SDK uses Pydantic v2 models where the _id field has Python name
    'field_id' and alias '_id'.  model_dump(by_alias=True) gives us '_id'
    correctly; plain model_dump() gives 'field_id' which we'd miss.
    """
    if isinstance(obj, dict):
        return obj
    # Pydantic v2 — always prefer alias names so _id comes back correctly
    fn = getattr(obj, "model_dump", None)
    if callable(fn):
        try:
            return fn(by_alias=True)
        except Exception:
            try:
                return fn()
            except Exception:
                pass
    # Pydantic v1 fallback
    fn = getattr(obj, "dict", None)
    if callable(fn):
        try:
            return fn(by_alias=True)
        except Exception:
            pass
    # Last resort
    try:
        return dict(vars(obj))
    except TypeError:
        return {}


def _extract_id(obj: Any) -> str:
    """
    Extract the record _id from a Zernio SDK object or dict.

    The Pydantic model stores the ID as field_id (Python attr) with
    alias '_id' (JSON key).  model_dump(by_alias=True) gives '_id'.
    """
    if isinstance(obj, dict):
        return str(obj.get("_id") or obj.get("id") or obj.get("field_id") or "")
    # Direct attribute access — try both the alias and the Python field name
    for attr in ("field_id", "_id", "id"):
        val = getattr(obj, attr, None)
        if val:
            return str(val)
    # Fall back to a serialised dict
    d = _obj_to_dict(obj)
    return str(d.get("_id") or d.get("id") or d.get("field_id") or "")


def _get_attr(obj: Any, *keys: str, default: Any = "") -> Any:
    """Get the first matching key/attribute from a dict or SDK object."""
    if isinstance(obj, dict):
        for k in keys:
            v = obj.get(k)
            if v is not None:
                return v
        return default
    for k in keys:
        v = getattr(obj, k, None)
        if v is not None:
            return v
    return default


# ─────────────────────────────────────────────────────────────────────────────
# Profile helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_profile_cache() -> Optional[str]:
    try:
        with open(_PROFILE_CACHE_FILE) as f:
            return json.load(f).get("profile_id")
    except Exception:
        return None


def _save_profile_cache(profile_id: str) -> None:
    try:
        with open(_PROFILE_CACHE_FILE, "w") as f:
            json.dump({"profile_id": profile_id}, f)
    except Exception:
        pass


def _pick_profile_from_list(client: Any) -> Optional[str]:
    """List existing Zernio profiles and return the first ID found."""
    res = client.profiles.list()
    profiles_raw = _get_attr(res, "profiles", default=[])
    if isinstance(profiles_raw, list) and profiles_raw:
        pid = _extract_id(profiles_raw[0])
        if pid:
            return pid
    return None


def get_or_create_profile() -> str:
    """
    Return a Zernio profile ID, reusing an existing one where possible.
    Priority: session_state → disk cache → list existing → create new.

    Never creates a new profile if the plan limit is already reached —
    falls back to re-listing and using the first existing profile instead.
    """
    if "zernio_profile_id" in st.session_state:
        return st.session_state["zernio_profile_id"]

    cached = _load_profile_cache()
    if cached:
        st.session_state["zernio_profile_id"] = cached
        return cached

    client = _get_zernio_client()

    # Always try listing first — avoids hitting plan limits unnecessarily
    pid = _pick_profile_from_list(client)
    if pid:
        _save_profile_cache(pid)
        st.session_state["zernio_profile_id"] = pid
        return pid

    # No existing profiles — attempt to create one
    try:
        res = client.profiles.create(
            name="Sponsored AI",
            description="Sponsored AI – Generative Engine Optimization",
        )
        profile_obj = _get_attr(res, "profile", default=res)
        pid = _extract_id(profile_obj)
    except Exception as create_err:
        err_str = str(create_err)
        # Plan limit reached (403) — re-list and reuse an existing profile
        if "403" in err_str or "limit" in err_str.lower() or "plan" in err_str.lower():
            pid = _pick_profile_from_list(client)
            if not pid:
                raise RuntimeError(
                    "Zernio profile limit reached and no existing profile could be found. "
                    "Please open your Zernio dashboard, delete an unused profile, or upgrade your plan."
                ) from create_err
        else:
            raise

    if not pid:
        raise RuntimeError(
            f"Could not extract a profile ID from the Zernio response. "
            f"Check your ZERNIO_API_KEY and try again."
        )

    _save_profile_cache(pid)
    st.session_state["zernio_profile_id"] = pid
    return pid


# ─────────────────────────────────────────────────────────────────────────────
# Account helpers
# ─────────────────────────────────────────────────────────────────────────────

def list_connected_accounts() -> Dict[str, Dict]:
    """
    Returns {platform_slug: account_dict} for all connected Zernio accounts.
    Only includes platforms we support.
    """
    client = _get_zernio_client()
    res = client.accounts.list()
    accounts_raw = (
        res.accounts if hasattr(res, "accounts")
        else (res if isinstance(res, list) else res.get("accounts", []))
    )

    connected: Dict[str, Dict] = {}
    supported_slugs = {p["slug"] for p in PLATFORMS}

    for acc in accounts_raw:
        acc_dict = _obj_to_dict(acc)
        # SDK may use 'id' instead of '_id' — normalise to '_id' for consistent access
        if "_id" not in acc_dict and "id" in acc_dict:
            acc_dict["_id"] = acc_dict["id"]
        slug = acc_dict.get("platform", "")
        if slug in supported_slugs and slug not in connected:
            connected[slug] = acc_dict

    return connected


def get_oauth_url(platform_slug: str, profile_id: str) -> str:
    """Start OAuth flow for a platform; return the auth URL."""
    client = _get_zernio_client()
    res = client.connect.get_connect_url(
        platform=platform_slug,
        profile_id=profile_id,
    )
    url = _get_attr(res, "auth_url", "authUrl", default="")
    return str(url)


def connect_bluesky_account(
    profile_id: str, identifier: str, password: str
) -> Dict:
    """Connect a Bluesky account using an app password."""
    client = _get_zernio_client()
    res = client.connect.connect_bluesky_credentials(
        profile_id=profile_id,
        identifier=identifier.strip(),
        password=password.strip(),
    )
    return res if isinstance(res, dict) else vars(res)


# ─────────────────────────────────────────────────────────────────────────────
# Publishing helper
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_post_dict(res: Any) -> Dict:
    """Convert a Zernio post response to a plain dict with normalised keys."""
    post_obj  = _get_attr(res, "post", default=res)
    post_dict = _obj_to_dict(post_obj)
    if "_id" not in post_dict and "id" in post_dict:
        post_dict["_id"] = post_dict["id"]
    # Normalise per-platform result entries
    raw_platforms = post_dict.get("platforms", [])
    if raw_platforms and not isinstance(raw_platforms[0], dict):
        post_dict["platforms"] = [_obj_to_dict(p) for p in raw_platforms]
    return post_dict


def publish_post(platform_targets: List[Dict]) -> Dict:
    """
    Publish immediately — one Zernio API call per platform so each gets
    its own content string.  The aggregate result mirrors the multi-platform
    response shape: { _id, status, platforms: [...] }.

    Each entry in platform_targets must have:
      - platform             : slug string
      - accountId            : Zernio account _id
      - content              : platform-specific post text (generated by Groq)
      - platformSpecificData : optional dict (e.g. Reddit subreddit/title)
    """
    client = _get_zernio_client()

    per_platform_results: List[Dict] = []

    for target in platform_targets:
        slug    = target.get("platform", "")
        content = target.get("content", "")

        # Build the minimal platform entry for this single call
        platform_entry: Dict[str, Any] = {
            "platform":  slug,
            "accountId": target["accountId"],
        }
        if "platformSpecificData" in target:
            platform_entry["platformSpecificData"] = target["platformSpecificData"]

        try:
            res = client.posts.create(
                content=content,
                publish_now=True,
                platforms=[platform_entry],
            )
            post_dict = _normalise_post_dict(res)

            # Extract per-platform result from the response
            p_results = post_dict.get("platforms", [])
            if p_results:
                p_entry = p_results[0] if isinstance(p_results[0], dict) else _obj_to_dict(p_results[0])
            else:
                p_entry = {"platform": slug, "status": post_dict.get("status", "published")}

            p_entry.setdefault("platform", slug)
            per_platform_results.append(p_entry)

        except Exception as exc:
            per_platform_results.append({
                "platform": slug,
                "status":   "failed",
                "error":    str(exc),
            })

    # Aggregate overall status
    statuses      = [r.get("status", "failed") for r in per_platform_results]
    all_published = all(s == "published" for s in statuses)
    any_published = any(s == "published" for s in statuses)
    overall       = "published" if all_published else ("partial" if any_published else "failed")

    return {
        "_id":       "",   # individual posts have separate IDs
        "status":    overall,
        "platforms": per_platform_results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Page configuration & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Generative Engine Optimization – Sponsored AI",
    page_icon="🚀",
    layout="wide",
)

st.markdown("""
<style>
    .platform-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.6rem;
        border: 1px solid #2a2a4a;
        min-height: 110px;
    }
    .platform-card.connected    { border-left: 4px solid #2ECC71; }
    .platform-card.disconnected { border-left: 4px solid #E67E22; }
    .badge-connected {
        display: inline-block;
        background: rgba(46,204,113,0.15);
        color: #2ECC71;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-disconnected {
        display: inline-block;
        background: rgba(230,126,34,0.15);
        color: #E67E22;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .connect-link-box {
        background: #0e1117;
        border: 1px solid #1E90FF;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin-top: 0.5rem;
        word-break: break-all;
        font-size: 0.8rem;
    }
    .section-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #ccc;
        border-left: 3px solid #1E90FF;
        padding-left: 0.75rem;
        margin: 1.2rem 0 0.8rem;
    }
    .result-card {
        background: #0e1117;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.4rem;
        border: 1px solid #2a2a4a;
    }
    .result-card.success { border-left: 4px solid #2ECC71; }
    .result-card.failed  { border-left: 4px solid #E74C3C; }
    .char-counter { font-size: 0.72rem; color: #888; text-align: right; }
    .char-counter.over   { color: #E74C3C; font-weight: 600; }
    .char-counter.close  { color: #E67E22; }
    .char-counter.ok     { color: #2ECC71; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Generative Engine Optimization")
st.markdown(
    "*Describe what you want to post once — AI generates platform-tuned content "
    "and Zernio publishes it everywhere you're connected.*"
)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
groq_ok    = bool(os.getenv("GROQ_API_KEY"))
zernio_ok  = bool(os.getenv("ZERNIO_API_KEY"))

with st.sidebar:
    st.markdown("### 🔑 API Keys")
    st.success("✅ GROQ_API_KEY")   if groq_ok   else st.error("❌ GROQ_API_KEY missing")
    st.success("✅ ZERNIO_API_KEY") if zernio_ok  else st.error(
        "❌ ZERNIO_API_KEY missing — get one at [zernio.com](https://zernio.com) "
        "→ Settings → API Keys"
    )
    st.markdown("---")
    st.markdown(
        "**How it works**\n"
        "1. Connect each platform once via OAuth\n"
        "2. Write what you want to post\n"
        "3. Hit **Generate & Auto-Post** — done!\n\n"
        "**Powered by**\n"
        "- [Zernio](https://zernio.com) — multi-platform posting API\n"
        "- Groq — fast AI content generation"
    )
    st.markdown("---")
    st.markdown(
        "**Platform limits**\n"
        "- Twitter/X: 280 chars\n"
        "- Bluesky: 300 chars\n"
        "- Threads: 500 chars\n"
        "- LinkedIn: 3,000 chars\n"
        "- Reddit: 40,000 chars"
    )

# ─────────────────────────────────────────────────────────────────────────────
# Guard: both keys must be present
# ─────────────────────────────────────────────────────────────────────────────
if not zernio_ok:
    st.error(
        "Add **ZERNIO_API_KEY** to your `.env` file and restart the app.  \n"
        "Get your key at [zernio.com → Settings → API Keys](https://zernio.com)."
    )
    st.stop()

if not _ZERNIO_AVAILABLE:
    st.error("Run `pip install zernio-sdk` in your virtual environment, then restart.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 – Connect your accounts
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔗 Step 1 — Connect your accounts</div>', unsafe_allow_html=True)

# Initialise session-state buckets
if "conn_accounts"  not in st.session_state:
    st.session_state.conn_accounts: Dict[str, Dict] = {}
if "oauth_urls"     not in st.session_state:
    st.session_state.oauth_urls: Dict[str, str] = {}
if "profile_id"     not in st.session_state:
    st.session_state.profile_id: str = ""

# ── Refresh button ─────────────────────────────────────────────────────────
col_ref, col_note = st.columns([1, 5])
with col_ref:
    do_refresh = st.button("🔄 Refresh status", key="refresh_btn")
with col_note:
    st.caption(
        "Click **Refresh status** after completing OAuth in your browser "
        "to see updated connection state."
    )

if do_refresh or not st.session_state.conn_accounts:
    with st.spinner("Fetching connected accounts from Zernio…"):
        try:
            st.session_state.conn_accounts = list_connected_accounts()
            st.session_state.oauth_urls    = {}   # clear stale URLs on refresh
        except Exception as exc:
            st.error(f"Could not fetch accounts: {exc}")
            st.stop()

    # Also resolve / create the profile we'll use for connect URLs
    if not st.session_state.profile_id:
        with st.spinner("Resolving Zernio profile…"):
            try:
                st.session_state.profile_id = get_or_create_profile()
            except Exception as exc:
                st.error(f"Could not resolve Zernio profile: {exc}")
                st.stop()

conn_accounts: Dict[str, Dict] = st.session_state.conn_accounts
profile_id:    str              = st.session_state.profile_id

# ── Debug expander ─────────────────────────────────────────────────────────
with st.expander("🔍 Raw connection data (debug)", expanded=False):
    st.json({
        "profile_id":    profile_id,
        "conn_accounts": {
            slug: {"_id": acc.get("_id"), "username": acc.get("username", "n/a")}
            for slug, acc in conn_accounts.items()
        },
    })

# ── Platform cards ─────────────────────────────────────────────────────────
num_cols    = len(PLATFORMS)
card_cols   = st.columns(num_cols)

for idx, platform in enumerate(PLATFORMS):
    slug         = platform["slug"]
    label        = platform["label"]
    icon         = platform["icon"]
    is_oauth     = platform["oauth"]
    is_connected = slug in conn_accounts
    card_cls     = "connected" if is_connected else "disconnected"
    badge        = (
        '<span class="badge-connected">✅ Connected</span>'
        if is_connected
        else '<span class="badge-disconnected">⚠ Not connected</span>'
    )

    with card_cols[idx]:
        st.markdown(
            f'<div class="platform-card {card_cls}">'
            f'<span style="font-size:1.5rem">{icon}</span>'
            f'<br><strong style="font-size:1rem; color:#eee">{label}</strong>'
            f'<br><br>{badge}</div>',
            unsafe_allow_html=True,
        )

        if not is_connected:
            if is_oauth:
                # Standard OAuth connect button
                if st.button(f"Connect {label}", key=f"btn_connect_{slug}", use_container_width=True):
                    if not profile_id:
                        st.error("Profile not ready — click Refresh status first.")
                    else:
                        with st.spinner(f"Generating {label} OAuth link…"):
                            try:
                                url = get_oauth_url(slug, profile_id)
                                st.session_state.oauth_urls[slug] = url
                            except Exception as exc:
                                st.error(f"Could not get {label} link: {exc}")

                # Show saved OAuth URL
                url = st.session_state.oauth_urls.get(slug)
                if url:
                    st.markdown(
                        f'<div class="connect-link-box">'
                        f'<strong style="color:#5aabff">Open this link to connect {label}:</strong>'
                        f'<br><br>'
                        f'<a href="{url}" target="_blank" style="color:#5aabff; font-size:0.75rem">{url}</a>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption("After connecting in your browser → click **🔄 Refresh status**.")

            else:
                # Bluesky — app password credentials
                with st.expander(f"🦋 Connect Bluesky", expanded=False):
                    bsky_handle = st.text_input(
                        "Handle",
                        placeholder="yourname.bsky.social",
                        key="bsky_handle",
                    )
                    bsky_pwd = st.text_input(
                        "App Password",
                        placeholder="xxxx-xxxx-xxxx-xxxx",
                        type="password",
                        key="bsky_pwd",
                        help=(
                            "Create an App Password in Bluesky → Settings → Privacy and Security → "
                            "App Passwords. Do NOT use your main account password."
                        ),
                    )
                    if st.button("Connect Bluesky", key="btn_connect_bluesky", use_container_width=True):
                        if not bsky_handle.strip() or not bsky_pwd.strip():
                            st.error("Enter both your Bluesky handle and app password.")
                        elif not profile_id:
                            st.error("Profile not ready — click Refresh status first.")
                        else:
                            with st.spinner("Connecting Bluesky account…"):
                                try:
                                    connect_bluesky_account(profile_id, bsky_handle, bsky_pwd)
                                    st.success("Bluesky connected! Click **🔄 Refresh status** to confirm.")
                                except Exception as exc:
                                    st.error(f"Bluesky connection failed: {exc}")

# ── Guard: at least one platform connected ────────────────────────────────
connected_slugs  = list(conn_accounts.keys())
connected_labels = [SLUG_TO_PLATFORM[s]["label"] for s in connected_slugs if s in SLUG_TO_PLATFORM]

if not connected_slugs:
    st.info(
        "No platforms connected yet.  "
        "Click **Connect [Platform]** on a card above, open the OAuth link, "
        "complete the flow, then click **🔄 Refresh status**."
    )
    st.stop()

st.success(f"✅ Connected: {', '.join(connected_labels)}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 – Write your idea
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">✍️ Step 2 — Write your idea</div>', unsafe_allow_html=True)

if not groq_ok:
    st.error("**GROQ_API_KEY** is required to generate content.  Add it to `.env` and restart.")
    st.stop()

col_idea, col_settings = st.columns([3, 2])

with col_idea:
    idea = st.text_area(
        "📝 What do you want to post?",
        placeholder=(
            "e.g. We just open-sourced our AI-powered code review tool — "
            "it automatically finds bugs, suggests improvements, and learns from your codebase."
        ),
        height=180,
    )

    selected_labels: List[str] = st.multiselect(
        "🌐 Post to (connected platforms only)",
        options=connected_labels,
        default=connected_labels,
        help="Only platforms where your account is connected via Zernio are shown.",
    )

selected_slugs = [LABEL_TO_PLATFORM[lbl]["slug"] for lbl in selected_labels]

with col_settings:
    st.markdown("#### ⚙️ Per-platform settings")

    reddit_subreddit = ""
    reddit_title     = ""

    if "reddit" in selected_slugs:
        reddit_subreddit = st.text_input(
            "Reddit – subreddit (without r/)",
            placeholder="e.g. SideProject  or  u_YourUsername",
            help=(
                "The target subreddit for your post. "
                "Use your profile subreddit (u_YourUsername) to guarantee permissions. "
                "Community subreddits may restrict bot/API submissions."
            ),
        )
        reddit_title = st.text_input(
            "Reddit – post title (optional)",
            placeholder="Defaults to first line of generated content",
            help="Max 300 characters. Leave blank to auto-generate from the post content.",
        )

    if "twitter" in selected_slugs:
        st.info(
            "🐦 Twitter/X posts are auto-trimmed to 280 chars by the AI.  \n"
            "Duplicate tweets will be rejected by Twitter — vary your content."
        )

    if "bluesky" in selected_slugs:
        st.info(
            "🦋 Bluesky has a **hard 300 char limit**.  \n"
            "The AI will generate a Bluesky-specific short version automatically."
        )

    if "threads" in selected_slugs:
        st.info("🧵 Threads limit is 500 chars — AI generates a concise version.")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 – Generate & Auto-Post
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">🚀 Step 3 — Generate & Auto-Post</div>', unsafe_allow_html=True)

if st.button("✨ Generate & Auto-Post", type="primary", use_container_width=True):

    # ── Validation ────────────────────────────────────────────────────────
    if not idea.strip():
        st.error("Please describe what you want to post.")
        st.stop()
    if not selected_labels:
        st.error("Select at least one connected platform to post to.")
        st.stop()
    if "reddit" in selected_slugs and not reddit_subreddit.strip():
        st.error("Enter a subreddit name for Reddit.")
        st.stop()

    # ── Generate content ──────────────────────────────────────────────────
    st.markdown("#### 📄 Generated drafts")
    with st.spinner("Generating platform-optimised content via Groq…"):
        try:
            generated: Dict[str, str] = generate_platform_posts(idea, selected_labels)
        except Exception as exc:
            st.error(f"Content generation failed: {exc}")
            st.stop()

    # Show generated drafts with character counters
    draft_cols = st.columns(min(len(selected_labels), 3))
    for i, lbl in enumerate(selected_labels):
        text  = generated.get(lbl, "")
        pconf = LABEL_TO_PLATFORM.get(lbl, {})
        limit = pconf.get("char_limit", 0)
        icon  = pconf.get("icon", "📝")
        chars = len(text)

        if limit and chars > limit:
            counter_cls = "over"
            counter_txt = f"{chars}/{limit} ⚠ OVER LIMIT"
        elif limit and chars > limit * 0.9:
            counter_cls = "close"
            counter_txt = f"{chars}/{limit} chars"
        else:
            counter_cls = "ok"
            counter_txt = f"{chars}{f'/{limit}' if limit else ''} chars"

        col = draft_cols[i % 3]
        with col:
            with st.expander(f"{icon} {lbl}", expanded=True):
                st.write(text or "*(no content generated)*")
                st.markdown(
                    f'<div class="char-counter {counter_cls}">{counter_txt}</div>',
                    unsafe_allow_html=True,
                )

    # ── Build platform targets ────────────────────────────────────────────
    platform_targets: List[Dict] = []
    for lbl in selected_labels:
        slug    = LABEL_TO_PLATFORM[lbl]["slug"]
        account = conn_accounts.get(slug)
        if not account:
            st.warning(f"No connected account found for {lbl} — skipping.")
            continue

        target: Dict[str, Any] = {
            "platform":     slug,
            "accountId":    _extract_id(account),
            "content":       generated.get(lbl, ""),
        }

        # Platform-specific data
        if slug == "reddit":
            title = reddit_title.strip() or (generated.get(lbl, "").split("\n", 1)[0] or "Update from Sponsored AI")[:300]
            target["platformSpecificData"] = {
                "subreddit": reddit_subreddit.strip(),
                "title":     title,
                "forceSelf": True,   # ensure text/self post (not link post)
            }

        platform_targets.append(target)

    if not platform_targets:
        st.error("No valid platform targets were built. Check your connections and try again.")
        st.stop()

    # ── Publish via Zernio ────────────────────────────────────────────────
    st.markdown("#### 📤 Publishing results")
    with st.spinner(f"Publishing to {len(platform_targets)} platform(s) via Zernio…"):
        try:
            post_result = publish_post(platform_targets)
        except Exception as exc:
            st.error(f"Publishing failed: {exc}")
            st.stop()

    # ── Show results ──────────────────────────────────────────────────────
    overall_status = post_result.get("status", "unknown")
    post_id        = post_result.get("_id", "")

    if overall_status == "published":
        st.balloons()
        st.success(f"✅ All platforms published successfully! (Post ID: `{post_id}`)")
    elif overall_status == "partial":
        st.warning(f"⚠️ Partial success — some platforms failed. (Post ID: `{post_id}`)")
    else:
        st.error(f"❌ Publishing failed. Status: `{overall_status}` (Post ID: `{post_id}`)")

    # Per-platform breakdown
    platform_results: List[Dict] = post_result.get("platforms", [])
    if platform_results:
        res_cols = st.columns(min(len(platform_results), 3))
        for i, pres in enumerate(platform_results):
            p_slug   = pres.get("platform", "")
            p_status = pres.get("status", "unknown")
            p_url    = pres.get("platformPostUrl", "")
            p_error  = pres.get("error", "")
            pconf    = SLUG_TO_PLATFORM.get(p_slug, {})
            p_icon   = pconf.get("icon", "📢")
            p_label  = pconf.get("label", p_slug.title())

            is_ok    = p_status == "published"
            card_cls = "success" if is_ok else "failed"
            status_emoji = "✅" if is_ok else "❌"

            with res_cols[i % 3]:
                url_html = (
                    f'<br><a href="{p_url}" target="_blank" '
                    f'style="color:#5aabff; font-size:0.8rem;">View post ↗</a>'
                    if p_url else ""
                )
                error_html = (
                    f'<br><span style="color:#E74C3C; font-size:0.78rem;">{p_error[:200]}</span>'
                    if p_error else ""
                )
                st.markdown(
                    f'<div class="result-card {card_cls}">'
                    f'<strong>{p_icon} {p_label}</strong> — {status_emoji} {p_status.title()}'
                    f'{url_html}{error_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        # Fallback if platforms list is empty but we have overall status
        if overall_status == "published":
            st.success("All posts published.")
        else:
            st.json(post_result)

    # ── Retry hint ────────────────────────────────────────────────────────
    if overall_status in ("failed", "partial") and post_id:
        st.info(
            f"You can retry failed platforms via the Zernio dashboard or API:  \n"
            f"`POST https://zernio.com/api/v1/posts/{post_id}/retry`"
        )
