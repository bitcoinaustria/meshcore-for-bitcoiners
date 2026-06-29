"""Draw the MeshCore-Austria regions map from scratch.

Our own figure: a public-domain Natural Earth basemap (Austria + neighbours,
faint state boundaries) plus three hand-placed ellipses for the community
regions at-west / at-ost / at-sued. No third-party map artwork — safe to ship
under the repo's Apache-2.0 license.

Run:  uv run draw_regions.py
Out:  ../pix/austria-regions.pdf  (+ a preview PNG next to it)
"""
from math import cos, radians
from pathlib import Path
from urllib.request import urlretrieve

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

HERE = Path(__file__).parent
CACHE = HERE / "ne_cache"
# The deck uses a committed PNG (repo gitignores *.pdf, so a vector PDF figure
# would not survive a fresh checkout / CI). 300 dpi is crisp at slide size.
OUT_PNG = HERE.parent / "pix" / "austria-regions.png"

# Public-domain Natural Earth source (auto-downloaded once into ne_cache/).
NE_BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
NE_FILES = {
    "ne_50m_admin_0_countries.geojson": NE_BASE + "ne_50m_admin_0_countries.geojson",
    "ne_10m_admin_1_states_provinces.geojson": NE_BASE + "ne_10m_admin_1_states_provinces.geojson",
}


def ensure_data():
    CACHE.mkdir(exist_ok=True)
    for name, url in NE_FILES.items():
        dst = CACHE / name
        if not dst.exists():
            print(f"downloading {name} ...")
            urlretrieve(url, dst)

# --- view window (lon/lat) ---------------------------------------------------
LON0, LON1 = 8.9, 17.5
LAT0, LAT1 = 46.1, 49.3
ASPECT = 1.0 / cos(radians((LAT0 + LAT1) / 2))  # de-squish lon at this latitude

# --- the three community regions: (label, lon, lat, width°, height°, angle) --
REGIONS = [
    ("at-west", 11.7, 47.45, 6.4, 2.0, -7, "#5BA6D6", "#2E6E9E"),
    ("at-ost",  14.9, 48.10, 4.6, 1.8, 2, "#73C16E", "#3E8C45"),
    ("at-sued", 14.9, 46.85, 4.8, 1.45, -4, "#E89B57", "#C26F28"),
]

def main():
    ensure_data()
    countries = gpd.read_file(CACHE / "ne_50m_admin_0_countries.geojson")
    states = gpd.read_file(CACHE / "ne_10m_admin_1_states_provinces.geojson")
    at_states = states[states["admin"] == "Austria"]
    austria = countries[countries["ADMIN"] == "Austria"]

    fig, ax = plt.subplots(figsize=(6.4, 4.3))

    # neighbours: faint outlines for context
    countries.boundary.plot(ax=ax, color="#B7B7B7", linewidth=0.6, zorder=1)
    # austria: faint fill + stronger outline
    austria.plot(ax=ax, facecolor="#FFFFFF", edgecolor="none", alpha=0.45, zorder=2)
    at_states.boundary.plot(ax=ax, color="#C2C2C2", linewidth=0.4, zorder=3)
    austria.boundary.plot(ax=ax, color="#6E6E6E", linewidth=1.1, zorder=4)

    # the three regions
    for label, lon, lat, w, h, ang, fc, ec in REGIONS:
        ax.add_patch(Ellipse((lon, lat), w, h, angle=ang, facecolor=fc,
                             edgecolor=ec, alpha=0.34, linewidth=1.2, zorder=5))
        ax.text(lon, lat, label, ha="center", va="center", zorder=6,
                fontsize=11, color="#222222", family="sans-serif")

    # faint whole-country "at" hint near the top
    ax.text(12.4, 49.05, "at", ha="center", va="center", fontsize=9,
            color="#8A8A8A", style="italic", zorder=6)

    ax.set_xlim(LON0, LON1)
    ax.set_ylim(LAT0, LAT1)
    ax.set_aspect(ASPECT)
    ax.axis("off")
    fig.tight_layout(pad=0.1)

    fig.savefig(OUT_PNG, transparent=True, dpi=300, bbox_inches="tight", pad_inches=0.02)
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
