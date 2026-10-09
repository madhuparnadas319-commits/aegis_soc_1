import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from datetime import datetime, timedelta
from textwrap import dedent
from html import escape
import time
import uuid
import json


# =========================================================
# AEGIS SOC
# Governed Agentic AI for SOC Alert Triage
# & Incident Investigation
#
# LIVE INTEGRATED STREAMLIT FRONTEND
# Uses existing AEGIS FastAPI dashboard routes and n8n orchestration.
# Local prototype: synthetic security events; no external banking actions.
# =========================================================


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AEGIS SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# RAW HTML RENDERER
# =========================================================
#
# IMPORTANT:
# We intentionally use st.html() rather than st.markdown()
# for UI HTML.
#
# st.markdown() can interpret indented multiline HTML
# as Markdown code blocks.
# =========================================================

def ui_html(content: str):
    st.html(dedent(content).strip())


# =========================================================
# DESIGN SYSTEM
# =========================================================

ui_html(
    """
    <style>

    /* =====================================================
       ROOT
    ===================================================== */

    :root {
        --bg: #04070d;
        --bg-soft: #07101b;
        --panel: rgba(9, 16, 28, 0.90);
        --panel-soft: rgba(12, 20, 34, 0.82);

        --border: rgba(255, 255, 255, 0.075);
        --border-strong: rgba(255, 255, 255, 0.12);

        --cyan: #20e7ff;
        --blue: #3c7cff;
        --purple: #8c63ff;
        --green: #2ce69a;
        --amber: #ffbf47;
        --orange: #ff883d;
        --red: #ff496f;

        --text: #f4f7fc;
        --text-2: #9aa7bb;
        --text-3: #637087;
    }


    /* =====================================================
       APP
    ===================================================== */

    html,
    body,
    [data-testid="stAppViewContainer"],
    .stApp {
        background:
            radial-gradient(
                circle at 8% 0%,
                rgba(32, 231, 255, 0.08),
                transparent 24%
            ),
            radial-gradient(
                circle at 92% 10%,
                rgba(140, 99, 255, 0.09),
                transparent 25%
            ),
            radial-gradient(
                circle at 55% 100%,
                rgba(60, 124, 255, 0.055),
                transparent 30%
            ),
            #04070d !important;

        color: var(--text);
    }

    /* =====================================================
       REMOVE STREAMLIT TOP HEADER / TOOLBAR / DEPLOY BAR
    ===================================================== */

    header[data-testid="stHeader"],
    [data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stAppDeployButton"],
    .stDeployButton {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Remove any space Streamlit reserves above the app */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .stApp {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    [data-testid="stMainBlockContainer"],
    .block-container {
        max-width: 1500px;
        padding-top: 1rem !important;
        padding-bottom: 4rem !important;
        margin-top: 0 !important;
    }

    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }

    footer {
        display: none !important;
        visibility: hidden !important;
    }


    /* =====================================================
       SIDEBAR
    ===================================================== */

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                rgba(6, 11, 21, 0.985),
                rgba(3, 7, 14, 0.99)
            );

        border-right:
            1px solid rgba(255, 255, 255, 0.065);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        margin-top: 0 !important;
    }

    .sidebar-brand {
        padding: 18px 8px 19px 8px;
    }

    .brand-row {
        display: flex;
        align-items: center;
        gap: 11px;
    }

    .brand-mark {
        width: 38px;
        height: 38px;

        display: flex;
        align-items: center;
        justify-content: center;

        border-radius: 11px;

        background:
            linear-gradient(
                135deg,
                rgba(32, 231, 255, .18),
                rgba(60, 124, 255, .08)
            );

        border:
            1px solid rgba(32, 231, 255, .2);

        box-shadow:
            0 0 30px rgba(32, 231, 255, .06);

        font-size: 19px;
    }

    .sidebar-logo {
        font-size: 25px;
        font-weight: 900;
        letter-spacing: .07em;
        line-height: 1;
    }

    .sidebar-logo span {
        color: var(--cyan);
    }

    .sidebar-subtitle {
        margin-top: 9px;

        font-size: 9px;
        line-height: 1.7;

        color: #59677e;

        letter-spacing: .11em;
        text-transform: uppercase;
    }

    .sidebar-divider {
        height: 1px;
        background: rgba(255,255,255,.065);
        margin: 5px 0 17px 0;
    }


    /* Navigation */

    [data-testid="stSidebar"]
    div[role="radiogroup"] > label {

        background:
            rgba(255,255,255,0.018);

        padding:
            9px 11px;

        border-radius:
            9px;

        margin-bottom:
            2px;

        border:
            1px solid transparent;

        transition:
            all .18s ease;
    }

    [data-testid="stSidebar"]
    div[role="radiogroup"] > label:hover {

        background:
            rgba(32,231,255,.045);

        border-color:
            rgba(32,231,255,.08);
    }


    /* =====================================================
       HERO
    ===================================================== */

    .hero {
        position: relative;
        overflow: hidden;

        border:
            1px solid rgba(255,255,255,.075);

        border-radius:
            21px;

        padding:
            30px 34px;

        margin-bottom:
            25px;

        background:
            radial-gradient(
                circle at 90% 12%,
                rgba(32,231,255,.12),
                transparent 23%
            ),
            radial-gradient(
                circle at 72% 130%,
                rgba(140,99,255,.11),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                rgba(9,17,31,.97),
                rgba(5,10,19,.97)
            );

        box-shadow:
            0 18px 50px rgba(0,0,0,.22);
    }

    .hero:after {
        content: "";

        position: absolute;

        width: 290px;
        height: 290px;

        right: -95px;
        top: -105px;

        border-radius: 50%;

        border:
            1px solid rgba(32,231,255,.07);

        box-shadow:
            0 0 90px rgba(32,231,255,.05);
    }

    .hero-eyebrow {
        color: var(--cyan);

        font-size: 10px;
        font-weight: 900;

        letter-spacing: .18em;

        text-transform: uppercase;
    }

    .hero-title {
        font-size: 36px;
        font-weight: 900;

        margin-top: 7px;

        letter-spacing: -.035em;
    }

    .hero-description {
        max-width: 920px;

        margin-top: 10px;

        color: #8b98ad;

        font-size: 14px;

        line-height: 1.75;
    }


    /* =====================================================
       STATUS CHIPS
    ===================================================== */

    .status-row {
        display: flex;
        flex-wrap: wrap;

        gap: 8px;

        margin-top: 19px;
    }

    .chip {
        display: inline-flex;
        align-items: center;

        gap: 7px;

        padding:
            7px 11px;

        border-radius:
            100px;

        border:
            1px solid rgba(255,255,255,.075);

        background:
            rgba(255,255,255,.028);

        color:
            #a9b4c6;

        font-size:
            10px;

        font-weight:
            700;

        letter-spacing:
            .04em;
    }

    .dot {
        display: inline-block;

        height: 7px;
        width: 7px;

        border-radius: 50%;
    }

    .dot-green {
        background: var(--green);

        box-shadow:
            0 0 11px rgba(44,230,154,.75);
    }

    .dot-cyan {
        background: var(--cyan);

        box-shadow:
            0 0 11px rgba(32,231,255,.7);
    }

    .dot-amber {
        background: var(--amber);

        box-shadow:
            0 0 11px rgba(255,191,71,.55);
    }

    .dot-red {
        background: var(--red);

        box-shadow:
            0 0 11px rgba(255,73,111,.55);
    }


    /* =====================================================
       SECTION TITLES
    ===================================================== */

    .section-eyebrow {
        color: #647189;

        font-size: 9px;
        font-weight: 900;

        letter-spacing: .17em;

        text-transform: uppercase;

        margin-bottom: 4px;
    }

    .section-title {
        color: var(--text);

        font-size: 22px;
        font-weight: 850;

        letter-spacing: -.015em;

        margin-bottom: 16px;
    }


    /* =====================================================
       KPI CARDS
    ===================================================== */

    .kpi-card {
        position: relative;

        min-height: 128px;

        padding:
            19px 18px;

        border-radius:
            16px;

        border:
            1px solid rgba(255,255,255,.07);

        background:
            linear-gradient(
                145deg,
                rgba(12,21,36,.95),
                rgba(6,12,22,.92)
            );

        overflow: hidden;

        transition:
            all .22s ease;
    }

    .kpi-card:hover {
        transform:
            translateY(-2px);

        border-color:
            rgba(32,231,255,.20);

        box-shadow:
            0 15px 35px rgba(0,0,0,.18);
    }

    .kpi-card:after {
        content: "";

        position: absolute;

        width: 85px;
        height: 85px;

        right: -42px;
        top: -42px;

        border-radius: 50%;

        background:
            rgba(32,231,255,.035);
    }

    .kpi-label {
        font-size: 9px;

        color: #69768b;

        font-weight: 850;

        letter-spacing: .11em;

        text-transform: uppercase;
    }

    .kpi-value {
        margin-top: 9px;

        font-size: 30px;

        font-weight: 900;

        line-height: 1.1;
    }

    .kpi-meta {
        margin-top: 8px;

        font-size: 10px;

        color: #59667b;
    }

    .kpi-cyan {
        color: var(--cyan);
    }

    .kpi-positive {
        color: var(--green);
    }

    .kpi-warning {
        color: var(--amber);
    }

    .kpi-danger {
        color: var(--red);
    }


    /* =====================================================
       GENERIC PANEL
    ===================================================== */

    .panel {
        padding: 19px;

        border-radius: 15px;

        border:
            1px solid rgba(255,255,255,.07);

        background:
            rgba(9,16,28,.82);

        margin-bottom: 15px;
    }

    .panel-title {
        color: #eef3fa;

        font-size: 13px;

        font-weight: 850;

        margin-bottom: 7px;
    }

    .panel-sub {
        color: #6e7b91;

        font-size: 11px;

        line-height: 1.65;
    }


    /* =====================================================
       ALERT CARD
    ===================================================== */

    .alert-card {
        padding:
            16px 17px;

        border-radius:
            14px;

        margin-bottom:
            9px;

        border:
            1px solid rgba(255,255,255,.068);

        background:
            linear-gradient(
                135deg,
                rgba(11,19,32,.92),
                rgba(6,12,22,.92)
            );

        transition:
            all .2s ease;
    }

    .alert-card:hover {
        border-color:
            rgba(32,231,255,.17);

        transform:
            translateX(2px);
    }

    .alert-head {
        display: flex;

        justify-content:
            space-between;

        align-items:
            center;

        gap: 12px;
    }

    .alert-title {
        color: #f2f5f9;

        font-size: 13px;

        font-weight: 800;
    }

    .alert-meta {
        margin-top: 6px;

        color: #647188;

        font-size: 10px;

        line-height: 1.6;
    }


    /* =====================================================
       SEVERITY
    ===================================================== */

    .severity {
        display: inline-block;

        flex-shrink: 0;

        padding:
            4px 8px;

        border-radius:
            6px;

        font-size:
            9px;

        font-weight:
            900;

        letter-spacing:
            .05em;

        text-transform:
            uppercase;
    }

    .sev-critical {
        color: #ff718e;

        background:
            rgba(255,73,111,.12);

        border:
            1px solid rgba(255,73,111,.25);
    }

    .sev-high {
        color: #ff9a62;

        background:
            rgba(255,136,61,.12);

        border:
            1px solid rgba(255,136,61,.22);
    }

    .sev-medium {
        color: #ffcb65;

        background:
            rgba(255,191,71,.12);

        border:
            1px solid rgba(255,191,71,.22);
    }

    .sev-low {
        color: #56e9a7;

        background:
            rgba(44,230,154,.10);

        border:
            1px solid rgba(44,230,154,.20);
    }


    /* =====================================================
       AGENTS
    ===================================================== */

    .agent-card {
        min-height: 150px;

        padding:
            17px;

        border-radius:
            14px;

        border:
            1px solid rgba(255,255,255,.065);

        background:
            linear-gradient(
                145deg,
                rgba(10,18,31,.95),
                rgba(5,11,20,.94)
            );
    }

    .agent-card-active {
        border-color:
            rgba(32,231,255,.30);

        box-shadow:
            inset 0 0 25px rgba(32,231,255,.025),
            0 0 24px rgba(32,231,255,.025);
    }

    .agent-icon {
        width: 28px;
        height: 28px;

        display: flex;
        align-items: center;
        justify-content: center;

        border-radius: 8px;

        background:
            rgba(32,231,255,.07);

        border:
            1px solid rgba(32,231,255,.12);

        margin-bottom: 12px;
    }

    .agent-name {
        font-size: 12px;

        font-weight: 850;

        color: #f0f4fb;
    }

    .agent-role {
        margin-top: 6px;

        color: #68758a;

        font-size: 10px;

        line-height: 1.55;
    }

    .agent-state {
        margin-top: 12px;

        color: var(--cyan);

        font-size: 9px;

        font-weight: 900;

        letter-spacing: .08em;
    }


    /* =====================================================
       PIPELINE
    ===================================================== */

    .pipeline {
        display: flex;

        flex-wrap: wrap;

        align-items: center;

        gap: 7px;

        margin:
            10px 0 23px 0;
    }

    .pipeline-node {
        padding:
            8px 10px;

        border-radius:
            9px;

        color:
            #a9f3fb;

        background:
            rgba(32,231,255,.045);

        border:
            1px solid rgba(32,231,255,.15);

        font-size:
            9px;

        font-weight:
            850;

        letter-spacing:
            .035em;
    }

    .pipeline-arrow {
        color: #36455a;

        font-size: 12px;
    }


    /* =====================================================
       RISK
    ===================================================== */

    .risk-score {
        text-align: center;

        padding:
            28px 14px;

        border-radius:
            17px;

        border:
            1px solid rgba(255,73,111,.20);

        background:
            radial-gradient(
                circle,
                rgba(255,73,111,.10),
                rgba(8,14,24,.80) 65%
            );
    }

    .risk-number {
        color: #ff5e7d;

        font-size: 56px;

        font-weight: 950;

        line-height: 1;
    }

    .risk-label {
        color: #7a879b;

        margin-top: 9px;

        font-size: 9px;

        font-weight: 800;

        letter-spacing: .13em;

        text-transform: uppercase;
    }


    /* =====================================================
       GOVERNANCE
    ===================================================== */

    .gov-card {
        min-height: 145px;

        padding:
            17px;

        border-radius:
            14px;

        border:
            1px solid rgba(140,99,255,.14);

        background:
            linear-gradient(
                145deg,
                rgba(140,99,255,.05),
                rgba(7,13,23,.90)
            );
    }

    .gov-title {
        color: #c4b5ff;

        font-size: 11px;

        font-weight: 900;

        letter-spacing: .05em;
    }

    .gov-text {
        margin-top: 8px;

        color: #6d7a8f;

        font-size: 10px;

        line-height: 1.65;
    }


    /* =====================================================
       SYSTEM STATUS
    ===================================================== */

    .system-card {
        min-height: 105px;

        padding: 16px;

        border-radius: 13px;

        border:
            1px solid rgba(255,255,255,.065);

        background:
            rgba(9,16,28,.80);
    }

    .system-title {
        color: #edf2f9;

        font-size: 11px;

        font-weight: 850;
    }

    .system-status {
        margin-top: 9px;

        font-size: 9px;

        font-weight: 850;

        letter-spacing: .055em;
    }

    .status-green {
        color: var(--green);
    }

    .status-cyan {
        color: var(--cyan);
    }

    .status-amber {
        color: var(--amber);
    }

    .status-red {
        color: var(--red);
    }


    /* =====================================================
       TIMELINE
    ===================================================== */

    .timeline-event {
        position: relative;

        padding:
            3px 0 19px 19px;

        border-left:
            2px solid rgba(32,231,255,.20);
    }

    .timeline-event:before {
        content: "";

        position: absolute;

        left: -6px;

        top: 6px;

        width: 10px;
        height: 10px;

        border-radius: 50%;

        background:
            var(--cyan);

        box-shadow:
            0 0 12px rgba(32,231,255,.52);
    }

    .timeline-title {
        color: #edf2f9;

        font-size: 12px;

        font-weight: 800;
    }

    .timeline-meta {
        margin-top: 4px;

        color: #5f6d83;

        font-size: 9px;
    }


    /* =====================================================
       STREAMLIT WIDGETS
    ===================================================== */

    div[data-testid="stMetric"] {
        padding:
            15px;

        border-radius:
            13px;

        border:
            1px solid rgba(255,255,255,.065);

        background:
            rgba(8,15,26,.75);
    }

    div[data-testid="stMetricLabel"] {
        color: #7e8ba0;
    }

    div[data-testid="stMetricValue"] {
        color: #f3f6fb;
    }

    .stButton > button {
        min-height: 40px;

        border-radius:
            9px !important;

        border:
            1px solid rgba(32,231,255,.23) !important;

        background:
            linear-gradient(
                135deg,
                rgba(32,231,255,.105),
                rgba(60,124,255,.07)
            ) !important;

        color:
            #d9fbff !important;

        font-weight:
            800 !important;

        transition:
            all .18s ease;
    }

    .stButton > button:hover {
        border-color:
            rgba(32,231,255,.55) !important;

        transform:
            translateY(-1px);

        box-shadow:
            0 0 20px rgba(32,231,255,.06) !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div {

        background-color:
            rgba(8,15,26,.93) !important;

        border-color:
            rgba(255,255,255,.08) !important;

        color:
            #f1f5fa !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        padding-left:
            13px;

        padding-right:
            13px;

        border-radius:
            8px;

        background:
            rgba(255,255,255,.018);

        color:
            #7f8ca1;
    }

    .stTabs [aria-selected="true"] {
        color:
            var(--cyan) !important;

        background:
            rgba(32,231,255,.055) !important;
    }

    [data-testid="stDataFrame"] {
        border:
            1px solid rgba(255,255,255,.055);

        border-radius:
            12px;

        overflow:
            hidden;
    }

    hr {
        border-color:
            rgba(255,255,255,.055);
    }



    /* =====================================================
       COMPACT PAGE HEADER
    ===================================================== */

    .compact-status-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        flex-wrap: wrap;

        padding: 14px 17px;
        margin-bottom: 25px;

        border-radius: 14px;

        border:
            1px solid rgba(255,255,255,.065);

        background:
            linear-gradient(
                135deg,
                rgba(8,16,28,.95),
                rgba(5,10,19,.93)
            );
    }

    .compact-page-name {
        color: #f2f5fa;
        font-size: 12px;
        font-weight: 850;
        letter-spacing: .04em;
    }

    .compact-page-name span {
        color: var(--cyan);
    }

    .compact-status-right {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }


    /* =====================================================
       RESPONSIVE AGENT GRID
    ===================================================== */

    .agent-grid {
        display: grid;
        grid-template-columns:
            repeat(5, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 19px;
    }

    @media (max-width: 1200px) {

        .agent-grid {
            grid-template-columns:
                repeat(3, minmax(0, 1fr));
        }
    }

    @media (max-width: 850px) {

        .agent-grid {
            grid-template-columns:
                repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 580px) {

        .agent-grid {
            grid-template-columns:
                1fr;
        }
    }


    /* =====================================================
       HUMAN REVIEW STAT CARDS
    ===================================================== */

    .review-stat {
        padding: 17px;
        margin-bottom: 12px;

        border-radius: 14px;

        border:
            1px solid rgba(255,255,255,.065);

        background:
            rgba(8,15,26,.82);
    }

    .review-stat-label {
        color: #78869b;
        font-size: 9px;
        font-weight: 850;
        letter-spacing: .08em;
        text-transform: uppercase;
    }

    .review-stat-value {
        margin-top: 9px;
        color: #f2f5fa;
        font-size: 23px;
        font-weight: 850;
        line-height: 1.2;
        word-break: normal;
    }

    .review-stat-value.amber {
        color: var(--amber);
    }

    .review-stat-value.green {
        color: var(--green);
    }

    .review-stat-value.red {
        color: var(--red);
    }

    .review-stat-value.cyan {
        color: var(--cyan);
    }


    /* =====================================================
       FOOTER
    ===================================================== */

    .aegis-footer {
        margin-top: 48px;

        padding-top: 18px;

        border-top:
            1px solid rgba(255,255,255,.045);

        color: #445166;

        text-align: center;

        font-size: 8px;

        letter-spacing: .13em;

        text-transform: uppercase;
    }

    </style>
    """
)


