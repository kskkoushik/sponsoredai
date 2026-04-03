"""
Zernio GEO service — all Zernio/publishing logic with no Streamlit dependencies.
Ported from pages/3_🚀_Generative_Engine_Optimization.py for use in Flask server.
"""

import json
import os
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# JSON safety — Pydantic v2 model_dump() can return AnyUrl / other custom types
# that are not JSON-serialisable. Recursively coerce everything to primitives.
# ─────────────────────────────────────────────────────────────────────────────

def _make_json_safe(obj: Any) -> Any:
    """Recursively convert all values to plain JSON-serialisable Python types."""
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_safe(v) for v in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    # AnyUrl, AnyHttpUrl, Pydantic enums, datetimes, etc. → str
    return str(obj)

try:
    from zernio import Zernio as _Zernio
    _ZERNIO_AVAILABLE = True
except ImportError:
    _Zernio = None  # type: ignore[assignment,misc]
    _ZERNIO_AVAILABLE = False

_PROFILE_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".zernio_profile.json")

PLATFORMS: List[Dict[str, Any]] = [
    {"slug": "twitter",  "label": "Twitter/X",  "icon": "🐦", "oauth": True,  "char_limit": 280},
    {"slug": "linkedin", "label": "LinkedIn",    "icon": "💼", "oauth": True,  "char_limit": 3000},
    {"slug": "reddit",   "label": "Reddit",      "icon": "🟠", "oauth": True,  "char_limit": 40000},
    {"slug": "bluesky",  "label": "Bluesky",     "icon": "🦋", "oauth": False, "char_limit": 300},
    {"slug": "threads",  "label": "Threads",     "icon": "🧵", "oauth": True,  "char_limit": 500},
]
SLUG_TO_PLATFORM  = {p["slug"]:  p for p in PLATFORMS}
LABEL_TO_PLATFORM = {p["label"]: p for p in PLATFORMS}

# Simple module-level cache for the Zernio client (no Streamlit cache_resource needed)
_zernio_client: Any = None


def _get_zernio_client() -> Any:
    global _zernio_client
    if _zernio_client is not None:
        return _zernio_client
    if not _ZERNIO_AVAILABLE or _Zernio is None:
        raise RuntimeError("zernio-sdk not installed. Run: pip install zernio-sdk")
    api_key = os.getenv("ZERNIO_API_KEY")
    if not api_key:
        raise RuntimeError("ZERNIO_API_KEY is not set in your .env file.")
    _zernio_client = _Zernio(api_key=api_key)
    return _zernio_client


def zernio_available() -> bool:
    return _ZERNIO_AVAILABLE


# ─────────────────────────────────────────────────────────────────────────────
# SDK object helpers
# ─────────────────────────────────────────────────────────────────────────────

def _obj_to_dict(obj: Any) -> Dict:
    if isinstance(obj, dict):
        return _make_json_safe(obj)
    fn = getattr(obj, "model_dump", None)
    if callable(fn):
        # mode='json' (Pydantic v2) serialises AnyUrl → str, datetime → str, etc.
        for kwargs in [
            {"by_alias": True, "mode": "json"},
            {"by_alias": True},
            {},
        ]:
            try:
                return _make_json_safe(fn(**kwargs))
            except Exception:
                continue
    fn = getattr(obj, "dict", None)
    if callable(fn):
        try:
            return _make_json_safe(fn(by_alias=True))
        except Exception:
            pass
    try:
        return _make_json_safe(dict(vars(obj)))
    except TypeError:
        return {}


def _extract_id(obj: Any) -> str:
    if isinstance(obj, dict):
        return str(obj.get("_id") or obj.get("id") or obj.get("field_id") or "")
    for attr in ("field_id", "_id", "id"):
        val = getattr(obj, attr, None)
        if val:
            return str(val)
    d = _obj_to_dict(obj)
    return str(d.get("_id") or d.get("id") or d.get("field_id") or "")


def _get_attr(obj: Any, *keys: str, default: Any = "") -> Any:
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
    res = client.profiles.list()
    profiles_raw = _get_attr(res, "profiles", default=[])
    if isinstance(profiles_raw, list) and profiles_raw:
        pid = _extract_id(profiles_raw[0])
        if pid:
            return pid
    return None


def get_or_create_profile(session_profile_cache: Optional[str] = None) -> str:
    """
    Return a Zernio profile ID.
    Priority: passed-in session cache → disk cache → list existing → create new.
    """
    if session_profile_cache:
        return session_profile_cache

    cached = _load_profile_cache()
    if cached:
        return cached

    client = _get_zernio_client()

    pid = _pick_profile_from_list(client)
    if pid:
        _save_profile_cache(pid)
        return pid

    try:
        res = client.profiles.create(
            name="Sponsored AI",
            description="Sponsored AI – Generative Engine Optimization",
        )
        profile_obj = _get_attr(res, "profile", default=res)
        pid = _extract_id(profile_obj)
    except Exception as create_err:
        err_str = str(create_err)
        if "403" in err_str or "limit" in err_str.lower() or "plan" in err_str.lower():
            pid = _pick_profile_from_list(client)
            if not pid:
                raise RuntimeError(
                    "Zernio profile limit reached and no existing profile could be found."
                ) from create_err
        else:
            raise

    if not pid:
        raise RuntimeError("Could not extract a profile ID from the Zernio response.")

    _save_profile_cache(pid)
    return pid


# ─────────────────────────────────────────────────────────────────────────────
# Account helpers
# ─────────────────────────────────────────────────────────────────────────────

def list_connected_accounts() -> Dict[str, Dict]:
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
        if "_id" not in acc_dict and "id" in acc_dict:
            acc_dict["_id"] = acc_dict["id"]
        slug = acc_dict.get("platform", "")
        if slug in supported_slugs and slug not in connected:
            connected[slug] = acc_dict

    return connected


def get_oauth_url(platform_slug: str, profile_id: str) -> str:
    client = _get_zernio_client()
    res = client.connect.get_connect_url(
        platform=platform_slug,
        profile_id=profile_id,
    )
    url = _get_attr(res, "auth_url", "authUrl", default="")
    return str(url)


def connect_bluesky_account(profile_id: str, identifier: str, password: str) -> Dict:
    client = _get_zernio_client()
    res = client.connect.connect_bluesky_credentials(
        profile_id=profile_id,
        identifier=identifier.strip(),
        password=password.strip(),
    )
    return _make_json_safe(res if isinstance(res, dict) else _obj_to_dict(res))


# ─────────────────────────────────────────────────────────────────────────────
# Publishing
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_post_dict(res: Any) -> Dict:
    post_obj  = _get_attr(res, "post", default=res)
    post_dict = _obj_to_dict(post_obj)
    if "_id" not in post_dict and "id" in post_dict:
        post_dict["_id"] = post_dict["id"]
    raw_platforms = post_dict.get("platforms", [])
    if raw_platforms and not isinstance(raw_platforms[0], dict):
        post_dict["platforms"] = [_obj_to_dict(p) for p in raw_platforms]
    return post_dict


def publish_post(platform_targets: List[Dict]) -> Dict:
    client = _get_zernio_client()
    per_platform_results: List[Dict] = []

    for target in platform_targets:
        slug    = target.get("platform", "")
        content = target.get("content", "")

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

    statuses      = [r.get("status", "failed") for r in per_platform_results]
    all_published = all(s == "published" for s in statuses)
    any_published = any(s == "published" for s in statuses)
    overall       = "published" if all_published else ("partial" if any_published else "failed")

    return {
        "_id":       "",
        "status":    overall,
        "platforms": per_platform_results,
    }
