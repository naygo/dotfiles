#!/usr/bin/env python3
"""Icon-click popover for Claude/Codex usage, mirroring HugoJF/cloudex-usage.

Two entry points:
  bar     -> print the (static) icon polybar shows, or nothing if neither
             CLI is running (module then disappears from the bar).
  popup   -> open a GTK popover under the bar with live usage details.

Never starts/authenticates either agent: only reads existing local
credentials, and only when the CLI process is already running.
"""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
import threading

LOCK_PATH = f"/tmp/cloudex_popover_{os.environ.get('USER', 'user')}.pid"


def _acquire_single_instance():
    """Returns True if we should proceed opening a window. If another
    instance is already showing the popover, ask it to close (toggle
    behavior) and return False instead of stacking a second window that
    can never win the input grab.
    """
    if os.path.isfile(LOCK_PATH):
        try:
            with open(LOCK_PATH) as f:
                other_pid = int(f.read().strip())
            os.kill(other_pid, 0)  # raises if not alive
            os.kill(other_pid, signal.SIGUSR1)
            return False
        except (OSError, ValueError):
            pass  # stale lock, fall through and reclaim it
    with open(LOCK_PATH, "w") as f:
        f.write(str(os.getpid()))
    return True


def _release_single_instance():
    try:
        with open(LOCK_PATH) as f:
            if int(f.read().strip()) == os.getpid():
                os.remove(LOCK_PATH)
    except (OSError, ValueError):
        pass

HOME = os.path.expanduser("~")
CLAUDE_CRED = os.path.join(HOME, ".claude", ".credentials.json")
CODEX_AUTH = os.path.join(HOME, ".codex", "auth.json")
CLAUDE_ENDPOINT = "https://api.anthropic.com/api/oauth/usage"
CODEX_ENDPOINT = "https://chatgpt.com/backend-api/wham/usage"
WEEK_SECONDS = 7 * 24 * 60 * 60
TIMEOUT = 5

COLORS = {
    "bg": "#282828",
    "card": "#3c3836",
    "fg": "#ebdbb2",
    "fg_dim": "#a89984",
    "fg_dark": "#7c6f64",
    "claude": "#fe8019",
    "codex": "#8ec07c",
    "track": "#504945",
}