# =========================================================
# COLORS
# =========================================================

CYAN = "#20e7ff"
BLUE = "#3c7cff"
PURPLE = "#8c63ff"
GREEN = "#2ce69a"
AMBER = "#ffbf47"
RED = "#ff496f"
ORANGE = "#ff883d"

GRID = "rgba(255,255,255,0.05)"
TEXT_SECONDARY = "#76849a"
TRANSPARENT = "rgba(0,0,0,0)"



# =========================================================
# AEGIS SOC | SINGLE-FILE LIVE OPERATIONS LAYER
# Retains the original design system and all ten navigation areas.
# Python backend services and database stay separate by design.
# =========================================================

from collections import Counter
from pathlib import Path
from datetime import timezone
import os
import sys
import subprocess
import requests

ROOT = Path(__file__).resolve().parents[1]
API_DEFAULT = os.getenv("AEGIS_API_URL", "http://localhost:8000").rstrip("/")
N8N_DEFAULT = os.getenv("AEGIS_N8N_WEBHOOK_URL", "").strip()
OLLAMA_DEFAULT = os.getenv("AEGIS_OLLAMA_URL", "http://localhost:11434").rstrip("/")

for key, default in {
    "aegis_api_url": API_DEFAULT,
    "aegis_n8n_url": N8N_DEFAULT,
    "aegis_ollama_url": OLLAMA_DEFAULT,
    "aegis_analyst": "demo-analyst",
    "aegis_last_result": {},
    "aegis_last_error": "",
    "aegis_selected_alert": "ALT-2404",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

ui_html('''
<style>
.aegis-tag {display:inline-flex; align-items:center; padding:5px 12px;
  border:1px solid rgba(32,231,255,.18); border-radius:999px;
  background:rgba(32,231,255,.06); color:#9af6ff; font-size:11px;
  letter-spacing:.1em; font-weight:750; margin:4px 5px 4px 0}
.aegis-subtle {color:#879ab6; font-size:12px; line-height:1.65}
.aegis-spotlight {padding:20px 25px; border-radius:17px;
  border:1px solid rgba(32,231,255,.2); background:linear-gradient(120deg,
  rgba(32,231,255,.075),rgba(140,99,255,.06) 60%,rgba(4,7,13,.15)); margin:12px 0 20px}
.aegis-title {font-size:26px; font-weight:850; color:#ebf7ff; letter-spacing:-.028em}
.aegis-label {font-size:10px; letter-spacing:.18em; font-weight:800; color:#20e7ff; margin-bottom:7px}
.aegis-footnote {color:#637087;font-size:11px;letter-spacing:.04em}
[data-testid="stDataFrame"] {border:1px solid rgba(255,255,255,.09); border-radius:12px}
</style>
''')


def api_url() -> str:
    return str(st.session_state.aegis_api_url).strip().rstrip("/")


def _request(method: str, url: str, *, timeout=15, **kwargs):
    """Parse a real JSON response or raise a human-readable error."""
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        if not response.content:
            raise RuntimeError("Service returned an empty response body")
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Service returned JSON that was not an object")
        return payload
    except requests.exceptions.RequestException as exc:
        details = ""
        if getattr(exc, "response", None) is not None:
            details = ": " + exc.response.text[:350]
        raise RuntimeError(f"{str(exc)}{details}") from exc
    except ValueError as exc:
        raise RuntimeError(f"Invalid JSON returned from {url}") from exc


@st.cache_data(ttl=5, show_spinner=False)
def dashboard_get(base: str, path: str, params=None):
    return _request("GET", f"{base}/dashboard/{path.lstrip('/')}",
                    timeout=(3, 15), params=params or {})


def dashboard_post(path: str, payload: dict):
    answer = _request("POST", f"{api_url()}/dashboard/{path.lstrip('/')}",
                      json=payload, timeout=(4, 40))
    dashboard_get.clear()
    return answer


@st.cache_data(ttl=10, show_spinner=False)
def check_status(url: str, *, json_required=True):
    try:
        response = requests.get(url, timeout=(2, 5))
        response.raise_for_status()
        return {"online": True, "data": response.json() if json_required else None,
                "status_code": response.status_code}
    except (requests.RequestException, ValueError) as exc:
        return {"online": False, "error": str(exc), "data": None}


def feed(path: str, limit: int = 250) -> list:
    try:
        result = dashboard_get(api_url(), path, {"limit": limit})
        rows = result.get("items", [])
        return rows if isinstance(rows, list) else []
    except RuntimeError:
        return []


def clean_number(value, default=0):
    try:
        return float(value if value is not None else default)
    except (ValueError, TypeError):
        return float(default)


def cell_text(value, limit=800):
    if value is None or value == "":
        return "Not recorded"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)[:limit]
    return str(value)[:limit]


