"""
Portfolio Dashboard — desktop window for dashboard.html.

* Borderless window, no browser UI.
* Drag it (by the symbol title, top-left) onto any monitor and let go: it snaps to fill
  that monitor's work area (Full / Top ½ / Bottom ½ — pick in the header).
* Remembers which monitor and mode you used last.

Run from source:   pip install -r requirements.txt   then   pythonw dashboard.py
Build an .exe:     build.bat   ->   dist\\PortfolioDashboard.exe
"""
import json
import os
import sys
import threading
import time
from pathlib import Path

IS_WIN = os.name == "nt"

if IS_WIN:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    # Per-monitor DPI awareness, so window coordinates are real pixels on every screen.
    # Must happen before any window is created.
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

import webview  # noqa: E402  (after DPI setup on purpose)

APP = "Portfolio Dashboard"
MODES = ("full", "top", "bottom")


# ---------------------------------------------------------------- paths
def app_dir() -> Path:
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent


def resource(name: str) -> Path:
    """Prefer a copy next to the exe/script (so you can edit the watchlist), else the bundled one."""
    local = app_dir() / name
    if local.exists():
        return local
    return Path(getattr(sys, "_MEIPASS", app_dir())) / name


DATA = Path(os.environ.get("APPDATA", Path.home())) / "PortfolioDashboard"
CONFIG = DATA / "window.json"


def load_config() -> dict:
    try:
        return json.loads(CONFIG.read_text())
    except Exception:
        return {}


def save_config(cfg: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg))


# ---------------------------------------------------------------- Win32 helpers
if IS_WIN:
    class MONITORINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

    MONITOR_DEFAULTTONEAREST = 2
    SWP_NOZORDER, SWP_NOACTIVATE = 0x0004, 0x0010
    VK_LBUTTON = 0x01
    MonitorEnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
                                         ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
    user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
    user32.MonitorFromPoint.restype = wintypes.HMONITOR
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.MonitorFromWindow.restype = wintypes.HMONITOR
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
    user32.FindWindowW.restype = wintypes.HWND
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, ctypes.c_uint]

    def work_area(hmon):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
        r = mi.rcWork
        return r.left, r.top, r.right, r.bottom

    def monitors():
        out = []

        def cb(hmon, _hdc, _rect, _lp):
            out.append(work_area(hmon))
            return True

        user32.EnumDisplayMonitors(None, None, MonitorEnumProc(cb), 0)
        return out

    def monitor_at(x, y):
        return user32.MonitorFromPoint(wintypes.POINT(int(x), int(y)), MONITOR_DEFAULTTONEAREST)

    def mouse_down():
        return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)


def mode_rect(area, mode):
    l, t, r, b = area
    w, h = r - l, b - t
    if mode == "top":
        return l, t, w, h // 2
    if mode == "bottom":
        return l, t + h // 2, w, h - h // 2
    return l, t, w, h


# ---------------------------------------------------------------- app
class Dashboard:
    def __init__(self):
        self.cfg = load_config()
        self.mode = self.cfg.get("mode", "full") if self.cfg.get("mode") in MODES else "full"
        self.window = None
        self.hwnd = None
        self._last_move = 0.0
        self._ignore_until = 0.0

    # -- monitor choice
    def start_point(self):
        """Centre of the monitor used last time; first run: the first portrait (vertical) monitor."""
        if "monitor" in self.cfg:
            return self.cfg["monitor"]
        if IS_WIN:
            mons = monitors()
            pick = next((m for m in mons if (m[3] - m[1]) > (m[2] - m[0])), mons[0] if mons else None)
            if pick:
                return [(pick[0] + pick[2]) // 2, (pick[1] + pick[3]) // 2]
        return None

    # -- snapping
    def find_hwnd(self):
        if not self.hwnd and IS_WIN:
            self.hwnd = user32.FindWindowW(None, APP) or None
        return self.hwnd

    def snap(self, point=None):
        if not IS_WIN or not self.find_hwnd():
            return
        hmon = monitor_at(*point) if point else user32.MonitorFromWindow(self.hwnd, MONITOR_DEFAULTTONEAREST)
        area = work_area(hmon)
        x, y, w, h = mode_rect(area, self.mode)
        self._ignore_until = time.time() + 0.6
        user32.SetWindowPos(self.hwnd, None, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE)
        self.cfg.update(mode=self.mode, monitor=[(area[0] + area[2]) // 2, (area[1] + area[3]) // 2])
        save_config(self.cfg)

    def on_shown(self):
        for _ in range(20):           # window handle may take a moment to appear
            if self.find_hwnd():
                break
            time.sleep(0.1)
        self.snap(self.start_point())
        threading.Thread(target=self._watch_drag, daemon=True).start()

    def on_moved(self, *_):
        if time.time() > self._ignore_until:
            self._last_move = time.time()

    def _watch_drag(self):
        # After you drag the window and release the mouse, fill whatever monitor it landed on.
        while True:
            time.sleep(0.15)
            if self._last_move and time.time() - self._last_move > 0.3 and not mouse_down():
                self._last_move = 0.0
                self.snap()

    # -- methods callable from the page (window.pywebview.api.*)
    def get_mode(self):
        return self.mode

    def set_mode(self, mode):
        if mode in MODES:
            self.mode = mode
            self.snap()

    def minimize(self):
        self.window.minimize()

    def close(self):
        self.window.destroy()


def main():
    html = resource("dashboard.html")
    if not html.exists():
        sys.exit("dashboard.html not found next to the app.")

    app = Dashboard()

    class Api:  # the only methods the page can call
        def get_mode(self): return app.get_mode()
        def set_mode(self, mode): return app.set_mode(mode)
        def minimize(self): return app.minimize()
        def close(self): return app.close()

    app.window = webview.create_window(
        APP, html.resolve().as_uri(),
        width=1000, height=900,
        frameless=IS_WIN, easy_drag=False,
        background_color="#0b0b0d",
        js_api=Api(),
    )
    if IS_WIN:
        app.window.events.shown += app.on_shown
        app.window.events.moved += app.on_moved

    DATA.mkdir(parents=True, exist_ok=True)
    # private_mode=False keeps your averages / API key / settings between launches
    webview.start(private_mode=False, storage_path=str(DATA / "webview"))


if __name__ == "__main__":
    main()
