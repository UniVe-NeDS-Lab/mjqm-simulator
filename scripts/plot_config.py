"""
Shared plotting configuration: colourblind-safe palette, policy styles,
and matplotlib defaults for thesis figures.

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

policy_styles = {
    "First-In First-Out":    {"color": BLACK,  "marker": "o", "linestyle": "-"},
    "Most Server First":     {"color": INDIGO, "marker": "s", "linestyle": "--"},
    "Server Filling":        {"color": ORANGE, "marker": "^", "linestyle": "-."},
    "Back Filling":          {"color": RED,    "marker": "v", "linestyle": ":"},
    "SMASH (w = 2)":         {"color": PURPLE, "marker": "D", "linestyle": "-"},
    "SMASH (w = 5)":         {"color": TEAL,   "marker": "P", "linestyle": "--"},
    "SMASH (w = 10)":        {"color": WINE,   "marker": "X", "linestyle": "-."},
    "Adaptive MSF":          {"color": CYAN,   "marker": "h", "linestyle": ":"},
    "Static MSF":            {"color": SAND,   "marker": "d", "linestyle": "--"},
    "Quick Swap (l = 1)":    {"color": OLIVE,  "marker": "<", "linestyle": "-."},
    "Quick Swap (l = 2048)": {"color": BLUE,   "marker": ">", "linestyle": ":"},
}

# Flat colour list (same order as policy_styles) for legacy scripts
policy_colors = [s["color"] for s in policy_styles.values()]


def configure_matplotlib(font_size=21):
    """Apply shared matplotlib defaults for thesis-quality figures."""
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