def parse_json(value):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            pass
    return value


def extract(record: dict, *keys, default=None):
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return default


def normalize_alert(row: dict) -> dict:
    """Support either synthetic alert JSON format without inventing evidence."""
    return {
        "Alert ID": cell_text(extract(row, "alert_id", "Alert ID", "id", default="UNKNOWN")),
        "Title": cell_text(extract(row, "title", "Title", "alert_name", "rule_name", default="Security Alert")),
        "Severity": cell_text(extract(row, "severity", "Severity", default="Unknown")),
        "Source": cell_text(extract(row, "source", "Source", "detection_source", default="Synthetic dataset")),
        "Asset": cell_text(extract(row, "asset_id", "asset", "Asset", "hostname", default="—")),
        "User": cell_text(extract(row, "user", "user_id", "User", "username", default="—")),
        "IP": cell_text(extract(row, "ip", "IP", "source_ip", "destination_ip", default="—")),
        "Status": cell_text(extract(row, "status", "Status", default="Ready")),
        "Confidence": extract(row, "detection_confidence", "confidence", "Confidence", default=None),
        "Time": cell_text(extract(row, "timestamp", "time", "Time", default="—")),
        "MITRE": cell_text(extract(row, "mitre_technique", "mitre", "MITRE", default="—")),
        "raw": row,
    }


