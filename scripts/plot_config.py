"""
Shared plotting configuration: colourblind-safe palette, policy styles,
and matplotlib defaults.

Palette from Paul Tol's muted/vibrant qualitative schemes, combined with
unique markers and line styles for triple redundant encoding.
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import savgol_filter

# Colourblind-safe named colours (Paul Tol's muted/vibrant qualitative schemes)
BLACK   = "#000000"
INDIGO  = "#332288"
ORANGE  = "#EE7733"
RED     = "#CC3311"
PURPLE  = "#AA3377"
TEAL    = "#44AA99"
WINE    = "#882255"
CYAN    = "#88CCEE"
SAND    = "#DDCC77"
OLIVE   = "#999933"
BLUE    = "#0077BB"

# ── Family-based encoding ────────────────────────────────────────────
# Linestyle  → policy *family*  (shared across all variants)
# Colour     → variant *within* the family (different shades)
# Marker     → unique per policy for additional discrimination
#
# Families: FIFO (solid), SMASH (dashed), Filling (dotted),
#           MSF (dash-dot), Quick Swap (long-dash)
# ─────────────────────────────────────────────────────────────────────

_LS_FIFO  = "-"
_LS_SMASH = "--"
_LS_FILL  = ":"
_LS_MSF   = "-."
_LS_QS    = (0, (5, 2))

policy_styles = {
    # FIFO family — solid, black, circle
    "First-In First-Out":    {"color": BLACK,  "marker": "o", "linestyle": _LS_FIFO},
    # SMASH family — dashed, blue shades, diamond
    "SMASH (w = 2)":         {"color": CYAN,   "marker": "D", "linestyle": _LS_SMASH},
    "SMASH (w = 5)":         {"color": BLUE,   "marker": "D", "linestyle": _LS_SMASH},
    "SMASH (w = 10)":        {"color": INDIGO, "marker": "D", "linestyle": _LS_SMASH},
    # Filling family — dotted, teal/green shades, triangle
    "Back Filling":          {"color": TEAL,   "marker": "^", "linestyle": _LS_FILL},
    "Server Filling":        {"color": OLIVE,  "marker": "^", "linestyle": _LS_FILL},
    # MSF family — dash-dot, orange/red shades, square
    "Most Server First":     {"color": ORANGE, "marker": "s", "linestyle": _LS_MSF},
    "Adaptive MSF":          {"color": RED,    "marker": "s", "linestyle": _LS_MSF},
    "Static MSF":            {"color": SAND,   "marker": "s", "linestyle": _LS_MSF},
    # Quick Swap family — long dash, purple shades, pentagon
    "Quick Swap (l = 1)":    {"color": PURPLE, "marker": "P", "linestyle": _LS_QS},
    "Quick Swap (l = 2048)": {"color": WINE,   "marker": "P", "linestyle": _LS_QS},
}

# Flat colour list (same order as policy_styles) for legacy scripts
policy_colors = [s["color"] for s in policy_styles.values()]


def configure_matplotlib(font_size=21):
    """Apply shared matplotlib defaults for publication-quality figures."""
    plt.rc("font", **{"family": "serif", "serif": ["Palatino"]})
    plt.rc("text", usetex=True)
    matplotlib.rcParams["font.size"] = font_size


def smooth(y, window=5, order=2):
    """Savitzky-Golay smoothing in log-space for data plotted on log axes.

    Linear-space smoothing produces negative artefacts when data spans
    many orders of magnitude.  Operating on log(y) avoids this.
    Returns raw data unchanged if any values are non-positive.
    """
    if len(y) < window:
        return y
    # Ensure odd window
    if window % 2 == 0:
        window -= 1
    if window < order + 2:
        return y
    if np.all(y > 0):
        return np.exp(savgol_filter(np.log(y), window, order))
    # Linear-space fallback is equally broken on log-scale data,
    # so return raw values when log-space smoothing is not possible.
    return y
