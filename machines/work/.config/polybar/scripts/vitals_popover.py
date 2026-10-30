#!/usr/bin/env python3
"""Vitals-style system popover for polybar (GNOME Vitals equivalent).

Bar keeps showing the fixed CPU/RAM/Temp/Disk values it already has
(polybar's own internal modules); this script only adds a click-to-open
popover with more detail (per-sensor temps, GPU, network throughput,
disk per-mount, peripheral battery), same square/no-border style as the
cloudex-usage popover.
"""
import glob
import fcntl
import json
import os
import signal
import subprocess
import sys
import threading
import time

COLORS = {
    "bg": "#282828",
    "card": "#3c3836",
    "fg": "#ebdbb2",
    "fg_dim": "#a89984",
    "fg_dark": "#7c6f64",
    "accent": "#fe8019",
    "good": "#b8bb26",
    "warn": "#fabd2f",
    "bad": "#fb4934",
    "track": "#504945",
}



_INSTANCE_LOCK = None


def _acquire_single_instance():
    """A repeated launch asks the currently open popup to close."""
    global _INSTANCE_LOCK
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    path = os.path.join(runtime_dir, f"vitals-popover-{os.getuid()}.lock")
    lock = open(path, "a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.seek(0)
        pid = lock.read().strip()
        try:
            if pid:
                os.kill(int(pid), signal.SIGUSR1)
        except (ValueError, ProcessLookupError):
            pass
        finally:
            lock.close()
        return False
    lock.seek(0)
    lock.truncate()
    lock.write(str(os.getpid()))
    lock.flush()
    _INSTANCE_LOCK = lock
    return True


def _release_single_instance():
    global _INSTANCE_LOCK
    if _INSTANCE_LOCK is not None:
        _INSTANCE_LOCK.close()
        _INSTANCE_LOCK = None


def _run(cmd, timeout=3):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout).stdout
    except Exception:
        return ""


def cpu_usage():
    def snapshot():
        with open("/proc/stat") as f:
            parts = f.readline().split()[1:8]
        vals = [int(v) for v in parts]
        idle = vals[3] + vals[4]
        total = sum(vals)
        return idle, total

    idle1, total1 = snapshot()
    time.sleep(0.15)
    idle2, total2 = snapshot()
    dt = total2 - total1
    di = idle2 - idle1
    pct = 0.0 if dt <= 0 else (1 - di / dt) * 100
    load1, load5, load15 = os.getloadavg()
    return {"pct": pct, "load": (load1, load5, load15)}


def memory_usage():
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, _, rest = line.partition(":")
            info[key] = int(rest.strip().split()[0])  # kB
    total = info.get("MemTotal", 0)
    avail = info.get("MemAvailable", 0)
    used = total - avail
    swap_total = info.get("SwapTotal", 0)
    swap_free = info.get("SwapFree", 0)
    swap_used = swap_total - swap_free
    return {
        "used_gb": used / 1048576, "total_gb": total / 1048576,
        "pct": 0 if total == 0 else used / total * 100,
        "swap_used_gb": swap_used / 1048576,
        "swap_total_gb": swap_total / 1048576,
    }


CHIP_NAMES = {
    "k10temp": "CPU", "coretemp": "CPU",
    "gigabyte_wmi": "Placa-mãe", "acpitz": "ACPI",
    "nvme": "NVMe",
}


def _chip_label(chip_key, seen_nvme=[0]):
    base = chip_key.split("-")[0]
    name = CHIP_NAMES.get(base, base)
    if base == "nvme":
        seen_nvme[0] += 1
        return f"{name} {seen_nvme[0]}"
    return name


def temperatures():
    out = _run(["sensors", "-j"])
    if not out:
        return []
    try:
        data = json.loads(out)
    except Exception:
        return []
    seen_nvme = [0]
    readings = []
    for chip_key, chip_val in data.items():
        if not isinstance(chip_val, dict):
            continue
        label = _chip_label(chip_key, seen_nvme)
        for sensor_key, sensor_val in chip_val.items():
            if sensor_key == "Adapter" or not isinstance(sensor_val, dict):
                continue
            input_key = next((k for k in sensor_val if k.endswith("_input")),
                              None)
            if input_key is None:
                continue
            value = sensor_val[input_key]
            readings.append((label, sensor_key, value))
    return readings


def gpu_info():
    out = _run(["nvidia-smi",
                "--query-gpu=name,temperature.gpu,utilization.gpu,"
                "memory.used,memory.total,power.draw",
                "--format=csv,noheader,nounits"])
    line = out.strip().splitlines()[0] if out.strip() else ""
    if not line:
        return None
    try:
        name, temp, util, mem_used, mem_total, power = \
            [p.strip() for p in line.split(",")]
        return {
            "name": name, "temp": float(temp), "util": float(util),
            "mem_used": float(mem_used), "mem_total": float(mem_total),
            "power": float(power),
        }
    except Exception:
        return None