def show_rows(rows: list, empty="No real records were returned.", *, columns=None):
    if not rows:
        st.info(empty)
        return
    dataset = [dict(r) for r in rows if isinstance(r, dict)]
    if not dataset:
        st.info(empty)
        return
    frame = pd.DataFrame(dataset)
    if columns:
        frame = frame[[col for col in columns if col in frame.columns]]
    for key in frame.columns:
        frame[key] = frame[key].map(lambda v: json.dumps(v, ensure_ascii=False)
                                    if isinstance(v, (dict, list)) else v)
    st.dataframe(frame, use_container_width=True, hide_index=True)


def heading(eyebrow, title, subtitle=""):
    ui_html(f'''
    <div class="aegis-label">{escape(eyebrow.upper())}</div>
    <div class="aegis-title">{escape(title)}</div>
    <div class="aegis-subtle" style="margin-bottom:16px">{escape(subtitle)}</div>
    ''')


def status_tag(label, online):
    color = "#2ce69a" if online else "#ffbf47"
    ui_html(f'<span class="aegis-tag" style="border-color:{color}55;color:{color}">'
            f'{"●" if online else "○"} {escape(label)}'
            '</span>')


def summary_card(label, number, note="", color=""):
    ui_html(f'''
       <div class="kpi-card"><div class="kpi-label">{escape(str(label))}</div>
       <div class="kpi-value {escape(color)}">{escape(str(number))}</div>
       <div class="kpi-meta">{escape(str(note))}</div></div>''')


def alert_card(alert):
    sev = str(alert.get("Severity", "Unknown"))
    sev_css = {"Critical":"sev-critical", "High":"sev-high",
               "Medium":"sev-medium", "Low":"sev-low"}.get(sev, "sev-low")
    ui_html(f'''
    <div class="alert-card"><div class="alert-head">
    <div class="alert-title">{escape(str(alert.get('Title', 'Security Alert')))}</div>
    <span class="severity {sev_css}">{escape(sev)}</span></div>
    <div class="alert-meta">{escape(str(alert.get('Alert ID','—')))} &nbsp; • &nbsp;
    {escape(str(alert.get('Source','—')))} &nbsp; • &nbsp;
    {escape(str(alert.get('Asset','—')))} &nbsp; • &nbsp;
    {escape(str(alert.get('Status','Ready')))}</div></div>
    ''')


def investigation_for_alert(alert_id: str, investigations: list, cases: list) -> list:
    case_ids = {r.get('case_id') for r in cases if r.get('alert_id') == alert_id}
    return [r for r in investigations if r.get('case_id') in case_ids or
            r.get('alert_id') == alert_id]


