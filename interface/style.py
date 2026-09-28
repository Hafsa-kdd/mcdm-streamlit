"""Habillage visuel : CSS global et petits blocs HTML (en-têtes, cartes KPI)."""
from html import escape

import streamlit as st

GRADIENT = "linear-gradient(135deg, #A78BFA 0%, #C4A1F7 45%, #F3A8D6 100%)"

CSS = f"""
<style>
.stApp {{
    background: linear-gradient(135deg, #EFE8FF 0%, #EEF1FF 45%, #FCEEF7 100%);
}}
.block-container {{ padding-top: 2.2rem; max-width: 1250px; }}

/* Cartes : tout conteneur dont la clé commence par "card" */
[class*="st-key-card"] {{
    background: rgba(255, 255, 255, 0.82);
    border-radius: 22px;
    padding: 1.3rem 1.5rem;
    box-shadow: 0 8px 30px rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.9);
}}

/* Onglets façon "pilules" */
.stTabs [data-baseweb="tab-list"] {{
    gap: .4rem; background: rgba(255,255,255,.7); padding: .35rem; border-radius: 999px;
    width: fit-content; box-shadow: 0 4px 18px rgba(139, 92, 246, .08);
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 999px; padding: .45rem 1.1rem; height: auto;
}}
.stTabs [aria-selected="true"] {{
    background: {GRADIENT}; color: white !important;
}}
.stTabs [aria-selected="true"] p {{ color: white !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}

/* En-tête de page */
.hero h1 {{ font-size: 2rem; margin: 0; padding: 0; }}
.hero p  {{ color: #7C7898; margin: .2rem 0 0 0; }}

/* Titre de section */
.section-title {{ display:flex; align-items:center; gap:.7rem; margin: .2rem 0 .6rem 0; }}
.section-title .num {{
    background: {GRADIENT}; color:white; width:2rem; height:2rem; border-radius:50%;
    display:flex; align-items:center; justify-content:center; font-weight:600; flex-shrink:0;
}}
.section-title h3 {{ margin:0; padding:0; font-size:1.15rem; }}
.section-sub {{ color:#7C7898; font-size:.92rem; margin:-.3rem 0 .8rem 2.7rem; }}

/* Cartes KPI */
.kpi {{
    border-radius: 20px; padding: 1.1rem 1.3rem; height: 100%;
    background: rgba(255,255,255,.85); box-shadow: 0 8px 30px rgba(139,92,246,.08);
}}
.kpi.grad {{ background: {GRADIENT}; color: white; }}
.kpi .label {{ font-size: .85rem; opacity: .8; }}
.kpi .value {{ font-size: 1.65rem; font-weight: 600; line-height: 1.3; }}
.kpi .hint  {{ font-size: .8rem; opacity: .75; }}

/* Barre latérale */
.brand {{ display:flex; align-items:center; gap:.6rem; margin-bottom: 1.2rem; }}
.brand .logo {{
    width: 2.3rem; height: 2.3rem; border-radius: 50%; background: {GRADIENT};
    box-shadow: inset -7px -3px 0 rgba(255,255,255,.55);
}}
.brand .name {{ font-size: 1.35rem; font-weight: 600; color: #8B5CF6; }}
.step {{ display:flex; align-items:center; gap:.6rem; padding:.5rem .7rem; border-radius: 12px; margin-bottom:.3rem; }}
.step .dot {{
    width:1.5rem; height:1.5rem; border-radius:50%; display:flex; align-items:center; justify-content:center;
    font-size:.8rem; background:#EFEAFE; color:#8B5CF6; flex-shrink:0;
}}
.step.done .dot {{ background: {GRADIENT}; color: white; }}
.step .txt {{ font-size:.9rem; }}
.step .txt small {{ display:block; color:#9A96B5; font-size:.75rem; }}
</style>
"""


def inject():
    st.html(CSS)


def hero(title, subtitle):
    st.html(f'<div class="hero"><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>')


def section(num, title, subtitle=""):
    sub = f'<div class="section-sub">{escape(subtitle)}</div>' if subtitle else ""
    st.html(f'<div class="section-title"><div class="num">{num}</div><h3>{escape(title)}</h3></div>{sub}')


def kpi(label, value, hint="", gradient=False):
    cls = "kpi grad" if gradient else "kpi"
    st.html(f'<div class="{cls}"><div class="label">{escape(label)}</div>'
            f'<div class="value">{escape(str(value))}</div><div class="hint">{escape(hint)}</div></div>')


def brand(name="MCDM"):
    st.html(f'<div class="brand"><div class="logo"></div><div class="name">{name}</div></div>')


def step(label, detail, done):
    icon = "✓" if done else "•"
    st.html(f'<div class="step {"done" if done else ""}"><div class="dot">{icon}</div>'
            f'<div class="txt">{escape(label)}<small>{escape(detail)}</small></div></div>')
