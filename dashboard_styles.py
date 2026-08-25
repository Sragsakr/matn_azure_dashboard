"""Inject the active dark/light theme for the Streamlit dashboard."""

import streamlit as st

from dashboard_theme import ACCENTS, PALETTES


def apply_theme(mode, arabic):
    palette = PALETTES[mode]
    direction = "rtl" if arabic else "ltr"
    align = "right" if arabic else "left"
    css_vars = ";".join(f"--{name}:{value}" for name, value in palette.items())
    css_vars += "".join(
        f";--accent-{name}:{value}" for name, value in ACCENTS.items()
    )
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Arabic:wght@400;500;600;700;800&display=swap');
        :root {{__CSS_VARS__}}
        html, body, [class*="css"] { font-family:'Inter','Noto Sans Arabic','Segoe UI',sans-serif; }
        .stApp { background:var(--bg); direction:__DIR__;
            color:var(--ink); transition:background .25s ease,color .25s ease; }
        .block-container { max-width:1480px; padding:1.1rem 2rem 3rem; }
        h1, h2, h3 { color:var(--ink); letter-spacing:-.02em; text-align:__ALIGN__; }
        h2 { font-size:1.42rem !important; margin-top:.3rem; }
        h3 { font-size:1.05rem !important; margin-bottom:.1rem; }
        p, .stCaption { color:var(--muted); }

        .enterprise-header { display:flex; align-items:center; justify-content:space-between;
            gap:1rem; background:linear-gradient(135deg,var(--surface) 0%,var(--surface2) 100%);
            border:1px solid var(--line); border-radius:16px; padding:1.05rem 1.3rem;
            margin:0 0 1.25rem; box-shadow:0 4px 14px -6px rgba(0,0,0,__SHADOW__); }
        .enterprise-header h1 { margin:.12rem 0 0; font-size:1.32rem !important; font-weight:800; }
        .header-kicker { color:var(--muted); font-size:.66rem; font-weight:800;
            letter-spacing:.14em; }
        .azure-pill { display:inline-flex; align-items:center; gap:.45rem;
            border:1px solid var(--line); background:var(--surface2); color:var(--ink);
            border-radius:999px; padding:.5rem .8rem; font-size:.75rem; font-weight:700;
            white-space:nowrap; box-shadow:inset 0 1px 0 rgba(255,255,255,.04); }
        .azure-dot { width:7px; height:7px; border-radius:50%; background:var(--accent-green);
            box-shadow:0 0 0 3px rgba(16,185,129,.18); animation:pulse-dot 2.4s infinite; }
        @keyframes pulse-dot {
            0%,100% { opacity:1; } 50% { opacity:.55; } }

        div[data-testid="stSidebar"] { background:var(--surface);
            border-inline-end:1px solid var(--line); }
        div[data-testid="stSidebar"] > div:first-child { padding-top:1rem; }
        div[data-testid="stSidebar"] * { text-align:__ALIGN__; }
        .sidebar-brand { display:flex; align-items:center; gap:.72rem;
            padding:.15rem .15rem 1rem; margin-bottom:.65rem; border-bottom:1px solid var(--line); }
        .brand-mark { display:grid; place-items:center; width:39px; height:39px;
            border-radius:11px; color:#FFF; font-size:1rem; font-weight:900;
            background:linear-gradient(145deg,var(--accent-blue),var(--accent-indigo));
            box-shadow:0 5px 14px -3px rgba(59,130,246,.5); }
        .sidebar-brand strong { display:block; color:var(--ink); font-size:.88rem; }
        .sidebar-brand span { display:block; color:var(--muted); font-size:.7rem; margin-top:.06rem; }
        .sidebar-label { color:var(--muted) !important; font-size:.64rem; font-weight:800;
            letter-spacing:.12em; margin:1rem .65rem .4rem; }
        div[data-testid="stSidebar"] div[role="radiogroup"] { gap:.12rem; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding:.58rem .72rem; border:1px solid transparent; border-radius:10px;
            margin-bottom:1px; transition:all .16s ease; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label p { color:var(--muted); font-size:.84rem; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background:var(--surface2); }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background:linear-gradient(90deg,rgba(59,130,246,.16),rgba(99,102,241,.07));
            border-color:rgba(59,130,246,.35); }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
            color:var(--accent-blue) !important; font-weight:700; }
        div[data-testid="stSidebar"] button[kind="primary"] {
            width:100%; border:0; border-radius:10px;
            background:linear-gradient(135deg,#3B82F6,#6366F1);
            box-shadow:0 6px 16px -4px rgba(59,130,246,.45); font-weight:700; }
        div[data-testid="stSidebar"] [data-testid="stMetric"] {
            background:var(--surface2); border:1px solid var(--line); box-shadow:none;
            min-height:70px; padding:8px 10px; border-radius:10px; }
        div[data-testid="stSidebar"] [data-testid="stMetricLabel"] p {
            color:var(--muted) !important; font-size:.68rem; }
        div[data-testid="stSidebar"] [data-testid="stMetricValue"] {
            color:var(--ink); font-size:1.05rem; }

        @keyframes card-in {
            from { opacity:0; transform:translateY(9px); }
            to { opacity:1; transform:translateY(0); } }
        .kpi-card { min-height:128px; position:relative; overflow:hidden;
            background:linear-gradient(180deg,var(--surface) 0%,var(--surface2) 100%);
            border:1px solid var(--line); border-radius:15px; padding:1rem;
            animation:card-in .38s ease both;
            transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease; }
        .kpi-card::before { content:""; position:absolute; inset-inline-start:0; top:0;
            width:100%; height:3px; background:linear-gradient(90deg,var(--accent),transparent 85%); }
        .kpi-card:hover { transform:translateY(-3px); border-color:color-mix(in srgb,var(--accent) 40%,var(--line));
            box-shadow:0 14px 26px -14px color-mix(in srgb,var(--accent) 55%,transparent); }
        .kpi-card-top { display:flex; justify-content:space-between; align-items:flex-start; gap:.4rem; }
        .kpi-label { color:var(--muted); font-size:.66rem; font-weight:800;
            letter-spacing:.075em; text-transform:uppercase; }
        .kpi-icon { display:grid; place-items:center; width:30px; height:30px; border-radius:9px;
            background:color-mix(in srgb,var(--accent) 13%,transparent);
            border:1px solid color-mix(in srgb,var(--accent) 28%,transparent);
            color:var(--accent); font-size:.85rem; }
        .kpi-value { color:var(--ink); font-size:1.78rem; line-height:1.08;
            font-weight:800; margin-top:1rem; letter-spacing:-.02em; }
        .health-ribbon { display:flex; align-items:center; gap:.6rem;
            border:1px solid color-mix(in srgb,var(--health) 32%,var(--line));
            border-inline-start:4px solid var(--health);
            background:color-mix(in srgb,var(--health) 12%,var(--surface));
            color:var(--ink); padding:.82rem 1rem; border-radius:12px;
            font-size:.9rem; font-weight:700; margin-bottom:1rem; }

        section.section-head { display:flex; align-items:center; gap:.55rem; margin:1.15rem 0 .35rem; }
        section.section-head .chip { display:grid; place-items:center; width:27px; height:27px;
            border-radius:8px; background:color-mix(in srgb,var(--accent-blue) 14%,transparent);
            color:var(--accent-blue); font-size:.82rem; }

        div[data-testid="stDataFrame"], div[data-testid="stChart"] {
            background:var(--surface); border:1px solid var(--line); border-radius:12px;
            overflow:hidden; box-shadow:0 2px 6px -2px rgba(0,0,0,.14); }
        div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {
            color:var(--ink); }
        div[data-testid="stAlert"] { border-radius:11px; background:var(--surface);
            border:1px solid var(--line); color:var(--ink); }
        hr { border-color:var(--line); margin:.8rem 0 1.1rem; }
        #MainMenu, footer { visibility:hidden; }
        ::-webkit-scrollbar { width:7px; height:7px; }
        ::-webkit-scrollbar-track { background:transparent; }
        ::-webkit-scrollbar-thumb { background:var(--line); border-radius:4px; }
        ::-webkit-scrollbar-thumb:hover { background:var(--muted); }
        @media (max-width:780px) {
            .block-container { padding:.8rem 1rem 2rem; }
            .enterprise-header { align-items:flex-start; }
            .azure-pill { font-size:0; }
            .azure-pill::after { content:'Azure'; font-size:.72rem; }
        }
        </style>
        """.replace("__CSS_VARS__", css_vars).replace("__DIR__", direction)\
            .replace("__ALIGN__", align)\
            .replace("__SHADOW__", ".35" if mode == "dark" else ".08"),
        unsafe_allow_html=True,
    )


def section_header(title_english, title_arabic, icon="◆"):
    st.markdown(
        f"<section class='section-head'><span class='chip'>{icon}</span>"
        f"<h3>{title_english if st.session_state.get('language_selector', 'العربية') == 'English' else title_arabic}</h3></section>",
        unsafe_allow_html=True,
    )
