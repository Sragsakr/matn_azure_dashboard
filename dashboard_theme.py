"""Theme palette, Altair theming, and chart factories for the dashboard.

ACCENTS and PALETTES below are the single source of truth for every color
used across dashboard_app.py, dashboard_styles.py, and this module. Do not
define additional hex-literal color dicts elsewhere — import and reuse these.
"""

import altair as alt

ACCENTS = {
    "blue": "#1D4ED8", "green": "#047857", "purple": "#6D28D9",
    "amber": "#B45309", "red": "#B91C1C", "teal": "#0F766E",
    "pink": "#BE185D", "gold": "#A16207", "indigo": "#4338CA",
}

PALETTES = {
    "dark": {
        "bg": "#0C0E12", "surface": "#15181F", "surface2": "#1A1E27",
        "line": "#282D38", "ink": "#E8EAF0", "muted": "#9297A6", "muted2": "#5F6472",
    },
    "light": {
        "bg": "#EFF1F4", "surface": "#FFFFFF", "surface2": "#F5F6F9",
        "line": "#DADEE6", "ink": "#1A1D24", "muted": "#5B6070", "muted2": "#8B90A0",
    },
}


def chart_theme(mode):
    """Altair-facing subset of the active palette plus accent list."""
    palette = PALETTES[mode]
    return {
        **palette,
        "series": [ACCENTS[key] for key in
                   ("blue", "green", "purple", "amber", "teal", "pink")],
        "font": "'Inter','Noto Sans Arabic','Segoe UI',sans-serif",
    }


def _configure(chart, theme, title=None, legend_columns=None):
    legend_kwargs = dict(
        labelColor=theme["ink"], titleColor=theme["ink"],
        strokeColor=theme["line"], orient="bottom", labelFontSize=11,
    )
    if legend_columns:
        legend_kwargs.update(columns=legend_columns, labelLimit=140, symbolSize=80)
    chart = (
        chart.configure_view(stroke=None)
        .configure(background="transparent")
        .configure_axis(
            labelColor=theme["muted"], titleColor=theme["muted"],
            gridColor=theme["line"], domainColor=theme["line"],
            labelFontSize=11, titleFontSize=12, labelFont=theme["font"],
        )
        .configure_legend(**legend_kwargs)
        .configure_title(color=theme["ink"], fontSize=13, anchor="start")
    )
    return chart


def donut_chart(frame, field, value_field, theme, colors=None):
    base = alt.Chart(frame).mark_arc(innerRadius=52, outerRadius=82, cornerRadius=4)
    encoding = {
        "theta": alt.Theta(f"{value_field}:Q", stack=True),
        "color": alt.Color(f"{field}:N", sort="-y"),
        "tooltip": [alt.Tooltip(f"{field}:N"), alt.Tooltip(f"{value_field}:Q")],
    }
    if colors:
        encoding["color"]["scale"] = alt.Scale(domain=list(colors), range=list(colors.values()))
    else:
        encoding["color"]["scale"] = alt.Scale(range=theme["series"])
    return _configure(base.encode(**encoding), theme, legend_columns=2)


def hbar_chart(frame, x_field, y_field, theme, color=None):
    chart = alt.Chart(frame).mark_bar(cornerRadius=3, height=16).encode(
        x=alt.X(f"{x_field}:Q", axis=None),
        y=alt.Y(f"{y_field}:N", sort="-x", axis=alt.Axis(ticks=False, labelLimit=200)),
        color=alt.value(color or theme["series"][0]),
        tooltip=[alt.Tooltip(f"{y_field}:N"), alt.Tooltip(f"{x_field}:Q")],
    ).properties(height=max(140, 30 * len(frame)))
    return _configure(chart, theme)


def grouped_hbar_chart(frame, y_field, columns, colors, theme):
    long_frame = frame.melt(id_vars=[y_field], value_vars=columns,
                            var_name="metric", value_name="amount")
    chart = alt.Chart(long_frame).mark_bar(cornerRadius=2, height=9).encode(
        x=alt.X("amount:Q", axis=None),
        y=alt.Y(f"{y_field}:N", sort="-x", axis=alt.Axis(ticks=False, labelLimit=200)),
        yOffset="metric:N",
        color=alt.Color("metric:N", scale=alt.Scale(
            domain=columns, range=[colors[key] for key in columns])),
        tooltip=[alt.Tooltip(f"{y_field}:N"), "metric:N", alt.Tooltip("amount:Q")],
    ).properties(height=max(160, 34 * len(frame)))
    return _configure(chart, theme)


def stacked_hbar_chart(frame, category_field, segment_field, amount_field, theme):
    chart = alt.Chart(frame).mark_bar(cornerRadius=2, height=18).encode(
        x=alt.X(f"{amount_field}:Q", stack="zero", axis=None),
        y=alt.Y(f"{category_field}:N", axis=alt.Axis(ticks=False, labelLimit=200)),
        color=alt.Color(f"{segment_field}:N", scale=alt.Scale(range=theme["series"])),
        tooltip=[category_field, segment_field, alt.Tooltip(f"{amount_field}:Q")],
    ).properties(height=max(150, 40 * frame[category_field].nunique()))
    return _configure(chart, theme)


def area_trend_chart(frame, x_field, y_fields, colors, theme):
    transformed = frame.melt("period", var_name="flow", value_name="count")
    chart = alt.Chart(transformed).mark_area(line=True, opacity=.22).encode(
        x=alt.X("period:N", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("count:Q"),
        color=alt.Color("flow:N", scale=alt.Scale(
            domain=y_fields, range=[colors[key] for key in y_fields]), legend=None),
        tooltip=["period:N", "flow:N", alt.Tooltip("count:Q")],
    ).properties(height=230)
    chart = chart.configure_line(color=colors[y_fields[-1]])
    return _configure(chart, theme)
