#!/usr/bin/env python3
"""
Integrated Sensor Dashboard – Raspberry Pi
Sensors: BME680 (env), PM2.5 (dust), SCD4x (CO2), MLX90393 (magnetometer), CapeSym MCA (radiation)
Display: fullscreen pygame window
"""

import sys
import threading
import time
import math
import random
import collections
import urllib.request
import io
import csv as _csv

import pygame

# ── Optional sensor imports ────────────────────────────────────────────────
# Each block is guarded so the dashboard still runs if a library is absent.

try:
    import board
    import adafruit_bme680
    _BME680 = True
except ImportError:
    _BME680 = False

try:
    import serial
    from adafruit_pm25.uart import PM25_UART
    _PM25 = True
except ImportError:
    _PM25 = False

try:
    import adafruit_scd30
    _SCD30 = True
except ImportError:
    _SCD30 = False

try:
    import adafruit_mlx90393
    _MLX = True
except ImportError:
    _MLX = False

try:
    from capemca import CapeMCA, find_all_mcas, SPECTRUM_CHANNELS
    _MCA = True
except ImportError:
    _MCA = False

# ── Configuration ──────────────────────────────────────────────────────────

SCREEN_W   = 0   # set at runtime from actual display
SCREEN_H   = 0
FPS        = 10
HISTORY    = 120        # data points kept per channel (≈ 120 s at 1 Hz)
PM_PORT    = "/dev/ttyS0"
SEA_LEVEL  = 1013.25    # hPa, for BME680 altitude

# ── Colours  (amber CRT / 70s terminal) ───────────────────────────────────

BG        = (  6,   3,   0)
PANEL     = ( 16,   8,   0)
BORDER    = (110,  55,   0)
AMBER     = (255, 165,   0)
AMBER_HI  = (255, 220,  80)
AMBER_DIM = ( 45,  22,   0)
OLIVE     = (155, 195,   0)   # good reading
GOLD      = (255, 185,   0)   # warn
RED_HOT   = (195,  35,   0)   # critical

# ── Shared state (all sensor threads write here) ───────────────────────────

_lock = threading.Lock()

_data = {
    "bme": dict(temperature=None, humidity=None, pressure=None,
                gas=None, altitude=None, ok=False, err=""),
    "pm":  dict(pm1=None, pm25=None, pm10=None, ok=False, err=""),
    "co2": dict(co2=None, temperature=None, humidity=None, ok=False, err=""),
    "mag": dict(x=None, y=None, z=None, magnitude=None, ok=False, err=""),
    "mca": dict(cps=None, temperature=None, total=None, usv_hr=None, ok=False, err=""),
}

_hist = {
    "co2_temp":  collections.deque(maxlen=HISTORY),
    "co2_humid": collections.deque(maxlen=HISTORY),
    "co2":       collections.deque(maxlen=HISTORY),
    "pm25":      collections.deque(maxlen=HISTORY),
    "mag":       collections.deque(maxlen=HISTORY),
    "mca_cps":   collections.deque(maxlen=HISTORY),
}

# ── Sensor threads ─────────────────────────────────────────────────────────

def _thread_bme680():
    if not _BME680:
        with _lock:
            _data["bme"]["err"] = "adafruit_bme680 not installed"
        return
    try:
        i2c  = board.I2C()
        bme  = adafruit_bme680.Adafruit_BME680_I2C(i2c)
        bme.sea_level_pressure = SEA_LEVEL
        while True:
            try:
                t = round(bme.temperature, 1)
                h = round(bme.relative_humidity, 1)
                p = round(bme.pressure, 1)
                g = bme.gas
                a = round(bme.altitude, 1)
                with _lock:
                    _data["bme"].update(temperature=t, humidity=h, pressure=p,
                                        gas=g, altitude=a, ok=True, err="")
            except Exception as e:
                with _lock:
                    _data["bme"].update(ok=False, err=str(e)[:40])
            time.sleep(2)
    except Exception as e:
        with _lock:
            _data["bme"].update(ok=False, err=f"init: {e}"[:40])