def by_case_latest(investigations: list) -> dict:
    """Use backend result order, most recent first. Do not assume date columns."""
    latest = {}
    for record in investigations:
        key = record.get('case_id')
        if key and key not in latest:
            latest[key] = record
    return latest


def invalidate():
    dashboard_get.clear()
    check_status.clear()


def run_investigation(alert_id: str, via_n8n: bool):
    if via_n8n:
        target = st.session_state.aegis_n8n_url.strip()
        if not target:
            raise RuntimeError(
                "Set the actual n8n production webhook URL in the sidebar. "
                "The test webhook URL works only while a test listener is active."
            )
    else:
        target = f"{api_url()}/investigate"
    result = _request("POST", target, json={"alert_id": alert_id},
                      timeout=(5, 360))
    if result.get('status') != 'success':
        raise RuntimeError(f"Investigation did not succeed: {cell_text(result)}")
    if result.get('alert_id') != alert_id:
        raise RuntimeError('Returned investigation belongs to a different alert')
    st.session_state.aegis_last_result = result
    st.session_state.aegis_selected_alert = alert_id
    st.session_state.aegis_last_error = ""
    invalidate()
    return result


def render_live_result(record: dict, *, historical=False):
    if not record:
        st.info("No investigation selected.")
        return
    confidence = extract(record, 'confidence', 'model_confidence', default=None)
    risk = extract(record, 'risk_score', 'overall_risk_score', default=None)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Classification', cell_text(record.get('classification')))
    col2.metric('Risk score', f"{risk}/100" if risk is not None else 'Not recorded')
    col3.metric('Control mode', cell_text(record.get('control_mode')))
    col4.metric('Confidence', f"{confidence}%" if confidence is not None else 'Not recorded')
    st.markdown(f"**Case:** `{cell_text(record.get('case_id'))}` · "
                f"**Investigation:** `{cell_text(record.get('investigation_id'))}`")
    if record.get('policy_rationale'):
        st.info(str(record['policy_rationale']))
    if record.get('executive_summary'):
        st.markdown('#### Executive summary')
        st.write(record['executive_summary'])
    if record.get('recommended_actions'):
        st.markdown('#### Recommended actions')
        for idx, item in enumerate(record['recommended_actions'],1):
            st.write(f"{idx}. {item}")
    if record.get('model_metadata'):
        with st.expander('Real model inference metadata', expanded=False):
            st.json(record['model_metadata'])
    if historical:
        with st.expander('Persisted investigation record', expanded=False):
            st.json({key:parse_json(val) for key,val in record.items()})


def render_real_agents(inv_id):
    if not inv_id:
        return
    try:
        agents = dashboard_get(api_url(),
                               f"investigations/{inv_id}/agent-outputs").get('items', [])
    except RuntimeError as exc:
        st.warning(f"Agent evidence unavailable: {exc}")
        return
    if not agents:
        st.info('No persisted agent outputs found for this investigation.')
        return
    st.caption(f'{len(agents)} persisted agent outputs from this investigation.')
    for record in agents:
        name = extract(record,'agent_name','agent','name',default='Agent')
        with st.expander(str(name),expanded=False):
            for key,value in record.items():
                if key in ('output_json','output','result_json'):
                    st.json(parse_json(value))
                elif key not in ('agent_name',):
                    st.caption(f'{key}: {cell_text(value)}')


def sidebar_and_header():
    with st.sidebar:
        ui_html('''
        <div class="sidebar-brand"><div class="brand-row"><div class="brand-mark">🛡</div>
        <div><div class="sidebar-logo">AEGIS<span>.</span></div></div></div>
        <div class="sidebar-subtitle">Autonomous Evidence &amp; Governance Intelligence System</div>
        </div><div class="sidebar-divider"></div>
        ''')
        sections = ["Command Center", "Alert Intake", "Investigation", "Evidence & Context",
                    "Human Review", "Escalation Center", "Model Lab", "Governance",
                    "Audit Trail", "System Status"]
        page = st.radio('AEGIS Navigation', sections, label_visibility='collapsed', key='aegis_page')
        st.divider()
        with st.expander('⚙ Runtime connection settings', expanded=False):
            st.text_input('AEGIS FastAPI', key='aegis_api_url')
            st.text_input('Ollama HTTP API', key='aegis_ollama_url')
            st.text_input('n8n webhook URL', key='aegis_n8n_url',
                          help='Use the published /webhook/aegis-triage URL, not /webhook-test, '
                               'unless actively testing.')
            st.text_input('Analyst ID', key='aegis_analyst')
        if st.button('↻ Refresh live data', use_container_width=True, key='refresh_all'):
            invalidate(); st.rerun()
        st.caption('Local prototype · Synthetic SOC alerts · No banking actions')
    return page


def render_banner(page, api_alive, dashboard_alive, ollama_alive, n8n_alive):
    ui_html(f'''
    <div class="aegis-spotlight">
        <div class="aegis-label">GOVERNED AGENTIC SECURITY OPERATIONS · LOCAL PROTOTYPE</div>
        <div class="aegis-title">{escape('AEGIS SOC Intelligence Platform' if page=='Command Center' else page)}</div>
        <div class="aegis-subtle" style="margin-top:8px">
            Real persisted investigations · Deterministic governance · Human approvals · Auditable outcomes
        </div>
    </div>''')
    cols = st.columns(4)
    for col, label, up in zip(cols,
        ['FastAPI', 'Dashboard API / SQLite', 'Ollama LLM', 'n8n'],
        [api_alive, dashboard_alive, ollama_alive, n8n_alive]):
        with col: status_tag(label, up)
    if not dashboard_alive:
        st.warning('Live dashboard endpoints are unavailable. Start the additive FastAPI '
                   'entrypoint `api.dashboard_api:app` on port 8000. '
                   'This dashboard deliberately does not show fabricated SOC metrics.')


# ---------------------------------------------------------
# Live source refresh (cached for a few seconds)
# ---------------------------------------------------------
page = sidebar_and_header()
api_health = check_status(f"{api_url()}/health")
ollama_health = check_status(f"{st.session_state.aegis_ollama_url.rstrip('/')}/api/tags")
n8n_health = check_status('http://localhost:5678', json_required=False)
try:
    overview = dashboard_get(api_url(), 'overview') if api_health['online'] else {}
    dash_online = bool(overview)
    raw_alerts = dashboard_get(api_url(), 'alerts').get('items', []) if dash_online else []
    raw_cases = dashboard_get(api_url(), 'cases', {'limit':1000}).get('items', []) if dash_online else []
    raw_investigations = dashboard_get(api_url(), 'investigations',
                                       {'limit':1000}).get('items', []) if dash_online else []
except RuntimeError as exc:
    dash_online = False
    dashboard_error = str(exc)
    overview, raw_alerts, raw_cases, raw_investigations = {}, [], [], []

alerts = [normalize_alert(item) for item in raw_alerts if isinstance(item, dict)]
case_map = {row.get('alert_id'):row for row in raw_cases if row.get('alert_id')}
latest = by_case_latest(raw_investigations)
for alert in alerts:
    case = case_map.get(alert['Alert ID'])
    if case:
        inv = latest.get(case.get('case_id'),{})
        alert['Status'] = (str(inv.get('control_mode')) if inv
                           else str(case.get('status','Ready')))
        if alert['Confidence'] is None and inv.get('confidence') is not None:
            alert['Confidence'] = inv['confidence']

