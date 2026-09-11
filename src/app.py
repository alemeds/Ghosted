"""Ghosted - Streamlit entry point.

Find out who doesn't follow you back on Instagram. Inspired by
https://github.com/davidarroyo1234/InstagramUnfollowers (MIT License, David Arroyo).

Credentials and the Instagram session live only in st.session_state for the
duration of the browser tab - nothing is written to disk, env vars, or logs.
"""
import csv
import io
import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import auth, scanner, unfollow, whitelist
from src.i18n import SUPPORTED_LANGUAGES, translator
from src.timings import Timings, default_timings, validate

st.set_page_config(page_title="Ghosted", page_icon="👻", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "es"
if "client" not in st.session_state:
    st.session_state.client = None
if "username" not in st.session_state:
    st.session_state.username = None
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None
if "whitelist" not in st.session_state:
    st.session_state.whitelist = []
if "timings" not in st.session_state:
    st.session_state.timings = default_timings()
if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = set()
if "unfollow_log" not in st.session_state:
    st.session_state.unfollow_log = []
if "theme_override" not in st.session_state:
    st.session_state.theme_override = "auto"

with st.sidebar:
    lang = st.selectbox("🌐", SUPPORTED_LANGUAGES, index=SUPPORTED_LANGUAGES.index(st.session_state.lang), label_visibility="collapsed")
    st.session_state.lang = lang
    theme_options = ["auto", "light", "dark"]
    theme = st.radio(
        "🎨",
        theme_options,
        index=theme_options.index(st.session_state.theme_override),
        format_func=lambda o: {"auto": "🌓", "light": "☀️", "dark": "🌙"}[o],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.theme_override = theme

t = translator(st.session_state.lang)

# Streamlit's runtime theme (st.context.theme) is read-only - there's no
# official API to force a per-viewer theme, so "light"/"dark" here work by
# overriding the CSS custom properties Streamlit's own components already
# read from, rather than fighting each widget individually. "auto" injects
# nothing and defers entirely to the viewer's system/Cloud-level theme.
_THEME_CSS = {
    "light": """
        :root, .stApp { --background-color: #ffffff; --secondary-background-color: #f0f2f6; --text-color: #262730; }
        .stApp { background-color: #ffffff; color: #262730; }
        [data-testid="stSidebar"] { background-color: #f0f2f6; }
    """,
    "dark": """
        :root, .stApp { --background-color: #0e1117; --secondary-background-color: #262730; --text-color: #fafafa; }
        .stApp { background-color: #0e1117; color: #fafafa; }
        [data-testid="stSidebar"] { background-color: #262730; }
    """,
}
if st.session_state.theme_override in _THEME_CSS:
    st.markdown(f"<style>{_THEME_CSS[st.session_state.theme_override]}</style>", unsafe_allow_html=True)

st.title(f"👻 {t('app.title')}")
st.caption(t("app.subtitle"))
st.info(t("app.disclaimer"), icon="⚠️")

with st.expander(t("about.header")):
    st.markdown(t("about.purpose"))
    st.markdown(t("about.what_it_does"))
    st.markdown(t("about.how_to_use"))
    st.warning(t("about.credentials_warning"), icon="🔑")


def _render_login():
    st.subheader(t("login.header"))
    st.caption(t("login.cookie.help"))
    st.warning(t("login.cookie.danger"))
    with st.expander(t("login.cookie.howto_header")):
        st.markdown(t("login.cookie.howto_intro"))
        st.markdown(t("login.cookie.howto_install"))
        st.markdown(t("login.cookie.howto_export"))
        st.markdown(t("login.cookie.howto_paste"))
        st.markdown(t("login.cookie.howto_after"))
        st.divider()
        st.markdown(t("login.cookie.machine_header"))
        st.markdown(t("login.cookie.machine_tips"))
    with st.form("cookie_login_form"):
        pasted = st.text_area(t("login.cookie.label"), height=100)
        submitted = st.form_submit_button(t("login.cookie.submit"))
    if submitted:
        if not pasted.strip():
            return
        result = auth.attempt_login_with_cookie(pasted)
        _handle_login_result(result, result.client.username if result.client else "")


def _handle_login_result(result: auth.LoginResult, username: str):
    if result.status == "success":
        st.session_state.client = result.client
        st.session_state.username = username
        st.rerun()
    elif result.error == "cookie_not_found":
        st.error(t("login.cookie.error.not_found"))
    elif result.error == "cookie_invalid":
        st.error(t("login.cookie.error.invalid"))
    else:
        st.error(t("login.error.generic", error=result.error or result.status))


def _render_timings_settings():
    with st.expander(t("timings.header")):
        current = st.session_state.timings
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{t('scan.header')}**")
            between_scan_pages_ms = st.number_input(t("timings.between_scan_pages"), min_value=300, value=current.between_scan_pages_ms, step=100)
            scan_long_pause_every = st.number_input(t("timings.scan_long_pause_every"), min_value=1, value=current.scan_long_pause_every, step=1)
            scan_long_pause_seconds = st.number_input(t("timings.scan_long_pause_seconds"), min_value=1, value=current.scan_long_pause_seconds, step=1)
        with col2:
            st.markdown(f"**{t('unfollow.header')}**")
            between_unfollows_ms = st.number_input(t("timings.between_unfollows"), min_value=1500, value=current.between_unfollows_ms, step=500)
            unfollow_long_pause_every = st.number_input(t("timings.unfollow_long_pause_every"), min_value=1, value=current.unfollow_long_pause_every, step=1)
            unfollow_long_pause_minutes = st.number_input(t("timings.unfollow_long_pause_minutes"), min_value=0.5, value=current.unfollow_long_pause_minutes, step=0.5)

        st.session_state.timings = validate(Timings(
            between_scan_pages_ms=int(between_scan_pages_ms),
            scan_long_pause_every=int(scan_long_pause_every),
            scan_long_pause_seconds=int(scan_long_pause_seconds),
            between_unfollows_ms=int(between_unfollows_ms),
            unfollow_long_pause_every=int(unfollow_long_pause_every),
            unfollow_long_pause_minutes=float(unfollow_long_pause_minutes),
        ))

        if st.button(t("timings.reset")):
            st.session_state.timings = default_timings()
            st.rerun()


def _run_scan():
    status = st.empty()
    progress = st.progress(0)
    client = st.session_state.client

    # Best-effort totals so the bar reflects real progress instead of sitting
    # at 0% until the very end - following is weighted as the first half,
    # followers as the second. If this call fails for any reason the scan
    # still runs, just without a moving bar.
    total_following = total_followers = None
    try:
        account = client.user_info(str(client.user_id))
        total_following = account.following_count or None
        total_followers = account.follower_count or None
    except Exception:  # noqa: BLE001 - progress-bar accuracy only, never fatal
        pass

    def on_progress(label: str, count: int):
        if label == "following":
            status.text(t("scan.scanning_following", count=count))
            if total_following:
                progress.progress(min(int(count / total_following * 50), 50))
        elif label == "followers":
            status.text(t("scan.scanning_followers", count=count))
            if total_followers:
                progress.progress(50 + min(int(count / total_followers * 50), 50))
        elif label == "long_pause":
            status.text(t("scan.sleeping", seconds=count))

    result = scanner.scan_non_followers(client, st.session_state.timings, on_progress)
    progress.progress(100)
    st.session_state.scan_result = result
    st.session_state.selected_ids = set()
    if result.get("error"):
        st.warning(t("scan.partial", following=len(result["following"]), error=result["error"]))
    else:
        st.success(t("scan.done", following=len(result["following"]), non_followers=len(result["non_followers"])))


def _export_bytes(users: list[dict], fmt: str) -> bytes:
    if fmt == "json":
        return json.dumps(users, indent=2, ensure_ascii=False).encode("utf-8")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["id", "username", "full_name", "is_private", "is_verified"])
    writer.writeheader()
    for user in users:
        writer.writerow({k: user[k] for k in writer.fieldnames})
    return buffer.getvalue().encode("utf-8")


def _render_results():
    result = st.session_state.scan_result
    non_followers = result["non_followers"]
    whitelisted_ids = {u["id"] for u in whitelist.load(st.session_state)}

    st.subheader(t("results.header"))
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input(t("results.search"), key="search_term")
    with col2:
        show_private = st.checkbox(t("results.filter.private"), value=True)
    with col3:
        show_verified = st.checkbox(t("results.filter.verified"), value=True)

    filtered = [
        u for u in non_followers
        if u["id"] not in whitelisted_ids
        and (show_private or not u["is_private"])
        and (show_verified or not u["is_verified"])
        and (search.lower() in u["username"].lower() or search.lower() in u["full_name"].lower())
    ]

    if not filtered:
        st.write(t("results.empty"))
        return

    select_all = st.checkbox(t("results.select_all"))
    if select_all:
        st.session_state.selected_ids |= {u["id"] for u in filtered}

    cards_per_row = 4
    for row_start in range(0, len(filtered), cards_per_row):
        row_cols = st.columns(cards_per_row)
        for col, user in zip(row_cols, filtered[row_start:row_start + cards_per_row]):
            with col.container(border=True):
                if user["profile_pic_url"]:
                    st.image(user["profile_pic_url"], width=80)
                else:
                    st.markdown("### 👤")
                badge = " 🔒" if user["is_private"] else ""
                badge += " ✔️" if user["is_verified"] else ""
                st.markdown(f"**@{user['username']}**{badge}")
                st.caption(user["full_name"])
                checked = user["id"] in st.session_state.selected_ids
                new_checked = st.checkbox(t("results.select_one"), value=checked, key=f"select_{user['id']}")
                if new_checked:
                    st.session_state.selected_ids.add(user["id"])
                else:
                    st.session_state.selected_ids.discard(user["id"])
                if st.button(t("results.whitelist_add"), key=f"wl_{user['id']}", use_container_width=True):
                    whitelist.add(st.session_state, [user])
                    st.rerun()

    col_csv, col_json = st.columns(2)
    col_csv.download_button(t("results.export_csv"), _export_bytes(filtered, "csv"), file_name="ghosted_non_followers.csv")
    col_json.download_button(t("results.export_json"), _export_bytes(filtered, "json"), file_name="ghosted_non_followers.json")

    st.divider()
    _render_unfollow_section(non_followers)


def _render_unfollow_section(non_followers: list[dict]):
    st.subheader(t("unfollow.header"))
    selected_users = [u for u in non_followers if u["id"] in st.session_state.selected_ids]
    st.write(t("unfollow.selected", count=len(selected_users)))

    if not selected_users:
        return

    if "unfollow_confirm_pending" not in st.session_state:
        st.session_state.unfollow_confirm_pending = False

    if not st.session_state.unfollow_confirm_pending:
        if st.button(t("unfollow.start")):
            st.session_state.unfollow_confirm_pending = True
            st.rerun()
    else:
        st.warning(t("unfollow.confirm", count=len(selected_users)))
        col1, col2 = st.columns(2)
        if col1.button(t("unfollow.start"), key="unfollow_confirm_yes"):
            st.session_state.unfollow_confirm_pending = False
            _run_unfollow(selected_users)
        if col2.button(t("unfollow.cancel"), key="unfollow_confirm_no"):
            st.session_state.unfollow_confirm_pending = False
            st.rerun()

    if st.session_state.unfollow_log:
        st.download_button(
            t("unfollow.log.download"),
            _unfollow_log_txt(st.session_state.unfollow_log),
            file_name="ghosted_unfollow_log.txt",
        )


def _run_unfollow(users: list[dict]):
    status = st.empty()
    progress = st.progress(0)

    def on_progress(user, success, error, index, total):
        progress.progress(int(index / total * 100))
        if success:
            status.text(t("unfollow.progress", username=user["username"], current=index, total=total))
        else:
            st.warning(t("unfollow.failed", username=user["username"], error=error or ""))
        st.session_state.unfollow_log.append({
            "user": user,
            "success": success,
            "error": error,
            "at": datetime.now().isoformat(timespec="seconds"),
        })

    def on_long_pause(minutes):
        status.text(t("unfollow.sleeping", minutes=minutes, batch=st.session_state.timings.unfollow_long_pause_every))

    for _ in unfollow.unfollow_users(st.session_state.client, users, st.session_state.timings, on_progress, on_long_pause):
        pass

    st.session_state.selected_ids -= {u["id"] for u in users}
    successes = sum(1 for e in st.session_state.unfollow_log if e["success"])
    failures = len(st.session_state.unfollow_log) - successes
    st.success(t("unfollow.done", success=successes, failed=failures))


def _unfollow_log_txt(log: list[dict]) -> bytes:
    lines = [t("unfollow.log.header", date=datetime.now().isoformat(timespec="seconds"))]
    for entry in log:
        status = t("unfollow.log.ok") if entry["success"] else t("unfollow.log.failed", error=entry["error"] or "")
        lines.append(f"{entry['at']}  @{entry['user']['username']}  {status}")
    return "\n".join(lines).encode("utf-8")


def _render_whitelist_manager():
    with st.expander(t("whitelist.header")):
        current = whitelist.load(st.session_state)
        st.write(f"{len(current)}")

        uploaded = st.file_uploader(t("whitelist.import"), type="json")
        if uploaded is not None:
            try:
                imported = whitelist.parse_import(json.loads(uploaded.read()))
                merged = whitelist.merge(current, imported)
                whitelist.save(st.session_state, merged)
                st.success(t("whitelist.import.success", count=len(imported)))
            except (json.JSONDecodeError, ValueError) as e:
                st.error(t("whitelist.import.error", error=str(e)))

        if current:
            st.download_button(t("whitelist.export"), _export_bytes(current, "json"), file_name="ghosted_whitelist.json")
            if st.button(t("whitelist.clear")):
                whitelist.clear(st.session_state)
                st.rerun()


if st.session_state.client is None:
    _render_login()
else:
    st.success(t("login.success", username=st.session_state.username))
    if st.button(t("login.logout")):
        st.session_state.client = None
        st.session_state.username = None
        st.session_state.scan_result = None
        st.rerun()

    _render_timings_settings()
    _render_whitelist_manager()

    if st.button(t("scan.start")):
        _run_scan()

    if st.session_state.scan_result is not None:
        _render_results()

st.divider()
st.caption(t("notice.footer"))
