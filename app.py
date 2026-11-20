"""Galaxy IMMA Horizon public research workspace."""
import json
import os
import re
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from exports import build_exports, evidence_text
from research import MAX_TICKERS, collect, draft, normalize_tickers

EXAMPLES = Path(__file__).with_name('examples')

st.set_page_config(page_title='Galaxy IMMA Horizon', page_icon='✦', layout='wide')
st.markdown("""
<style>
.stApp {
  background: radial-gradient(ellipse at 85% 0%, #172447 0%, transparent 42%), #070d1f;
}
[data-testid="stMainBlockContainer"] { max-width: 1200px; padding-top: 3.15rem; }
.horizon {
  min-height: 270px; display: grid; align-content: center; padding: clamp(22px, 5vw, 62px);
  border: 1px solid #37476c; border-radius: 24px;
  background: linear-gradient(90deg, #070d1f 3%, #070d1fed 27%, #070d1f70 57%, transparent 100%),
    url("app/static/galaxy-horizon.webp") right center / cover;
}
.horizon p { color: #c5d2ed; font-size: 1rem; margin: .85rem 0 0; max-width: 32rem; }
.horizon .brand { color: #57dbff; font-size: .75rem; letter-spacing: .23em; font-weight: 700; }
.horizon h1 { font-size: clamp(2.35rem, 6vw, 4.75rem); line-height: .98; padding: 0;
  margin: .55rem 0 0; letter-spacing: -.06em; max-width: 12ch; }
@media (max-width: 640px) {
  .horizon {
    min-height: 255px; align-content: end; background:
      linear-gradient(180deg, transparent 0%, #070d1fed 75%),
      url("app/static/galaxy-horizon.webp") 64% center / cover;
  }
}
</style>
<section class="horizon" aria-label="Galaxy IMMA Horizon">
  <div class="brand">GALAXY IMMA HORIZON</div>
  <h1>Market intelligence</h1>
  <p>Research listed companies and macro developments. Download a brief with links to the evidence.</p>
</section>
""", unsafe_allow_html=True)

@st.cache_data(ttl=900, max_entries=160, show_spinner=False)
def cached_evidence(symbols, topic):
    return collect(symbols, topic)


@st.cache_resource
def ai_quota():
    return Lock(), {"day": None, "calls": 0, "last": float("-inf")}


def reserve_cloud_call():
    lock, limits = ai_quota()
    with lock:
        day = datetime.now(timezone.utc).date()
        now = monotonic()
        if limits["day"] != day:
            limits.update(day=day, calls=0)
        if limits["calls"] >= 100 or now - limits["last"] < 20:
            return False
        limits.update(calls=limits["calls"] + 1, last=now)
        return True


def cloud_settings():
    try:
        key = st.secrets.get("GROQ_API_KEY")
        model = st.secrets.get("GROQ_MODEL")
    except StreamlitSecretNotFoundError:
        key, model = None, None
    return key or os.environ.get("GROQ_API_KEY"), model or os.environ.get(
        "GROQ_MODEL", "llama-3.3-70b-versatile"
    )


def markdown_text(text):
    return re.sub(r"([\\`*_{}\[\]()<>#!|])", r"\\\1", text)