render_banner(page, api_health['online'], dash_online, ollama_health['online'],
              n8n_health['online'])
if not dash_online and api_health['online']:
    st.caption('Backend response: ' + str(globals().get('dashboard_error','unknown error'))[:500])


# =========================================================
# 01 COMMAND CENTER: REAL PERSISTED STATISTICS
# =========================================================
if page == 'Command Center':
    heading('Operational intelligence', 'SOC Command Center',
            'Measured from the AEGIS synthetic alert catalog and persisted SQLite investigations.')
    if dash_online:
        pending_count = overview.get('pending_reviews',0)
        total_cases = overview.get('database',{}).get('cases',len(raw_cases))
        current_modes = [record.get('control_mode','') for record in latest.values()]
        autonomous_count = current_modes.count('[A] Autonomous')
        critical_count = sum(a['Severity'].casefold()=='critical' for a in alerts)
        with st.container():
            cols=st.columns(5)
            for col,args in zip(cols,[
                ('Catalogued alerts',len(alerts),'Synthetic alert fixtures','kpi-cyan'),
                ('Critical alerts',critical_count,'From current alert catalog','kpi-danger'),
                ('Investigations',overview.get('database',{}).get('investigations',0),
                 'Stored execution records','kpi-cyan'),
                ('Autonomous cases',autonomous_count,'Latest decision per case','kpi-positive'),
                ('Pending HITL',pending_count,'Requires analyst decision','kpi-warning')]):
                with col:summary_card(*args)
        st.write('')
        a,b=st.columns([1.1,1])
        with a:
            heading('Detection distribution', 'Alert severity')
            counts=Counter(alert['Severity'] for alert in alerts)
            if counts:
                fig=go.Figure(go.Pie(labels=list(counts),values=list(counts.values()),
                                     hole=.66,marker={'colors':[RED,AMBER,CYAN,BLUE]}))
                fig.update_layout(height=310,margin=dict(l=10,r=10,t=10,b=10),
                                  showlegend=True,paper_bgcolor='rgba(0,0,0,0)',
                                  font={'color':'#b8cbe1'})
                st.plotly_chart(fig,use_container_width=True)
        with b:
            heading('Policy outcomes','Governance decisions')
            modes=Counter(current_modes)
            if modes:
                fig=go.Figure(go.Bar(x=list(modes.values()),y=list(modes),orientation='h',
                                   marker_color=[CYAN if '[A]' in k else AMBER if '[H]' in k
                                                 else RED for k in modes]))
                fig.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),
                                  paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                                  font={'color':'#b8cbe1'})
                st.plotly_chart(fig,use_container_width=True)
            else:st.info('No completed investigations yet.')
        a,b=st.columns([1.1,1])
        with a:
            heading('Priority queue','Current synthetic security alerts')
            priority={'Critical':4,'High':3,'Medium':2,'Low':1}
            for alert in sorted(alerts,key=lambda a:priority.get(a['Severity'],0),
                                reverse=True)[:5]:alert_card(alert)
        with b:
            heading('Latest persisted cases','Investigation history')
            show_rows(raw_investigations[:10],'No investigations stored yet.',
                      columns=['investigation_id','case_id','classification',
                               'overall_risk_score','control_mode','status'])
        st.caption('Counts and charts come from the local dataset and SQLite. '
                   'They are not production SOC telemetry.')
    else:
        st.info('Waiting for the live AEGIS dashboard service; no simulated metrics are shown.')


# =========================================================
# 02 ALERT INTAKE: REAL FIXTURE CATALOG + INVESTIGATION
# =========================================================
elif page == 'Alert Intake':
    heading('Case intake','Security Alert Gateway',
            'Select an existing synthetic security alert and launch a real governed investigation.')
    if not alerts:st.info('No alerts returned by /dashboard/alerts.')
    else:
        names={f"{a['Alert ID']} · {a['Title']}":a for a in alerts}
        chosen=names[st.selectbox('Choose catalogued alert',list(names),key='intake_alert')]
        alert_card(chosen)
        with st.expander('Original synthetic alert payload',expanded=False):
            st.json(chosen['raw'])
        dispatch=st.radio('Execution path',['FastAPI: direct governed investigation',
                      'n8n: webhook orchestration'],horizontal=True,key='intake_path')
        if st.button('▶ Investigate selected alert',type='primary',
                     use_container_width=True,key='intake_start'):
            try:
                with st.spinner('Running live agent correlation, intelligence, risk and summary...'):
                    result=run_investigation(chosen['Alert ID'],via_n8n=dispatch.startswith('n8n'))
                st.success('AI investigation completed and persisted.')
                render_live_result(result)
            except RuntimeError as exc:st.error(str(exc))
        heading('Synthetic fixtures','Complete incoming alert catalog')
        show_rows([{k:v for k,v in a.items() if k!='raw'} for a in alerts],
                  'No catalogued alerts')
        st.caption('Custom arbitrary alert creation is not enabled in the current '
                   'backend schema. This screen investigates the actual fixtures accepted '
                   'by AEGIS instead of pretending new alerts were persisted.')


# =========================================================
# 03 INVESTIGATION: REAL AI OUTPUT + HISTORY
# =========================================================
elif page == 'Investigation':
    heading('Agentic workspace','Live Incident Investigation',
            'Real Qwen inference, deterministic routing, and persisted agent evidence.')
    if alerts:
        ids=[a['Alert ID'] for a in alerts]
        if st.session_state.aegis_selected_alert not in ids:
            st.session_state.aegis_selected_alert=ids[0]
        chosen_id=st.selectbox('Investigation alert ID',ids,
                               index=ids.index(st.session_state.aegis_selected_alert),
                               key='investigation_selector')
        st.session_state.aegis_selected_alert=chosen_id
        alert_card(next(a for a in alerts if a['Alert ID']==chosen_id))
        via_n8n=st.checkbox('Route through n8n webhook (requires active URL)',
                            value=False,key='inv_via_n8n')
        btn,reload=st.columns([3,1])
        with btn:execute=st.button('▶ Run Governed Agentic Investigation',type='primary',
                                    use_container_width=True,key='run_ai')
        with reload:refresh=st.button('↻ Refresh',use_container_width=True,key='recheck_ai')
        if refresh:invalidate();st.rerun()
        if execute:
            try:
                with st.spinner('AEGIS multi-agent runtime and local LLM are investigating...'):
                    result=run_investigation(chosen_id,via_n8n)
                st.success('Complete. Governance decision returned by the Python policy engine.')
            except RuntimeError as exc:
                st.session_state.aegis_last_error=str(exc)
                st.error(str(exc))
        cached=st.session_state.aegis_last_result
        historical=investigation_for_alert(chosen_id,raw_investigations,raw_cases)
        if cached.get('alert_id')==chosen_id:
            heading('Investigation decision','Latest live result')
            render_live_result(cached)
            render_real_agents(cached.get('investigation_id'))
        if historical:
            heading('Durable evidence','Stored investigation history')
            choices={f"{x.get('investigation_id','—')} | {x.get('control_mode','—')}"
                     :x for x in historical}
            select=choices[st.selectbox('Choose persisted investigation',list(choices),
                                       key='saved_investigation')]
            render_live_result(select,historical=True)
            render_real_agents(select.get('investigation_id'))
        elif not cached or cached.get('alert_id')!=chosen_id:
            st.info('No investigation for this case yet. Run AEGIS above.')
    else:st.info('No synthetic alerts loaded.')


