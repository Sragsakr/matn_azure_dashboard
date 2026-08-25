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
        html, body, [class*="css"] { font-family:'Inter','Noto Sans Arabic','Segoe UI',sans-serif; font-size:14px; }
        .stApp { background:var(--bg); direction:__DIR__;
            color:var(--ink); transition:background .25s ease,color .25s ease; }
        .block-container { max-width:1480px; padding:.9rem 1.6rem 2.2rem; }
        h1, h2, h3 { color:var(--ink); letter-spacing:-.01em; text-align:__ALIGN__; }
        h2 { font-size:1.12rem !important; margin-top:.15rem; margin-bottom:.2rem; }
        h3 { font-size:.92rem !important; margin-bottom:.05rem; }
        p, .stCaption { color:var(--muted); font-size:.82rem; }

        .enterprise-header { display:flex; align-items:center; justify-content:space-between;
            gap:1rem; background:var(--surface);
            border:1px solid var(--line); border-radius:8px; padding:.7rem 1rem;
            margin:0 0 .8rem; }
        .enterprise-header h1 { margin:.08rem 0 0; font-size:1.05rem !important; font-weight:800; }
        .header-kicker { color:var(--muted); font-size:.6rem; font-weight:800;
            letter-spacing:.12em; }
        .azure-pill { display:inline-flex; align-items:center; gap:.4rem;
            border:1px solid var(--line); background:var(--surface2); color:var(--ink);
            border-radius:5px; padding:.35rem .65rem; font-size:.68rem; font-weight:700;
            white-space:nowrap; }
        .azure-dot { width:5px; height:5px; border-radius:50%; background:var(--accent-green);
            animation:pulse-dot 2.4s infinite; }
        @keyframes pulse-dot {
            0%,100% { opacity:1; } 50% { opacity:.55; } }

        div[data-testid="stSidebar"] { background:var(--surface);
            border-inline-end:1px solid var(--line); }
        div[data-testid="stSidebar"] > div:first-child { padding-top:.7rem; }
        div[data-testid="stSidebar"] * { text-align:__ALIGN__; }
        section[data-testid="stSidebar"] { min-width:230px !important; max-width:230px !important; }
        .sidebar-brand { display:flex; align-items:center; gap:.55rem;
            padding:.1rem .1rem .7rem; margin-bottom:.4rem; border-bottom:1px solid var(--line); }
        .brand-mark { display:grid; place-items:center; width:30px; height:30px;
            border-radius:6px; color:#FFF; font-size:.85rem; font-weight:900;
            background:var(--accent-blue); }
        .sidebar-brand strong { display:block; color:var(--ink); font-size:.76rem; }
        .sidebar-brand span { display:block; color:var(--muted); font-size:.62rem; margin-top:.04rem; }
        .sidebar-label { color:var(--muted2) !important; font-size:.6rem; font-weight:800;
            letter-spacing:.05em; text-transform:uppercase; margin:.7rem .3rem .3rem; }
        div[data-testid="stSidebar"] div[role="radiogroup"] { gap:.05rem; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding:.4rem .5rem; border:1px solid transparent; border-radius:5px;
            margin-bottom:1px; transition:background .12s ease; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label p { color:var(--muted); font-size:.74rem; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background:var(--surface2); }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background:var(--surface2); border-color:transparent; }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
            color:var(--accent-blue) !important; font-weight:700; }
        div[data-testid="stSidebar"] button[kind="primary"] {
            width:100%; border:0; border-radius:5px;
            background:var(--accent-blue); font-weight:700; font-size:.76rem; }
        div[data-testid="stSidebar"] [data-testid="stMetric"] {
            background:var(--surface2); border:1px solid var(--line); box-shadow:none;
            min-height:54px; padding:6px 8px; border-radius:6px; }
        div[data-testid="stSidebar"] [data-testid="stMetricLabel"] p {
            color:var(--muted) !important; font-size:.62rem; }
        div[data-testid="stSidebar"] [data-testid="stMetricValue"] {
            color:var(--ink); font-size:.9rem; }

        .kpi-card { min-height:78px; position:relative; overflow:hidden;
            background:var(--surface);
            border:1px solid var(--line); border-radius:6px; padding:.6rem .7rem; }
        .kpi-card::before { content:""; position:absolute; inset-inline-start:0; top:0;
            width:100%; height:2px; background:var(--accent); }
        .kpi-card-top { display:flex; justify-content:space-between; align-items:flex-start; gap:.3rem; }
        .kpi-label { color:var(--muted); font-size:.62rem; font-weight:700; }
        .kpi-icon { display:grid; place-items:center; width:20px; height:20px; border-radius:5px;
            background:color-mix(in srgb,var(--accent) 15%,transparent);
            color:var(--accent); font-size:.68rem; font-weight:800; }
        .kpi-value { color:var(--ink); font-size:1.25rem; line-height:1.05;
            font-weight:800; margin-top:.4rem; letter-spacing:-.01em; }
        .kpi-sub { color:var(--muted2); font-size:.6rem; font-weight:600; margin-top:.2rem; }
        .health-ribbon { display:flex; align-items:center; gap:.5rem;
            background:var(--surface);
            border:1px solid var(--line);
            border-inline-start:3px solid var(--health);
            color:var(--ink); padding:.55rem .8rem; border-radius:6px;
            font-size:.78rem; font-weight:700; margin-bottom:.8rem; }
        .health-ribbon .badge { background:color-mix(in srgb,var(--health) 16%,transparent); color:var(--health);
            padding:.15rem .55rem; border-radius:4px; font-size:.64rem; font-weight:800; }

        .pctpill { font-size:.62rem; padding:.12rem .5rem; border-radius:4px; font-weight:800;
            display:inline-block; }
        .pctpill.zero { background:color-mix(in srgb,var(--accent-red) 14%,transparent); color:var(--accent-red); }
        .pctpill.mid { background:color-mix(in srgb,var(--accent-amber) 14%,transparent); color:var(--accent-amber); }
        .pctpill.high { background:color-mix(in srgb,var(--accent-green) 14%,transparent); color:var(--accent-green); }

        section.section-head { display:flex; align-items:center; gap:.4rem; margin:.6rem 0 .3rem;
            padding-bottom:.25rem; border-bottom:1px solid var(--line); }
        section.section-head .chip { display:grid; place-items:center; width:19px; height:19px;
            border-radius:5px; background:color-mix(in srgb,var(--accent-blue) 14%,transparent);
            color:var(--accent-blue); font-size:.68rem; }
        section.section-head h3 { font-size:.85rem !important; font-weight:800; }

        div[data-testid="stDataFrame"], div[data-testid="stChart"] {
            background:var(--surface); border:1px solid var(--line); border-radius:6px;
            overflow:hidden; }
        div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {
            color:var(--ink); font-size:.78rem; }
        div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] [role="row"] {
            min-height:30px !important; }
        div[data-testid="stAlert"] { border-radius:6px; background:var(--surface);
            border:1px solid var(--line); color:var(--ink); font-size:.8rem; }
        hr { border-color:var(--line); margin:.5rem 0 .7rem; }
        #MainMenu, footer { visibility:hidden; }
        ::-webkit-scrollbar { width:6px; height:6px; }
        ::-webkit-scrollbar-track { background:transparent; }
        ::-webkit-scrollbar-thumb { background:var(--line); border-radius:3px; }
        ::-webkit-scrollbar-thumb:hover { background:var(--muted); }
        @media (max-width:780px) {
            .block-container { padding:.6rem .8rem 1.6rem; }
            .enterprise-header { align-items:flex-start; }
            .azure-pill { font-size:0; }
            .azure-pill::after { content:'Azure'; font-size:.68rem; }
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
