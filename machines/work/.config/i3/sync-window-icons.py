#!/usr/bin/python3
"""Shrink client icons inside transparent canvases; preserve i3 title geometry."""
import ctypes as C
import ctypes.util
import fcntl
import os
from pathlib import Path
import time

import gi
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, GLib


def padded_icons(values):
    """Keep every advertised resolution, with 70% artwork centered in each."""
    result = []
    offset = 0
    while offset + 2 <= len(values):
        width, height = values[offset:offset + 2]
        count = width * height
        if not width or not height or width > 2048 or height > 2048:
            return None
        if offset + 2 + count > len(values):
            return None
        pixels = values[offset + 2:offset + 2 + count]
        rgba = bytes(channel for p in pixels for channel in
                     ((p >> 16) & 255, (p >> 8) & 255, p & 255, (p >> 24) & 255))
        image = GdkPixbuf.Pixbuf.new_from_bytes(
            GLib.Bytes.new(rgba), GdkPixbuf.Colorspace.RGB, True, 8,
            width, height, width * 4)
        small_width, small_height = max(1, round(width * .7)), max(1, round(height * .7))
        scaled = image.scale_simple(small_width, small_height, GdkPixbuf.InterpType.BILINEAR)
        data, stride = scaled.get_pixels(), scaled.get_rowstride()
        canvas = [0] * count
        left, top = (width - small_width) // 2, (height - small_height) // 2
        for y in range(small_height):
            for x in range(small_width):
                pos = y * stride + x * 4
                r, g, b, a = data[pos:pos + 4]
                canvas[(top + y) * width + left + x] = (a << 24) | (r << 16) | (g << 8) | b
        result.extend((width, height))
        result.extend(canvas)
        offset += 2 + count
    return result if offset == len(values) else None


class Properties:
    def __init__(self):
        self.x = C.CDLL(ctypes.util.find_library("X11"))
        self.x.XOpenDisplay.argtypes = [C.c_char_p]
        self.x.XOpenDisplay.restype = C.c_void_p
        self.x.XDefaultRootWindow.argtypes = [C.c_void_p]
        self.x.XDefaultRootWindow.restype = C.c_ulong
        self.x.XInternAtom.argtypes = [C.c_void_p, C.c_char_p, C.c_int]
        self.x.XInternAtom.restype = C.c_ulong
        self.x.XGetWindowProperty.argtypes = [
            C.c_void_p, C.c_ulong, C.c_ulong, C.c_long, C.c_long, C.c_int,
            C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_int),
            C.POINTER(C.c_ulong), C.POINTER(C.c_ulong), C.POINTER(C.c_void_p)]
        self.x.XChangeProperty.argtypes = [C.c_void_p, C.c_ulong, C.c_ulong,
                                          C.c_ulong, C.c_int, C.c_int, C.c_void_p, C.c_int]
        self.x.XFree.argtypes = [C.c_void_p]
        self.x.XFlush.argtypes = [C.c_void_p]
        self.x.XCloseDisplay.argtypes = [C.c_void_p]
        self.error_handler = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_void_p)(lambda *_: 0)
        self.x.XSetErrorHandler.argtypes = [type(self.error_handler)]
        self.x.XSetErrorHandler(self.error_handler)
        self.display = self.x.XOpenDisplay(None)
        if not self.display:
            raise SystemExit("Não foi possível acessar a sessão X11 para ajustar os ícones.")
        self.root = self.x.XDefaultRootWindow(self.display)
        self.atoms = {}

    def atom(self, name):
        if name not in self.atoms:
            self.atoms[name] = self.x.XInternAtom(self.display, name.encode(), 0)
        return self.atoms[name]

    def get(self, window, name):
        kind, count, remaining = C.c_ulong(), C.c_ulong(), C.c_ulong()
        fmt, data = C.c_int(), C.c_void_p()
        status = self.x.XGetWindowProperty(
            self.display, window, self.atom(name), 0, 8_000_000, 0, 0,
            C.byref(kind), C.byref(fmt), C.byref(count), C.byref(remaining), C.byref(data))
        try:
            if status or fmt.value != 32 or remaining.value or not data:
                return []
            return list(C.cast(data, C.POINTER(C.c_ulong))[:count.value])
        finally:
            if data:
                self.x.XFree(data)

    def set(self, window, name, values):
        data = (C.c_ulong * len(values))(*values)
        self.x.XChangeProperty(self.display, window, self.atom(name), self.atom("CARDINAL"),
                               32, 0, data, len(values))


def main():
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/i3-bar-{os.getuid()}"))
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (runtime / "i3-window-icons.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        properties = Properties()
        previous = {}
        try:
            while True:
                windows = properties.get(properties.root, "_NET_CLIENT_LIST")
                previous = {w: v for w, v in previous.items() if w in windows}
                for window in windows:
                    current = properties.get(window, "_NET_WM_ICON")
                    if not current or current == previous.get(window):
                        continue
                    original = properties.get(window, "_I3_ORIGINAL_WINDOW_ICON")
                    padded = padded_icons(original) if original else None
                    if padded != current:
                        original = current
                        padded = padded_icons(original)
                    if padded is None:
                        continue
                    properties.set(window, "_I3_ORIGINAL_WINDOW_ICON", original)
                    properties.set(window, "_NET_WM_ICON", padded)
                    previous[window] = padded
                properties.x.XFlush(properties.display)
                time.sleep(1)
        finally:
            properties.x.XCloseDisplay(properties.display)


if __name__ == "__main__":
    main()