# =========================================================
# 04 EVIDENCE: REAL AGENT OUTPUTS + RAW ALERT
# =========================================================
elif page == 'Evidence & Context':
    heading('Evidence plane','Investigation Evidence & Context',
            'Agent evidence comes from the SQLite agent_outputs table via FastAPI.')
    if not raw_investigations:st.info('No agent evidence yet. Run an investigation first.')
    else:
        candidates={str(x.get('investigation_id')):x for x in raw_investigations
                    if x.get('investigation_id')}
        chosen_id=st.selectbox('Investigation',list(candidates),key='evidence_inv')
        row=candidates[chosen_id]
        a,b=st.tabs(['Persisted agent reasoning outputs','Synthetic source alert'])
        with a:render_real_agents(chosen_id)
        with b:
            case=next((c for c in raw_cases if c.get('case_id')==row.get('case_id')), {})
            corresponding=next((a for a in alerts if a['Alert ID']==case.get('alert_id')),None)
            if corresponding:st.json(corresponding['raw'])
            else:st.info('No matching source fixture found.')
        st.caption('These are synthetic incident signals and persisted agent findings; '
                   'no unobserved telemetry or fabricated evidence is added.')


# =========================================================
# 05 HUMAN REVIEW: PERSISTED SOC ANALYST DECISIONS
# =========================================================
elif page == 'Human Review':
    heading('Human-in-the-Loop','SOC Analyst Decision Gateway',
            'Only the latest [H] HITL cases may receive a final analyst decision.')
    pending=feed('queues/human-review') if dash_online else []
    a,b,c=st.columns(3)
    with a:summary_card('Awaiting review',len(pending),'Live pending investigations','kpi-warning')
    with b:summary_card('Approved/rejected',len(feed('reviews')),
                        'Persisted analyst actions','kpi-cyan')
    with c:summary_card('Policy', '[H] HITL','Deterministic human-control gate','kpi-positive')
    heading('Review queue','Cases requiring analyst attention')
    show_rows(pending,'No pending human reviews.')
    if pending:
        options={f"{r.get('alert_id')} · {r.get('investigation_id')}":r for r in pending}
        chosen=options[st.selectbox('Select case to review',list(options),key='pending_case')]
        with st.form('decision_form'):
            actor=st.text_input('Authorized analyst ID',value=st.session_state.aegis_analyst)
            decision=st.radio('Decision',['approve','reject','request_more_evidence'],
                              horizontal=True)
            rationale=st.text_area('Analyst rationale (mandatory)',height=125,
                                   placeholder='Evidence reviewed and justification...')
            saved=st.form_submit_button('Record human decision',type='primary',
                                       use_container_width=True)
        if saved:
            try:
                answer=dashboard_post('reviews',{'case_id':chosen['case_id'],
                    'investigation_id':chosen['investigation_id'],
                    'analyst_id':actor.strip(),'decision':decision,
                    'rationale':rationale.strip()})
                st.success(f"Analyst decision persisted: {answer.get('action_id')}")
                st.rerun()
            except RuntimeError as exc:st.error(str(exc))
    heading('Analyst action history','Persisted decisions')
    show_rows(feed('reviews'),'No analyst decisions recorded yet.')
    st.caption('Approval is an auditable decision only. AEGIS does NOT autonomously '
               'block accounts, transfer money, modify firewalls, or perform external actions.')


# =========================================================
# 06 ESCALATIONS: ACKNOWLEDGE, ASSIGN, RESOLVE
# =========================================================
elif page == 'Escalation Center':
    heading('Exception management','Critical Threat Escalation',
            'Persist and audit response-team case handling; no external containment commands.')
    escalations=feed('queues/escalations') if dash_online else []
    actions=feed('escalation-actions') if dash_online else []
    a,b,c=st.columns(3)
    with a:summary_card('Escalated cases',len(escalations),'Latest risk-governed cases','kpi-danger')
    with b:summary_card('Recorded actions',len(actions),'Local analyst actions','kpi-cyan')
    with c:summary_card('Unacknowledged',sum(r.get('escalation_status')=='unacknowledged'
                                        for r in escalations),'Awaiting investigation owner','kpi-warning')
    heading('Live escalation queue','Critical investigations')
    show_rows(escalations,'No [E] Escalation cases stored yet.')
    if escalations:
        options={f"{r.get('alert_id')} · {r.get('investigation_id')}":r
                 for r in escalations}
        selected=options[st.selectbox('Select escalated investigation',list(options),
                                      key='escalation_case')]
        if selected.get('escalation_status')=='resolve':
            st.success('This case has a recorded resolution.')
        else:
            with st.form('escalate_form'):
                actor=st.text_input('Analyst ID',value=st.session_state.aegis_analyst,
                                     key='esc_actor')
                action=st.selectbox('Action',['acknowledge','assign','resolve'])
                assignee=st.text_input('Assignee (mandatory for assign)')
                rationale=st.text_area('Rationale (mandatory)',height=120)
                save=st.form_submit_button('Save escalation action',type='primary',
                                          use_container_width=True)
            if save:
                try:
                    data=dashboard_post('escalation-actions',{
                        'case_id':selected['case_id'],
                        'investigation_id':selected['investigation_id'],
                        'analyst_id':actor.strip(),'action':action,
                        'assignee':assignee.strip() or None,
                        'rationale':rationale.strip()})
                    st.success(f"Escalation action recorded: {data.get('action_id')}")
                    st.rerun()
                except RuntimeError as exc:st.error(str(exc))
    heading('Exception lifecycle','Escalation audit actions')
    show_rows(actions,'No escalation handling actions recorded yet.')
    st.caption('No external ticketing, account lock, firewall change or banking action is initiated.')