def disk_usage():
    out = _run(["df", "-B1", "--output=target,pcent,avail,size"])
    entries = []
    skip_prefixes = ("/sys", "/proc", "/dev", "/run", "/snap", "/var/lib/docker")
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) != 4:
            continue
        target, pcent, avail, size = parts
        if target.startswith(skip_prefixes) or "efivars" in target:
            continue
        try:
            pct = int(pcent.rstrip("%"))
            avail_gb = int(avail) / 1_000_000_000
            size_gb = int(size) / 1_000_000_000
        except ValueError:
            continue
        if size_gb < 1:
            continue
        entries.append({"target": target, "pct": pct, "avail_gb": avail_gb,
                         "size_gb": size_gb})
    return entries[:5]


def network_speed(iface_hint="enp5s0", sample_s=0.4):
    path = f"/sys/class/net/{iface_hint}/statistics"
    if not os.path.isdir(path):
        candidates = [d for d in os.listdir("/sys/class/net")
                      if d not in ("lo",) and not d.startswith(
                          ("docker", "br-", "veth", "virbr"))]
        if not candidates:
            return None
        iface_hint = candidates[0]
        path = f"/sys/class/net/{iface_hint}/statistics"

    def read():
        with open(f"{path}/rx_bytes") as f:
            rx = int(f.read())
        with open(f"{path}/tx_bytes") as f:
            tx = int(f.read())
        return rx, tx

    try:
        rx1, tx1 = read()
        time.sleep(sample_s)
        rx2, tx2 = read()
    except Exception:
        return None
    return {
        "iface": iface_hint,
        "rx_kbps": (rx2 - rx1) / sample_s / 1024,
        "tx_kbps": (tx2 - tx1) / sample_s / 1024,
    }


def peripheral_batteries():
    devices = _run(["upower", "-e"]).splitlines()
    results = []
    for dev in devices:
        dev = dev.strip()
        if "battery" not in dev.lower() or not dev:
            continue
        info = _run(["upower", "-i", dev])
        model = None
        pct = None
        for line in info.splitlines():
            line = line.strip()
            if line.startswith("model:"):
                model = line.split(":", 1)[1].strip()
            elif line.startswith("percentage:"):
                try:
                    pct = float(line.split(":", 1)[1].strip().rstrip("%"))
                except ValueError:
                    pass
        if pct is not None:
            results.append({"model": model or dev, "pct": pct})
    return results


def fetch_all():
    return {
        "cpu": cpu_usage(),
        "mem": memory_usage(),
        "temps": temperatures(),
        "gpu": gpu_info(),
        "disk": disk_usage(),
        "net": network_speed(),
        "peripherals": peripheral_batteries(),
    }