def show_downloads(blobs, historical=False):
    suffix = "Example" if historical else "Research"
    kinds = [
        ("PDF", "pdf", "application/pdf"),
        ("Editable PowerPoint", "pptx",
         "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        ("Evidence JSON", "json", "application/json"),
    ]
    for column, (label, extension, mime), payload in zip(st.columns(3), kinds, blobs):
        column.download_button(label, payload, f"Galaxy_IMMA_{suffix}.{extension}", mime,
                               key=f"{suffix}-{extension}", on_click="ignore")


def show_report(report):
    st.subheader("Research brief")
    st.caption(f'{report["method"]} · {report["window_start"]} to {report["generated_at"][:10]} · Jakarta time')
    st.caption("Daily prices may include an open session. Open headline sources to verify the underlying claims.")
    scopes = st.tabs([markdown_text(section["name"]) for section in report["sections"]])
    for section, tab in zip(report["sections"], scopes):
        with tab:
            for row in section["rows"]:
                if row["kind"] == "price":
                    st.metric(row["title"], row["value"])
                    if row["change_pct"] is not None:
                        st.caption(f'{row["change_pct"]:+.2f}% since {row["points"][0][0]} · unadjusted daily prices')
                    frame = pd.DataFrame(row["points"], columns=["Session", "Price"])
                    frame["Session"] = pd.to_datetime(frame["Session"])
                    st.line_chart(frame, x="Session", y="Price", height=185)
                    st.link_button(f'{row["id"]} · {row["source"]} · {row["date"]}', row["url"])
            headlines = [row for row in section["rows"] if row["kind"] == "headline"]
            if headlines:
                st.markdown("**Recent headlines**")
            for row in headlines:
                st.link_button(markdown_text(f'{row["id"]} · {evidence_text(row)}'), row["url"])
                st.caption(markdown_text(f'{row["source"]} · {row["date"]}'))
            if section["ai"]:
                st.markdown("**AI interpretation**")
                for insight in section["ai"]:
                    refs = ", ".join(insight["evidence_ids"])
                    st.markdown(f'- {markdown_text(insight["text"])} · {refs}')
            st.markdown("**What to check next**")
            for item in section["watch"]:
                st.markdown(f"- {item}")
            for gap in section["gaps"]:
                st.info(gap)


workspace, sample = st.tabs(["Research workspace", "Historical example"])

with workspace:
    api_key, model = cloud_settings()
    mode = st.radio("Research scope", ["Stocks", "Macro", "Stocks and macro"], horizontal=True)
    with st.form("research-request"):
        tickers = ""
        topic = ""
        exchange = "Indonesia (IDX)"
        if mode != "Macro":
            exchange = st.selectbox("Ticker convention", ["Indonesia (IDX)", "Global"])
            tickers = st.text_input("Tickers", value="BSDE, PWON", max_chars=90,
                                    help=f"Separate up to {MAX_TICKERS} symbols with commas. IDX adds .JK to bare symbols.")
        if mode != "Stocks":
            topic = st.text_input("Macro topic", value="properti Indonesia", max_chars=100,
                                  help="Use a short public search phrase.")
        use_model = bool(api_key) and st.checkbox("Add cloud AI interpretation", value=True,
                                                  help="Sends the topic and public evidence labels to the configured model.")
        submitted = st.form_submit_button("Generate brief", type="primary")
    if submitted:
        try:
            symbols = normalize_tickers(tickers, exchange == "Indonesia (IDX)")
            topic = " ".join(topic.split())
            if mode != "Macro" and not symbols:
                raise ValueError("Enter at least one stock ticker.")
            if mode != "Stocks" and not any(character.isalnum() for character in topic):
                raise ValueError("Enter a macro topic.")
        except ValueError as error:
            st.warning(str(error))
        else:
            with st.spinner("Gathering recent evidence and building your brief…"):
                evidence_packet = cached_evidence(tuple(symbols), topic)
                run_ai = use_model and any(section["rows"] for section in evidence_packet["sections"]) and reserve_cloud_call()
                report = draft(evidence_packet, api_key if run_ai else None, model)
                if use_model and not run_ai and any(section["rows"] for section in report["sections"]):
                    report["method"] = "Structured brief · cloud AI quota busy"
                st.session_state["live_report"] = report, build_exports(report)
    if "live_report" in st.session_state:
        live_report, live_downloads = st.session_state["live_report"]
        show_report(live_report)
        st.subheader("Download this brief")
        show_downloads(live_downloads)
    else:
        st.caption("Uses the latest available evidence within a rolling 30-day window. Public source results can be cached for 15 minutes.")


packet = json.loads((EXAMPLES / 'Galaxy_IMMA_Example_Evidence.json').read_text(encoding='utf-8'))
note = packet['research_note']
evidence = {item['id']: item for item in note['evidence']}

with sample:
    st.caption(f"Historical example · Evidence cutoff {note['cutoff']}")
    overview, research, exports = st.tabs(['Overview', 'Research note', 'Downloads'])

    with overview:
        st.subheader('Indonesia property')
        for column, key in zip(st.columns(3), ('E1', 'E2', 'E3')):
            item = evidence[key]
            column.metric(item['title'], item['value'], border=True)
            column.caption(item['date'])
        st.write('The November rate decision followed a quarter in which GDP grew and primary-market home sales fell.')
        st.caption('Explore Research note to see the company implications and the sources behind each finding.')

    with research:
        section_names = {section['title']: section for section in note['sections']}
        selection = st.selectbox('View', list(section_names))
        for finding in section_names[selection]['findings']:
            with st.container(border=True):
                st.caption(finding['category'].capitalize())
                st.write(finding['text'])
                for ident in finding['evidence_ids']:
                    item = evidence[ident]
                    st.link_button(f"{item['source']} · {item['date']}", item['url'])

    with exports:
        st.subheader('Download the example research brief')
        for label, filename, mime in (
            ('Download PDF', 'Galaxy_IMMA_Example.pdf', 'application/pdf'),
            ('Download editable PowerPoint', 'Galaxy_IMMA_Example.pptx',
             'application/vnd.openxmlformats-officedocument.presentationml.presentation'),
            ('Download evidence JSON', 'Galaxy_IMMA_Example_Evidence.json', 'application/json'),
        ):
            st.download_button(label, (EXAMPLES / filename).read_bytes(), filename, mime)