def _thread_pm25():
    if not _PM25:
        with _lock:
            _data["pm"]["err"] = "adafruit_pm25 not installed"
        return
    try:
        uart = serial.Serial(PM_PORT, baudrate=9600, timeout=0.25)
        pm   = PM25_UART(uart, reset_pin=None)
        while True:
            try:
                r = pm.read()
                p1  = r["pm10 standard"]
                p25 = r["pm25 standard"]
                p10 = r["pm100 standard"]
                with _lock:
                    _data["pm"].update(pm1=p1, pm25=p25, pm10=p10,
                                       ok=True, err="")
                    _hist["pm25"].append(p25)
            except Exception as e:
                with _lock:
                    _data["pm"].update(ok=False, err=str(e)[:40])
            time.sleep(1)
    except Exception as e:
        with _lock:
            _data["pm"].update(ok=False, err=f"init: {e}"[:40])


def _thread_scd4x():
    if not _SCD30:
        with _lock:
            _data["co2"]["err"] = "adafruit_scd30 not installed"
        return
    try:
        i2c = board.I2C()
        scd = adafruit_scd30.SCD30(i2c)
        while True:
            try:
                if scd.data_available:
                    co2 = scd.CO2
                    t   = round(scd.temperature, 1)
                    h   = round(scd.relative_humidity, 1)
                    with _lock:
                        _data["co2"].update(co2=int(co2), temperature=t,
                                            humidity=h, ok=True, err="")
                        _hist["co2"].append(int(co2))
                        _hist["co2_temp"].append(t)
                        _hist["co2_humid"].append(h)
            except Exception as e:
                with _lock:
                    _data["co2"].update(ok=False, err=str(e)[:40])
            time.sleep(2)
    except Exception as e:
        with _lock:
            _data["co2"].update(ok=False, err=f"init: {e}"[:40])


def _thread_mlx90393():
    if not _MLX:
        with _lock:
            _data["mag"]["err"] = "adafruit_mlx90393 not installed"
        return
    try:
        i2c = board.I2C()
        mlx = adafruit_mlx90393.MLX90393(i2c, gain=adafruit_mlx90393.GAIN_1X)
        while True:
            try:
                mx, my, mz = mlx.magnetic
                mag = math.sqrt(mx * mx + my * my + mz * mz)
                with _lock:
                    _data["mag"].update(x=round(mx, 1), y=round(my, 1),
                                        z=round(mz, 1), magnitude=round(mag, 1),
                                        ok=True, err="")
                    _hist["mag"].append(mag)
            except Exception as e:
                with _lock:
                    _data["mag"].update(ok=False, err=str(e)[:40])
            time.sleep(0.5)
    except Exception as e:
        with _lock:
            _data["mag"].update(ok=False, err=f"init: {e}"[:40])


def _thread_mca():
    if not _MCA:
        with _lock:
            _data["mca"]["err"] = "capemca not found"
        return
    if not find_all_mcas():
        with _lock:
            _data["mca"].update(ok=False, err="no MCA device found")
        return
    while True:
        try:
            with CapeMCA() as mca:
                status = mca.read_status()
                cps   = status.cps
                total = status.total_count
                with _lock:
                    _data["mca"].update(cps=round(cps, 1), total=total,
                                        ok=True, err="")
                    _hist["mca_cps"].append(cps)
        except Exception as e:
            with _lock:
                _data["mca"].update(ok=False, err=str(e)[:40])
        time.sleep(5)

# ── Drawing helpers ────────────────────────────────────────────────────────

def _text(surf, font, text, color, x, y):
    surf.blit(font.render(text, True, color), (x, y))

def _text_c(surf, font, text, color, cx, cy):
    s = font.render(text, True, color)
    surf.blit(s, s.get_rect(center=(cx, cy)))