def _is_running(name):
    try:
        subprocess.run(["pgrep", "-x", "-u", os.environ.get("USER", ""), name],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def _get_json(url, token, extra_headers=None):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    for k, v in (extra_headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _iso_to_epoch_ms(value):
    try:
        # python's fromisoformat needs "+00:00" not "Z"
        v = value.replace("Z", "+00:00")
        import datetime
        return int(datetime.datetime.fromisoformat(v).timestamp() * 1000)
    except Exception:
        return None


def fetch_claude():
    if not _is_running("claude") or not os.path.isfile(CLAUDE_CRED):
        return None
    try:
        with open(CLAUDE_CRED) as f:
            token = json.load(f).get("claudeAiOauth", {}).get("accessToken")
        if not token:
            return None
        data = _get_json(CLAUDE_ENDPOINT, token,
                          {"anthropic-beta": "oauth-2025-04-20"})
        short = data["five_hour"]
        weekly = data["seven_day"]
        return {
            "short_pct": float(short["utilization"]),
            "short_reset_ms": _iso_to_epoch_ms(short["resets_at"]),
            "weekly_pct": float(weekly["utilization"]),
            "weekly_reset_ms": _iso_to_epoch_ms(weekly["resets_at"]),
        }
    except Exception:
        return None


def fetch_codex():
    if not _is_running("codex") or not os.path.isfile(CODEX_AUTH):
        return None
    try:
        with open(CODEX_AUTH) as f:
            token = json.load(f).get("tokens", {}).get("access_token")
        if not token:
            return None
        data = _get_json(CODEX_ENDPOINT, token)
        rl = data.get("rate_limit", {})
        for key in ("primary_window", "secondary_window"):
            window = rl.get(key)
            if window and window.get("limit_window_seconds") == WEEK_SECONDS:
                return {
                    "weekly_pct": float(window["used_percent"]),
                    "weekly_reset_ms": int(window["reset_at"]) * 1000,
                }
        return None
    except Exception:
        return None


def humanize(reset_ms):
    if reset_ms is None:
        return "unknown"
    diff = (reset_ms / 1000) - time.time()
    if diff <= 0:
        return "resetting soon"
    days = int(diff // 86400)
    hours = int((diff % 86400) // 3600)
    mins = int((diff % 3600) // 60)
    if days >= 1:
        return f"in {days} day{'s' if days != 1 else ''}"
    if hours >= 1:
        return f"in {hours} hr{'s' if hours != 1 else ''}, {mins} min{'s' if mins != 1 else ''}"
    return f"in {mins} min{'s' if mins != 1 else ''}"


def cmd_bar():
    claude = _is_running("claude")
    codex = _is_running("codex")
    if not claude and not codex:
        return
    print("%{T4}󰚩%{T-}")  # Symbols Nerd Font: robot (nf-md-robot)


def cmd_popup():
    if not _acquire_single_instance():
        return

    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk, GLib

    css = Gtk.CssProvider()
    css.load_from_data(f"""
        window {{
            background-color: {COLORS['bg']};
        }}
        .popup-bg {{
            background-color: {COLORS['bg']};
        }}
        .card {{
            background-color: {COLORS['card']};
            padding: 12px;
        }}
        .title {{
            color: {COLORS['fg_dark']};
            font-size: 10px;
            letter-spacing: 1px;
        }}
        .heading {{
            color: {COLORS['fg']};
            font-size: 18px;
            font-weight: bold;
        }}
        .section-label {{
            color: {COLORS['fg']};
            font-weight: bold;
        }}
        .pct-label {{
            color: {COLORS['fg']};
            font-weight: bold;
        }}
        .reset-label {{
            color: {COLORS['fg_dim']};
            font-size: 11px;
        }}
        .empty-label {{
            color: {COLORS['fg_dim']};
        }}
        progressbar.claude trough progress {{
            background-color: {COLORS['claude']};
        }}
        progressbar.codex trough progress {{
            background-color: {COLORS['codex']};
        }}
        progressbar trough {{
            background-color: {COLORS['track']};
            min-height: 6px;
        }}
        progressbar progress {{
            min-height: 6px;
        }}
    """.encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), css,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    win = Gtk.Window(type=Gtk.WindowType.POPUP)
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)
    win.set_skip_pager_hint(True)
    win.set_keep_above(True)
    win.set_resizable(False)
    win.set_default_size(320, -1)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    outer.get_style_context().add_class("popup-bg")
    outer.set_margin_top(14)
    outer.set_margin_bottom(14)
    outer.set_margin_start(14)
    outer.set_margin_end(14)
    win.add(outer)

    title = Gtk.Label(label="USAGE", xalign=0)
    title.get_style_context().add_class("title")
    outer.pack_start(title, False, False, 0)

    heading = Gtk.Label(label="Claude + Codex", xalign=0)
    heading.get_style_context().add_class("heading")
    outer.pack_start(heading, False, False, 0)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    outer.pack_start(content, False, False, 0)

    loading = Gtk.Label(label="Loading...")
    loading.get_style_context().add_class("empty-label")
    content.pack_start(loading, False, False, 4)

    def make_section(name, css_class, pct, reset_text):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("card")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label(label=name, xalign=0)
        label.get_style_context().add_class("section-label")
        row.pack_start(label, True, True, 0)
        pct_label = Gtk.Label(label=f"{round(pct)}%")
        pct_label.get_style_context().add_class("pct-label")
        row.pack_start(pct_label, False, False, 0)
        card.pack_start(row, False, False, 0)

        bar = Gtk.ProgressBar()
        bar.get_style_context().add_class(css_class)
        bar.set_fraction(max(0.0, min(1.0, pct / 100.0)))
        card.pack_start(bar, False, False, 0)

        reset = Gtk.Label(label=f"Resets {reset_text}", xalign=0)
        reset.get_style_context().add_class("reset-label")
        card.pack_start(reset, False, False, 0)

        return card

    def unavailable_card(name):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("card")
        label = Gtk.Label(label=f"{name} - not running or unavailable", xalign=0)
        label.get_style_context().add_class("empty-label")
        card.pack_start(label, False, False, 0)
        return card

    result = {}

    def fetch_worker():
        result["claude"] = fetch_claude()
        result["codex"] = fetch_codex()
        GLib.idle_add(populate)

    def populate():
        content.remove(loading)
        claude = result.get("claude")
        codex = result.get("codex")
        if claude:
            content.pack_start(make_section(
                "Claude - 5-hour window", "claude", claude["short_pct"],
                humanize(claude["short_reset_ms"])), False, False, 0)
            content.pack_start(make_section(
                "Claude - weekly window", "claude", claude["weekly_pct"],
                humanize(claude["weekly_reset_ms"])), False, False, 0)
        else:
            content.pack_start(unavailable_card("Claude"), False, False, 0)
        if codex:
            content.pack_start(make_section(
                "Codex - weekly window", "codex", codex["weekly_pct"],
                humanize(codex["weekly_reset_ms"])), False, False, 0)
        else:
            content.pack_start(unavailable_card("Codex"), False, False, 0)
        content.show_all()
        win.queue_resize()
        return False

    threading.Thread(target=fetch_worker, daemon=True).start()

    seat_holder = {}

    def close(*_a):
        seat = seat_holder.get("seat")
        if seat is not None:
            seat.ungrab()
        _release_single_instance()
        Gtk.main_quit()
        return False

    win.connect("focus-out-event", close)
    win.connect("destroy", close)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, close)

    def on_key(_w, event):
        if event.keyval == Gdk.KEY_Escape:
            close()
    win.connect("key-press-event", on_key)

    def on_button_press(_w, event):
        x, y = win.get_position()
        w, h = win.get_size()
        outside = not (x <= event.x_root <= x + w and y <= event.y_root <= y + h)
        if outside:
            close()
            return True
        return False
    win.connect("button-press-event", on_button_press)

    win.show_all()

    def position(*_a):
        screen = Gdk.Screen.get_default()
        # Pick the top-left-most monitor (where the polybar bar lives),
        # rather than trusting Gdk's "primary" flag, which is unreliable
        # with this multi-monitor setup.
        geoms = [screen.get_monitor_geometry(i)
                 for i in range(screen.get_n_monitors())]
        monitor = min(geoms, key=lambda g: (g.x, g.y))
        w, h = win.get_size()
        x = monitor.x + monitor.width - w - 12
        y = monitor.y + 34
        win.move(x, y)
    win.connect("size-allocate", position)
    position()

    win.grab_add()
    win.present()
    win.grab_focus()
    try:
        seat = win.get_display().get_default_seat()
        gdkwin = win.get_window()
        status = seat.grab(gdkwin, Gdk.SeatCapabilities.ALL, True,
                            None, None, None, None)
        if status == Gdk.GrabStatus.SUCCESS:
            seat_holder["seat"] = seat
    except Exception:
        pass

    Gtk.main()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "bar"
    if mode == "popup":
        cmd_popup()
    else:
        cmd_bar()