def cmd_popup():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk, GLib

    if not _acquire_single_instance():
        return

    css = Gtk.CssProvider()
    css.load_from_data(f"""
        window {{ background-color: {COLORS['bg']}; }}
        .popup-bg {{ background-color: {COLORS['bg']}; }}
        .card {{ background-color: {COLORS['card']}; padding: 10px; }}
        .title {{ color: {COLORS['fg_dark']}; font-size: 10px;
                  letter-spacing: 1px; }}
        .heading {{ color: {COLORS['fg']}; font-size: 18px;
                    font-weight: bold; }}
        .section-title {{ color: {COLORS['fg']}; font-weight: bold;
                           font-size: 12px; }}
        .row-label {{ color: {COLORS['fg_dim']}; }}
        .row-value {{ color: {COLORS['fg']}; font-weight: bold; }}
        .empty-label {{ color: {COLORS['fg_dim']}; }}
        progressbar trough {{
            background-color: {COLORS['track']};
            min-height: 6px;
        }}
        progressbar progress {{ min-height: 6px; }}
    """.encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), css,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    win = Gtk.Window(type=Gtk.WindowType.POPUP)
    win.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                   Gdk.EventMask.BUTTON_RELEASE_MASK |
                   Gdk.EventMask.KEY_PRESS_MASK)
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)
    win.set_skip_pager_hint(True)
    win.set_keep_above(True)
    win.set_resizable(False)
    win.set_default_size(360, -1)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    outer.get_style_context().add_class("popup-bg")
    outer.set_margin_top(14)
    outer.set_margin_bottom(14)
    outer.set_margin_start(14)
    outer.set_margin_end(14)
    win.add(outer)

    title = Gtk.Label(label="VITALS", xalign=0)
    title.get_style_context().add_class("title")
    outer.pack_start(title, False, False, 0)

    heading = Gtk.Label(label="Sistema", xalign=0)
    heading.get_style_context().add_class("heading")
    outer.pack_start(heading, False, False, 0)

    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroller.set_max_content_height(560)
    scroller.set_propagate_natural_height(True)
    outer.pack_start(scroller, False, False, 0)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    scroller.add(content)

    loading = Gtk.Label(label="Carregando...")
    loading.get_style_context().add_class("empty-label")
    content.pack_start(loading, False, False, 4)

    def section(title_text):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("card")
        label = Gtk.Label(label=title_text, xalign=0)
        label.get_style_context().add_class("section-title")
        card.pack_start(label, False, False, 0)
        return card

    def row(parent, label_text, value_text, pct=None):
        r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbl = Gtk.Label(label=label_text, xalign=0)
        lbl.get_style_context().add_class("row-label")
        r.pack_start(lbl, True, True, 0)
        val = Gtk.Label(label=value_text)
        val.get_style_context().add_class("row-value")
        r.pack_start(val, False, False, 0)
        parent.pack_start(r, False, False, 0)

    def bar(parent, pct):
        b = Gtk.ProgressBar()
        b.set_fraction(max(0.0, min(1.0, pct / 100.0)))
        parent.pack_start(b, False, False, 0)

    result = {}

    def fetch_worker():
        result["data"] = fetch_all()
        GLib.idle_add(populate)

    def populate():
        content.remove(loading)
        data = result["data"]

        cpu = data["cpu"]
        c = section("CPU")
        row(c, "Uso", f"{cpu['pct']:.0f}%", cpu["pct"])
        bar(c, cpu["pct"])
        l1, l5, l15 = cpu["load"]
        row(c, "Load average", f"{l1:.2f} / {l5:.2f} / {l15:.2f}")
        content.pack_start(c, False, False, 0)

        mem = data["mem"]
        m = section("Memória")
        row(m, "RAM", f"{mem['used_gb']:.1f} / {mem['total_gb']:.1f} GB",
            mem["pct"])
        bar(m, mem["pct"])
        if mem["swap_total_gb"] > 0:
            row(m, "Swap", f"{mem['swap_used_gb']:.1f} / "
                            f"{mem['swap_total_gb']:.1f} GB")
        content.pack_start(m, False, False, 0)

        gpu = data["gpu"]
        if gpu:
            g = section(f"GPU — {gpu['name']}")
            row(g, "Temp", f"{gpu['temp']:.0f}°C", gpu["temp"])
            row(g, "Uso", f"{gpu['util']:.0f}%", gpu["util"])
            row(g, "VRAM", f"{gpu['mem_used']:.0f} / "
                            f"{gpu['mem_total']:.0f} MB",
                gpu["mem_used"] / gpu["mem_total"] * 100)
            row(g, "Consumo", f"{gpu['power']:.0f} W")
            content.pack_start(g, False, False, 0)

        temps = data["temps"]
        if temps:
            t = section("Temperatura")
            for label, sensor, value in temps:
                t_pct = value if value <= 100 else None
                row(t, f"{label} · {sensor}", f"{value:.0f}°C", t_pct)
            content.pack_start(t, False, False, 0)

        disks = data["disk"]
        if disks:
            d = section("Disco")
            for entry in disks:
                row(d, entry["target"],
                    f"{entry['avail_gb']:.0f} GB livre "
                    f"({entry['pct']}% usado)", entry["pct"])
            content.pack_start(d, False, False, 0)

        net = data["net"]
        if net:
            n = section(f"Rede — {net['iface']}")
            row(n, "Download", f"{net['rx_kbps']:.0f} KB/s")
            row(n, "Upload", f"{net['tx_kbps']:.0f} KB/s")
            content.pack_start(n, False, False, 0)

        peripherals = data["peripherals"]
        if peripherals:
            p = section("Periféricos")
            for dev in peripherals:
                row(p, dev["model"], f"{dev['pct']:.0f}%", dev["pct"])
            content.pack_start(p, False, False, 0)

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
    win.connect("grab-broken-event", close)
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
        geoms = [screen.get_monitor_geometry(i)
                 for i in range(screen.get_n_monitors())]
        monitor = min(geoms, key=lambda g: (g.x, g.y))
        w, h = win.get_size()
        x = monitor.x + monitor.width - w - 12
        y = monitor.y + 46
        win.move(x, y)
    win.connect("size-allocate", position)
    position()

    win.grab_add()
    win.present()
    win.grab_focus()
    grab_attempts = 0

    def grab_inputs():
        nonlocal grab_attempts
        grab_attempts += 1
        seat = win.get_display().get_default_seat()
        status = seat.grab(win.get_window(), Gdk.SeatCapabilities.ALL, True,
                           None, None, None, None)
        if status == Gdk.GrabStatus.SUCCESS:
            seat_holder["seat"] = seat
            return False
        if grab_attempts < 10:
            return True
        print("Vitals: não foi possível capturar os cliques; fechando o painel.",
              file=sys.stderr)
        close()
        return False

    # Wait for the launch click to release its implicit pointer grab.
    GLib.timeout_add(50, grab_inputs)
    try:
        Gtk.main()
    finally:
        _release_single_instance()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "popup"
    cmd_popup()