def _glow(surf, font, text, color, cx, cy):
    dim = tuple(c // 4 for c in color)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        s = font.render(text, True, dim)
        surf.blit(s, s.get_rect(center=(cx + dx, cy + dy)))
    surf.blit(font.render(text, True, color), font.render(text, True, color).get_rect(center=(cx, cy)))

def _tcolor(value, warn, crit):
    if value is None or warn is None:
        return AMBER
    return OLIVE if value < warn else (GOLD if value < crit else RED_HOT)

def _hline(surf, y, x0=0, x1=None, color=None):
    pygame.draw.line(surf, color or BORDER, (x0, y), (x1 or SCREEN_W, y), 1)

def _vline(surf, x, y0, y1, color=None):
    pygame.draw.line(surf, color or BORDER, (x, y0), (x, y1), 1)

def _make_scanlines(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 2):
        pygame.draw.line(s, (0, 0, 0, 45), (0, y), (w, y), 1)
    return s


# ── Gauge (arc meter) ──────────────────────────────────────────────────────

def _draw_gauge(surf, fonts, cx, cy, r, value, lo, hi, label, unit, warn, crit):
    NTICKS = 36
    SPAN   = 270.0
    START  = 225.0
    col    = _tcolor(value, warn, crit)

    # Background tick ring
    for i in range(NTICKS + 1):
        frac   = i / NTICKS
        rad    = math.radians(START - frac * SPAN)
        ca, sa = math.cos(rad), -math.sin(rad)
        major  = (i % 6 == 0)
        inner  = r - (18 if major else 10)
        ox, oy = cx + r * ca, cy + r * sa
        ix, iy = cx + inner * ca, cy + inner * sa
        pygame.draw.line(surf, AMBER_DIM,
                         (int(ix), int(iy)), (int(ox), int(oy)),
                         2 if major else 1)

    # Filled ticks up to value + needle
    if value is not None:
        frac_v = max(0.0, min(1.0, (value - lo) / (hi - lo)))
        n_fill = int(frac_v * NTICKS)
        for i in range(n_fill + 1):
            frac   = min(i / NTICKS, frac_v)
            rad    = math.radians(START - frac * SPAN)
            ca, sa = math.cos(rad), -math.sin(rad)
            major  = (i % 6 == 0)
            inner  = r - (18 if major else 10)
            ox, oy = cx + r * ca, cy + r * sa
            ix, iy = cx + inner * ca, cy + inner * sa
            pygame.draw.line(surf, col,
                             (int(ix), int(iy)), (int(ox), int(oy)),
                             3 if major else 2)
        # Needle
        nrad   = math.radians(START - frac_v * SPAN)
        ca, sa = math.cos(nrad), -math.sin(nrad)
        nx, ny = cx + (r - 22) * ca, cy + (r - 22) * sa
        pygame.draw.line(surf, AMBER_HI, (int(cx), int(cy)), (int(nx), int(ny)), 2)
        pygame.draw.circle(surf, AMBER_HI, (int(cx), int(cy)), 5)

    # Centre value
    if value is not None:
        val_str = f"{value:.1f}" if isinstance(value, float) else str(int(value))
        _glow(surf, fonts["xl"], val_str, col, cx, cy - 10)
        _text_c(surf, fonts["xs"], unit, AMBER_DIM, cx, cy + 22)
    else:
        _text_c(surf, fonts["md"], "---", AMBER_DIM, cx, cy - 5)

    # Label sits in the open gap at the bottom of the arc
    _text_c(surf, fonts["sm"], label, AMBER, cx, cy + r - 20)


# ── Secondary info strip ───────────────────────────────────────────────────

def _draw_info_strip(surf, fonts, fields, rect):
    x, y, w, h = rect
    pygame.draw.rect(surf, PANEL, rect)
    pygame.draw.rect(surf, BORDER, rect, 1)
    col_w = w // len(fields)
    for i, (label, val, color) in enumerate(fields):
        cx = x + i * col_w + col_w // 2
        if i > 0:
            _vline(surf, x + i * col_w, y + 6, y + h - 6)
        _text_c(surf, fonts["xs"], label, AMBER_DIM, cx, y + 16)
        _text_c(surf, fonts["md"], val,   color,     cx, y + 38)


# ── 3-D magnetic field sphere ─────────────────────────────────────────────

def _draw_mag_sphere(surf, fonts, cx, cy, r, mx, my, mz, rect):
    """Draw a 3-D globe with a field-vector arrow and latitude/longitude rings."""
    x, y, w, h = rect
    pygame.draw.rect(surf, PANEL, rect)
    pygame.draw.rect(surf, BORDER, rect, 1)

    _text_c(surf, fonts["xs"], "MAGNETIC FIELD", AMBER_DIM, cx, y + 10)

    # Isometric projection angles
    ISO_X =  0.6   # tilt forward
    ISO_Z = -0.8   # rotate left

    def project(vx, vy, vz):
        """Simple isometric-style 3-D → 2-D."""
        # rotate around Z
        rx = vx * math.cos(ISO_Z) - vy * math.sin(ISO_Z)
        ry = vx * math.sin(ISO_Z) + vy * math.cos(ISO_Z)
        rz = vz
        # tilt around X
        px = rx
        py = ry * math.cos(ISO_X) - rz * math.sin(ISO_X)
        return int(cx + px * r), int(cy + py * r)

    # Latitude rings (horizontal circles)
    for lat in range(-60, 90, 30):
        rad_lat = math.radians(lat)
        ring_r  = math.cos(rad_lat)
        ring_z  = math.sin(rad_lat)
        pts = []
        for deg in range(0, 361, 6):
            a  = math.radians(deg)
            vx = ring_r * math.cos(a)
            vy = ring_r * math.sin(a)
            pts.append(project(vx, vy, ring_z))
        if len(pts) > 1:
            pygame.draw.lines(surf, AMBER_DIM, False, pts, 1)

    # Longitude lines (vertical half-circles)
    for lon in range(0, 180, 30):
        rad_lon = math.radians(lon)
        pts = []
        for deg in range(0, 361, 6):
            a  = math.radians(deg)
            vx = math.cos(a) * math.cos(rad_lon)
            vy = math.cos(a) * math.sin(rad_lon)
            vz = math.sin(a)
            pts.append(project(vx, vy, vz))
        if len(pts) > 1:
            pygame.draw.lines(surf, AMBER_DIM, False, pts, 1)

    # Outer circle (equator silhouette)
    pygame.draw.circle(surf, BORDER, (cx, cy), r, 1)

    # Field vector arrow with proper arrowhead
    if mx is not None:
        mag_ut = math.sqrt(mx*mx + my*my + mz*mz) or 1.0
        nx, ny, nz = mx/mag_ut, my/mag_ut, mz/mag_ut
        tip  = project(nx,       ny,       nz)
        tail = project(-nx*0.5, -ny*0.5, -nz*0.5)
        col  = AMBER_HI

        # Thick shaft
        pygame.draw.line(surf, col, tail, tip, 5)

        # Arrowhead — triangle at tip
        tx, ty = tip
        # perpendicular direction in screen space
        dx, dy = tx - tail[0], ty - tail[1]
        length = math.sqrt(dx*dx + dy*dy) or 1
        pdx, pdy = -dy/length, dx/length   # perpendicular unit vector
        head_size = max(r // 5, 8)
        base_x = tx - dx/length * head_size
        base_y = ty - dy/length * head_size
        p1 = (int(base_x + pdx * head_size * 0.5), int(base_y + pdy * head_size * 0.5))
        p2 = (int(base_x - pdx * head_size * 0.5), int(base_y - pdy * head_size * 0.5))
        pygame.draw.polygon(surf, col, [tip, p1, p2])

        # Tail dot
        pygame.draw.circle(surf, AMBER_DIM, tail, 4)

        # |B| magnitude label
        _text_c(surf, fonts["sm"], f"|B|  {mag_ut:.1f} µT", AMBER, cx, y + h - 14)
    else:
        _text_c(surf, fonts["md"], "---", AMBER_DIM, cx, cy)


# ── Retro chart with grid ──────────────────────────────────────────────────

def _draw_chart(surf, fonts, title, values, unit, rect,
                lo=None, hi=None, warn=None, crit=None):
    x, y, w, h = rect
    pygame.draw.rect(surf, PANEL, rect)
    pygame.draw.rect(surf, BORDER, rect, 1)

    # Dim grid
    for gi in range(1, 4):
        pygame.draw.line(surf, AMBER_DIM, (x+1, y + gi*h//4), (x+w-2, y + gi*h//4), 1)
    for gi in range(1, 5):
        pygame.draw.line(surf, AMBER_DIM, (x + gi*w//5, y+1), (x + gi*w//5, y+h-2), 1)

    _text(surf, fonts["xs"], title, AMBER_DIM, x + 6, y + 4)

    pts = list(values)
    if not pts:
        return

    latest = pts[-1]
    col    = _tcolor(latest, warn, crit)
    s      = fonts["sm"].render(f"{latest:.1f} {unit}", True, col)
    surf.blit(s, (x + w - s.get_width() - 6, y + 2))

    lo_ = lo if lo is not None else min(pts)
    hi_ = hi if hi is not None else max(pts)
    if hi_ <= lo_:
        hi_ = lo_ + 1.0
    span = hi_ - lo_

    coords = [
        (x + 1 + int(i / max(len(pts)-1, 1) * (w-2)),
         y + h - 2 - int((v - lo_) / span * (h - 8)))
        for i, v in enumerate(pts)
    ]
    if len(coords) >= 2:
        fill  = tuple(max(0, c - 160) for c in col)
        pygame.draw.polygon(surf, fill,
                            [(x+1, y+h-2)] + coords + [(coords[-1][0], y+h-2)])
        pygame.draw.lines(surf, col, False, coords, 2)
        pygame.draw.circle(surf, AMBER_HI, coords[-1], 3)


# ── Main render pass ───────────────────────────────────────────────────────

def _render(surf, fonts, d, hist, scanlines):
    surf.fill(BG)

    bme = d["bme"]
    co2 = d["co2"]
    pm  = d["pm"]
    mag = d["mag"]
    mca = d["mca"]

    # SCD30 is the source for temperature and humidity
    env_temp = co2["temperature"]
    env_hum  = co2["humidity"]

    # ── Title bar ──────────────────────────────────────────────────────────
    pygame.draw.rect(surf, PANEL, (0, 0, SCREEN_W, 36))
    _hline(surf, 36)
    _text_c(surf, fonts["lg"],
            "◄   ENVIRONMENTAL  MONITORING  SYSTEM   ►",
            AMBER, SCREEN_W // 2, 18)
    _text(surf, fonts["xs"], time.strftime("%H : %M : %S"),
          AMBER_DIM, SCREEN_W - 90, 12)

    # ── Arc gauges + sphere ────────────────────────────────────────────────
    GR = int(SCREEN_H * 0.147)
    GY = 38 + GR + 12
    QW = SCREEN_W // 4
    for gx in [QW, QW*2, QW*3]:
        _vline(surf, gx, 40, GY + GR + 8)

    # Gauge 1: Temperature
    _draw_gauge(surf, fonts, QW//2,      GY, GR,
                env_temp,   0, 50,   "TEMPERATURE", "°C",  30,   40)
    # Gauge 2: CO2
    _draw_gauge(surf, fonts, QW + QW//2, GY, GR,
                co2["co2"], 350, 2500, "CO2",       "ppm", 1000, 2000)
    # Gauge 3 slot: 3D magnetic sphere
    _draw_mag_sphere(surf, fonts,
                     QW*2 + QW//2, GY, GR,
                     mag["x"], mag["y"], mag["z"],
                     (QW*2, 38, QW, GR*2 + 4))
    # Gauge 4: Radiation
    _draw_gauge(surf, fonts, QW*3 + QW//2, GY, GR,
                mca["cps"], 0, 200, "RADIATION", "cps", 100, 500)

    STRIP_TOP = GY + GR + 14
    _hline(surf, STRIP_TOP)

    # ── Secondary info strip ───────────────────────────────────────────────
    def _v(val, fmt):
        return fmt.format(val) if val is not None else "---"

    strip = [
        ("HUMIDITY",  _v(env_hum,       "{:.1f} %"),  AMBER),
        ("PM 1.0",    _v(pm["pm1"],     "{} µg"),     _tcolor(pm["pm1"],  12,  35)),
        ("PM 2.5",    _v(pm["pm25"],    "{} µg"),     _tcolor(pm["pm25"], 12,  35)),
        ("PM 10",     _v(pm["pm10"],    "{} µg"),     _tcolor(pm["pm10"], 54, 154)),
        ("µSV / HR",  _v(mca["usv_hr"],"{:.4f}"),     _tcolor(mca["usv_hr"], 0.5, 1.0)),
        ("COUNTS",    _v(mca["total"], "{}"),          AMBER_DIM),
    ]

    SH = int(SCREEN_H * 0.105)
    _draw_info_strip(surf, fonts, strip, (0, STRIP_TOP + 1, SCREEN_W, SH))

    CT = STRIP_TOP + SH + 4
    _hline(surf, CT)

    # ── Charts ─────────────────────────────────────────────────────────────
    CT += 2
    CH  = (SCREEN_H - CT - 4) // 2
    CW  = SCREEN_W // 3

    charts = [
        ("TEMPERATURE  (°C)",    hist["co2_temp"],  "°C",   0,    50,   30,   40),
        ("CO2  (ppm)",           hist["co2"],       "ppm",  300, 2500, 1000, 2000),
        ("HUMIDITY  (%)",        hist["co2_humid"], "%",    0,   100,   70,   85),
        ("PM 2.5  (µg/m³)",      hist["pm25"],      "µg",   0,    60,   12,   35),
        ("MAGNETIC FIELD  |B|",  hist["mag"],       "µT",   None, None, None, None),
        ("RADIATION  (cps)",     hist["mca_cps"],   "cps",  0,   200,  100,  500),
    ]

    for idx, (title, vals, unit, lo, hi, warn, crit) in enumerate(charts):
        ci, ri = idx % 3, idx // 3
        _draw_chart(surf, fonts, title, vals, unit,
                    (ci * CW, CT + ri * (CH + 4), CW, CH),
                    lo, hi, warn, crit)

    # ── CRT scanline overlay ───────────────────────────────────────────────
    surf.blit(scanlines, (0, 0))
    pygame.display.flip()


# ── Demo / simulation threads ──────────────────────────────────────────────
# Run with:  python3 dashboard.py --demo
#
# Three sensors (BME680, PM2.5, MCA) replay real data fetched from the GitHub
# repo at startup.  CO2 and magnetometer have no recorded data so they use a
# random walk instead.

_GITHUB_RAW = (
    "https://raw.githubusercontent.com/MattiPatti1/"
    "E11_RohanMatthiasAnushka/main"
)

_demo_data: dict = {}   # populated by _preload_demo_data() before threads start


def _fetch_csv(repo_path: str) -> list[dict]:
    url = f"{_GITHUB_RAW}/{repo_path}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            text = r.read().decode("utf-8")
        rows = list(_csv.DictReader(io.StringIO(text)))
        print(f"[demo] {len(rows)} rows  ←  {repo_path}")
        return rows
    except Exception as e:
        print(f"[demo] could not load {repo_path}: {e}")
        return []


def _preload_demo_data():
    """Download all CSV files needed for demo mode (called once from main)."""
    print("[demo] fetching data from GitHub …")
    _demo_data["week5"]     = _fetch_csv("data/Week5Data_Inside.csv")
    _demo_data["radiation"] = _fetch_csv("2026-04-24_14-54-51/radiation.csv")
    _demo_data["air"]       = _fetch_csv("2026-04-24_14-54-51/air_quality.csv")
    print("[demo] data ready")


# ── random-walk fallback (used when a CSV is missing) ─────────────────────

def _walk(v, center, step, lo, hi):
    v += random.uniform(-step, step) + (center - v) * 0.05
    return max(lo, min(hi, v))


# ── per-sensor demo threads ────────────────────────────────────────────────

def _demo_bme680():
    rows = _demo_data.get("week5", [])
    if rows:
        i = 0
        while True:
            r = rows[i % len(rows)]
            try:
                t = round(float(r["Temperature"]), 1)
                h = round(float(r["Humidity"]), 1)
                p = round(float(r["Pressure"]), 1)
                g = int(float(r["Gas"]))
                a = round(float(r["Altitude"]), 1)
                with _lock:
                    _data["bme"].update(temperature=t, humidity=h,
                                        pressure=p, gas=g, altitude=a,
                                        ok=True, err="")
            except Exception as e:
                with _lock:
                    _data["bme"].update(ok=False, err=str(e)[:40])
            i += 1
            time.sleep(1)
    else:
        t, h, p, g = 22.0, 50.0, 1013.0, 45000
        while True:
            t = _walk(t, 22.0, 0.2, 15.0, 45.0)
            h = _walk(h, 50.0, 0.5, 10.0, 100.0)
            p = _walk(p, 1013.0, 0.3, 950.0, 1050.0)
            g = _walk(g, 45000, 500, 5000, 100000)
            a = round(44330 * (1 - (p / 1013.25) ** 0.1903), 1)
            with _lock:
                _data["bme"].update(temperature=round(t, 1), humidity=round(h, 1),
                                    pressure=round(p, 1), gas=int(g),
                                    altitude=a, ok=True, err="")
                _hist["bme_temp"].append(round(t, 1))
                _hist["bme_humid"].append(round(h, 1))
            time.sleep(1)


def _demo_pm25():
    # Prefer the structured air_quality.csv; fall back to week5 raw data
    rows = _demo_data.get("air") or _demo_data.get("week5", [])
    air_fmt = bool(_demo_data.get("air"))   # tells us which column names to use
    if rows:
        i = 0
        while True:
            r = rows[i % len(rows)]
            try:
                if air_fmt:
                    p1  = round(float(r["pm1_mean"]),  1)
                    p25 = round(float(r["pm25_mean"]), 1)
                    p10 = round(float(r["pm10_mean"]), 1)
                else:
                    p1  = round(float(r["pm1_standard"]),  1)
                    p25 = round(float(r["pm25_standard"]), 1)
                    p10 = round(float(r["pm10_standard"]), 1)
                with _lock:
                    _data["pm"].update(pm1=p1, pm25=p25, pm10=p10,
                                       ok=True, err="")
                    _hist["pm25"].append(p25)
            except Exception as e:
                with _lock:
                    _data["pm"].update(ok=False, err=str(e)[:40])
            i += 1
            time.sleep(4)
    else:
        p1, p25, p10 = 3.0, 6.0, 9.0
        while True:
            p1  = _walk(p1,  3.0, 0.5, 0, 50)
            p25 = _walk(p25, 6.0, 0.8, 0, 80)
            p10 = _walk(p10, 9.0, 1.0, 0, 150)
            with _lock:
                _data["pm"].update(pm1=round(p1, 1), pm25=round(p25, 1),
                                   pm10=round(p10, 1), ok=True, err="")
                _hist["pm25"].append(round(p25, 1))
            time.sleep(1)


def _demo_scd4x():
    # No recorded CO2 data — random walk
    co2, t, h = 600.0, 22.0, 50.0
    while True:
        co2 = _walk(co2, 600.0, 15.0, 350, 3000)
        t   = _walk(t,   22.0,  0.2,  15,  45)
        h   = _walk(h,   50.0,  0.5,  10,  100)
        with _lock:
            _data["co2"].update(co2=int(co2), temperature=round(t, 1),
                                humidity=round(h, 1), ok=True, err="")
            _hist["co2"].append(int(co2))
            _hist["co2_temp"].append(round(t, 1))
            _hist["co2_humid"].append(round(h, 1))
        time.sleep(2)


def _demo_mlx90393():
    # No recorded magnetometer data — random walk
    mx, my, mz = 20.0, -10.0, 40.0
    while True:
        mx = _walk(mx,  20.0, 1.0, -500, 500)
        my = _walk(my, -10.0, 1.0, -500, 500)
        mz = _walk(mz,  40.0, 1.0, -500, 500)
        mag = math.sqrt(mx * mx + my * my + mz * mz)
        with _lock:
            _data["mag"].update(x=round(mx, 1), y=round(my, 1),
                                z=round(mz, 1), magnitude=round(mag, 1),
                                ok=True, err="")
            _hist["mag"].append(round(mag, 1))
        time.sleep(0.5)


def _demo_mca():
    rows = _demo_data.get("radiation", [])
    if rows:
        i = 0
        total = 0
        while True:
            r = rows[i % len(rows)]
            try:
                cps   = round(float(r["cps"]), 1)
                usv   = round(float(r["usv_hr"]), 4)
                total += int(cps * 2)
                with _lock:
                    _data["mca"].update(cps=cps, usv_hr=usv, total=total,
                                        ok=True, err="")
                    _hist["mca_cps"].append(cps)
            except Exception as e:
                with _lock:
                    _data["mca"].update(ok=False, err=str(e)[:40])
            i += 1
            time.sleep(2)
    else:
        cps, total = 30.0, 0
        while True:
            cps    = _walk(cps, 30.0, 3.0, 0, 800)
            total += int(cps * 2)
            with _lock:
                _data["mca"].update(cps=round(cps, 1), total=total,
                                    ok=True, err="")
                _hist["mca_cps"].append(round(cps, 1))
            time.sleep(2)


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    demo = "--demo" in sys.argv

    if demo:
        _preload_demo_data()

    if demo:
        sensor_threads = [
            threading.Thread(target=_demo_bme680,   daemon=True, name="demo-bme680"),
            threading.Thread(target=_demo_pm25,      daemon=True, name="demo-pm25"),
            threading.Thread(target=_demo_scd4x,     daemon=True, name="demo-scd4x"),
            threading.Thread(target=_demo_mlx90393,  daemon=True, name="demo-mlx90393"),
            threading.Thread(target=_demo_mca,       daemon=True, name="demo-mca"),
        ]
    else:
        sensor_threads = [
            threading.Thread(target=_thread_bme680,   daemon=True, name="bme680"),
            threading.Thread(target=_thread_pm25,      daemon=True, name="pm25"),
            threading.Thread(target=_thread_scd4x,     daemon=True, name="scd4x"),
            threading.Thread(target=_thread_mlx90393,  daemon=True, name="mlx90393"),
            threading.Thread(target=_thread_mca,       daemon=True, name="mca"),
        ]
    for t in sensor_threads:
        t.start()

    pygame.init()

    # Auto-detect screen size — fullscreen by default on Pi, windowed on laptop
    info = pygame.display.Info()
    global SCREEN_W, SCREEN_H
    if "--windowed" in sys.argv:
        SCREEN_W, SCREEN_H = 1280, 720
        flags = 0
    else:
        SCREEN_W = info.current_w
        SCREEN_H = info.current_h
        flags    = pygame.FULLSCREEN

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    pygame.display.set_caption("Sensor Dashboard")
    pygame.mouse.set_visible(False)
    clock  = pygame.time.Clock()

    # Scale fonts relative to screen height (designed for 720p)
    sc = SCREEN_H / 720
    def _fs(base, minimum=11):
        return max(int(base * sc), minimum)

    mono = "dejavusansmono"
    sans = "dejavusans"
    fonts = {
        "xl": pygame.font.SysFont(mono, _fs(36, 24), bold=True),  # gauge value
        "lg": pygame.font.SysFont(sans, _fs(22, 16), bold=True),  # title
        "md": pygame.font.SysFont(sans, _fs(17, 13), bold=True),  # secondary values
        "sm": pygame.font.SysFont(sans, _fs(14, 12)),             # chart labels
        "xs": pygame.font.SysFont(sans, _fs(12, 11)),             # small labels
    }

    scanlines = _make_scanlines(SCREEN_W, SCREEN_H)

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_q, pygame.K_ESCAPE):
                pygame.quit()
                sys.exit(0)

        with _lock:
            d    = {k: dict(v) for k, v in _data.items()}
            hist = {k: list(v) for k, v in _hist.items()}

        _render(screen, fonts, d, hist, scanlines)
        clock.tick(FPS)


if __name__ == "__main__":
    main()