# =========================================================
# 07 MODEL LAB: MEASURED COMPARISON, NO INVENTED RESULTS
# =========================================================
elif page == 'Model Lab':
    heading('AI evaluation','Three-Model Research Lab',
            'Run the existing identical-prompt benchmark on three installed open-weight Ollama models.')
    from glob import glob
    registry=ROOT/'evaluation'/'model_registry.json'
    model_ids=['qwen3:8b','llama3.1:8b','gemma3:4b']
    if registry.exists():
        try:model_ids=[str(m['id']) for m in json.loads(registry.read_text())['models']]
        except (KeyError,ValueError,TypeError):pass
    available={r.get('name') for r in (ollama_health.get('data') or {}).get('models',[])}
    left,right=st.columns([1.1,1])
    with left:
        heading('Model registry','Candidate open-weight models')
        for model in model_ids:
            status_tag(model,model in available)
        selected=st.multiselect('Compare exactly three installed models',model_ids,
                                default=model_ids[:3],key='selected_models')
        st.caption('Missing models must be installed in local Ollama before evaluation. '
                   'No accuracy scores are fabricated.')
        runnable=len(selected)==3 and all(m in available for m in selected)
        if st.button('▶ Run real three-model benchmark',type='primary',
                     disabled=not runnable,use_container_width=True,key='launch_benchmark'):
            with st.spinner('Running genuine model inference. This can take several minutes...'):
                try:
                    process=subprocess.run([sys.executable,'-m',
                        'evaluation.benchmark_runner','--models',*selected],
                        cwd=str(ROOT),capture_output=True,text=True,timeout=1800,
                        check=False,env=os.environ.copy())
                    if process.returncode==0:
                        st.success('Benchmark completed; results written to evaluation/results/.')
                        st.code(process.stdout or 'Benchmark complete')
                    else:st.error((process.stderr or process.stdout)[-1800:])
                except subprocess.TimeoutExpired:
                    st.error('Benchmark exceeded the 30-minute safety timeout.')
                except (OSError,ValueError) as exc:st.error(str(exc))
    with right:
        heading('Benchmark method','Comparable controlled evaluation')
        st.write('**Dataset:** common labeled synthetic alert cases')
        st.write('**Prompt:** shared, fixed model instructions')
        st.write('**Scoring:** classification correctness against reference labels')
        st.write('**Telemetry:** inference latency and per-case classification output')
        st.info('The benchmark evaluates triage classification, not the entire SOC '
                'governance system. Policy decisions remain deterministic.')
    folder=ROOT/'evaluation'/'results'
    result_files=sorted(folder.glob('benchmark_*.json'),reverse=True) if folder.exists() else []
    heading('Measured evidence','Saved benchmark results')
    if not result_files:st.info('No benchmark results on disk yet. Install the '
                                'three models and run the evaluation.')
    else:
        selected_file=st.selectbox('Saved benchmark result',result_files,
                                  format_func=lambda p:p.name,key='bench_file')
        try:
            data=json.loads(selected_file.read_text(encoding='utf-8'))
            report_rows=[]
            for run in data.get('results',[]):
                row={'Model':run.get('model')}
                row.update(run.get('metrics',{}))
                report_rows.append(row)
            show_rows(report_rows,'No comparable model metrics in this file.')
            for run in data.get('results',[]):
                with st.expander(f"Model {run.get('model')} · individual cases",expanded=False):
                    show_rows(run.get('rows',[]),'No case results.')
            st.caption(f"Measured at: {data.get('generated_at','unknown')}")
        except (OSError,ValueError,TypeError) as exc:st.error(str(exc))


# =========================================================
# 08 GOVERNANCE: ACTUAL ROUTING DISTRIBUTION
# =========================================================
elif page == 'Governance':
    heading('Policy control plane','Deterministic Governance',
            'Risk policy is applied by the Python agent; LLM recommendations cannot bypass it.')
    modes=Counter(r.get('control_mode','Unknown') for r in latest.values())
    cols=st.columns(3)
    for col,(name,key,color) in zip(cols,[('Autonomous','[A] Autonomous','kpi-positive'),
                                       ('Human review','[H] HITL','kpi-warning'),
                                       ('Escalation','[E] Escalation','kpi-danger')]):
        with col:summary_card(name,modes.get(key,0),'Latest decision per case',color)
    heading('Real decisions','Saved risk scores and policy routes')
    show_rows(raw_investigations,'No completed governed investigations yet.',
              columns=['investigation_id','case_id','classification',
                       'overall_risk_score','control_mode','status'])
    heading('Policy transparency','Current Python governance rules')
    st.markdown('''
    - **Escalation [E]**: a critical asset, malicious IOC, and risk score at least 85.
    - **Human review [H]**: risk score at least 75, inadequate correlation confidence,
      or significant evidence gaps above the evidence-quality threshold.
    - **Autonomous [A]**: investigations meeting neither escalation nor human-review gate.
    - **Human action boundary**: recommendations do not execute containment or banking operations.
    ''')
    st.caption('Rules are documented from the current AEGIS Python governance design. '
               'The persisted control_mode field is authoritative for each actual case.')


# =========================================================
# 09 AUDIT: SQLITE AGENT + ANALYST ACTION HISTORY
# =========================================================
elif page == 'Audit Trail':
    heading('Chain of accountability','Investigation Audit Trail',
            'Combined original runtime audit entries and locally persisted analyst actions.')
    events=feed('audit',1000) if dash_online else []
    cols=st.columns(4)
    with cols[0]:summary_card('Audit entries',len(events),'Returned from database','kpi-cyan')
    with cols[1]:summary_card('Investigations',
                              overview.get('database',{}).get('investigations',0),
                              'Stored investigations','kpi-positive')
    with cols[2]:summary_card('Analyst decisions',len(feed('reviews')),
                              'Persisted human actions','kpi-warning')
    with cols[3]:summary_card('Escalation actions',len(feed('escalation-actions')),
                              'Locally recorded response','kpi-danger')
    if events:
        options=['All']+sorted({str(v.get('origin','agent_runtime')) for v in events})
        chosen=st.selectbox('Filter audit source',options)
        selected=[r for r in events if chosen=='All' or str(r.get('origin','agent_runtime'))==chosen]
        heading('Audit evidence','Latest recorded events')
        show_rows(selected)
        st.download_button('⬇ Export displayed audit JSON',
                           data=json.dumps(selected,indent=2,default=str),
                           file_name='aegis_audit_export.json',mime='application/json')
    else:st.info('No database audit entries available.')
    st.caption('Audit evidence is obtained from stored SQLite records, not temporary UI events.')


# =========================================================
# 10 SYSTEM STATUS: ACTIVE SERVICE PROBES
# =========================================================
elif page == 'System Status':
    heading('Runtime telemetry','AEGIS System Health',
            'Each component is checked against its actual local HTTP endpoint.')
    service_rows=[
        {'Service':'AEGIS FastAPI','Endpoint':api_url()+'/health',
         'Status':'ONLINE' if api_health['online'] else 'OFFLINE',
         'Check':'GET /health'},
        {'Service':'Dashboard API + SQLite','Endpoint':api_url()+'/dashboard/overview',
         'Status':'ONLINE' if dash_online else 'OFFLINE',
         'Check':'GET /dashboard/overview'},
        {'Service':'Local Ollama','Endpoint':st.session_state.aegis_ollama_url+'/api/tags',
         'Status':'ONLINE' if ollama_health['online'] else 'OFFLINE',
         'Check':'GET /api/tags'},
        {'Service':'n8n UI','Endpoint':'http://localhost:5678',
         'Status':'ONLINE' if n8n_health['online'] else 'OFFLINE',
         'Check':'GET / (UI only, not webhook)'},
    ]
    show_rows(service_rows,'No runtime probes available.')
    if dash_online:
        heading('SQLite','Live persistence counters')
        counts=overview.get('database',{})
        show_rows([{'Table':table,'Records':count} for table,count in counts.items()])
        st.success('Dashboard API can read the persisted AEGIS database.')
    else:st.warning('The SQLite dashboard API cannot currently be reached.')
    if ollama_health['online']:
        heading('Ollama runtime','Installed local models')
        show_rows(ollama_health['data'].get('models',[]),'No models installed.')
    st.info('n8n UI health does not guarantee that the POST webhook is published. '
            'A valid n8n URL must be configured separately before selecting that execution path.')
    st.caption('AEGIS is a local synthetic-data prototype. All external financial or '
               'production security actions remain disabled.')

# =========================================================
# END OF CONSOLIDATED DASHBOARD
# =========================================================
ui_html('<div class="aegis-footer">AEGIS SOC · Governed Agentic Investigation · '
        'Synthetic Data · Local Prototype · No External Banking Actions</div>')
