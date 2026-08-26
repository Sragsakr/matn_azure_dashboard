"""Stroke-based SVG icon set (Lucide/Feather visual style).

Replaces the Unicode glyphs previously used across app.py's PAGES dict and
the Executive Dashboard (◈ ⏱ ▦ # 👥 ◇ ⚡ ⚠ ✓ 📊 🏆 📁). Every icon is a
plain inline `<svg>` string that inherits color via `currentColor`, so it
automatically respects the active dark/light theme when rendered inside an
element whose CSS `color` is already theme-aware (e.g. our .kpi-icon /
sidebar-label / chip classes). No JS, no external requests, no file I/O —
safe to import from app.py and any page.
"""

# Each entry is the inner markup of a 24x24 stroke icon (viewBox 0 0 24 24),
# stroke="currentColor", no fill — matches the Lucide/Feather look used by
# the rest of the dashboard's flat, line-based visual language.
_ICONS = {
    # ◈ — Executive overview
    "executive": (
        '<path d="M12 2 L22 12 L12 22 L2 12 Z"/>'
        '<path d="M12 7 L17 12 L12 17 L7 12 Z"/>'
    ),
    # ⏱ — Sprint summary / stale
    "clock": (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M12 7 L12 12 L16 14"/>'
    ),
    # ▦ — Sprint board
    "board": (
        '<rect x="3" y="3" width="7" height="18" rx="1"/>'
        '<rect x="14" y="3" width="7" height="10" rx="1"/>'
        '<rect x="14" y="16" width="7" height="5" rx="1"/>'
    ),
    # # — Tag analysis
    "tag": (
        '<line x1="4" y1="9" x2="20" y2="9"/>'
        '<line x1="4" y1="15" x2="20" y2="15"/>'
        '<line x1="10" y1="3" x2="8" y2="21"/>'
        '<line x1="16" y1="3" x2="14" y2="21"/>'
    ),
    # 👥 — Team analysis
    "team": (
        '<circle cx="9" cy="8" r="3.2"/>'
        '<path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/>'
        '<circle cx="17.2" cy="8.5" r="2.6"/>'
        '<path d="M15.5 14.3c2.9.3 5 2.6 5 5.7"/>'
    ),
    # ◇ — Area analysis
    "area": '<path d="M12 2 L22 12 L12 22 L2 12 Z"/>',
    # ⚡ — Active now
    "active": '<polygon points="13 2 4 14 11 14 10 22 20 9 13 9 13 2"/>',
    # ⚠ — Risks & aging
    "warning": (
        '<path d="M12 3 L22 20 L2 20 Z"/>'
        '<line x1="12" y1="9" x2="12" y2="14"/>'
        '<circle cx="12" cy="17.2" r="0.6" fill="currentColor" stroke="none"/>'
    ),
    # ✓ — Data quality
    "check": '<polyline points="4 12.5 9.5 18 20 6"/>',
    # 📊 — Repository intelligence
    "chart": (
        '<line x1="4" y1="21" x2="20" y2="21"/>'
        '<rect x="6" y="12" width="3.4" height="9" rx="0.6"/>'
        '<rect x="12" y="7" width="3.4" height="14" rx="0.6"/>'
        '<rect x="18" y="3" width="0" height="18" rx="0.6" opacity="0"/>'
    ),
    # 🏆 — Releases
    "trophy": (
        '<path d="M7 4h10v4a5 5 0 0 1-10 0Z"/>'
        '<path d="M7 5H4a3 3 0 0 0 3 5"/>'
        '<path d="M17 5h3a3 3 0 0 1-3 5"/>'
        '<line x1="12" y1="13" x2="12" y2="17"/>'
        '<path d="M8 21h8"/>'
        '<path d="M9.5 17h5l1 4h-7Z"/>'
    ),
    # 📁 — Raw data
    "folder": '<path d="M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z"/>',
    # Extra glyphs used inline on the Executive Dashboard KPI row.
    "percent": (
        '<line x1="5" y1="19" x2="19" y2="5"/>'
        '<circle cx="7.5" cy="7.5" r="2.2"/>'
        '<circle cx="16.5" cy="16.5" r="2.2"/>'
    ),
    "backlog": '<path d="M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z"/>',
    "hierarchy": (
        '<circle cx="12" cy="4.5" r="2"/>'
        '<circle cx="5" cy="19.5" r="2"/>'
        '<circle cx="19" cy="19.5" r="2"/>'
        '<path d="M12 6.5 V12 M12 12 L5 17.5 M12 12 L19 17.5"/>'
    ),
}


def icon_svg(name, size=16, color="currentColor", stroke_width=2):
    """Return an inline <svg> string for the icon `name` at the given size.

    `color` defaults to `currentColor` so the icon inherits the surrounding
    element's CSS color (and therefore the active theme) automatically;
    pass an explicit hex/CSS color (e.g. an ACCENTS value) to force one.
    """
    body = _ICONS.get(name)
    if body is None:
        raise KeyError(f"Unknown icon '{name}'. Available: {sorted(_ICONS)}")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle">'
        f'{body}</svg>'
    )


def render_icon(container, name, size=16, color="currentColor", stroke_width=2):
    """Render icon `name` inline via st.markdown into a Streamlit container
    (a `with` block, a column, or the `st` module itself)."""
    container.markdown(
        icon_svg(name, size=size, color=color, stroke_width=stroke_width),
        unsafe_allow_html=True,
    )


ICON_NAMES = tuple(sorted(_ICONS))
