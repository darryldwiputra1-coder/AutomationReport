"""Public Galaxy IMMA Horizon demo using a frozen example."""
import json
from pathlib import Path

import streamlit as st

EXAMPLES = Path(__file__).with_name('examples')

st.set_page_config(page_title='Galaxy IMMA Horizon', page_icon='✦', layout='wide')
st.markdown("""
<style>
.stApp {
  background: radial-gradient(ellipse at 85% 0%, #172447 0%, transparent 42%), #070d1f;
}
[data-testid="stMainBlockContainer"] { max-width: 1200px; padding-top: 3.15rem; }
.horizon {
  min-height: 335px; display: grid; align-content: center; padding: clamp(22px, 5vw, 62px);
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
    min-height: 320px; align-content: end; background:
      linear-gradient(180deg, transparent 0%, #070d1fed 75%),
      url("app/static/galaxy-horizon.webp") 64% center / cover;
  }
}
</style>
<section class="horizon" aria-label="Galaxy IMMA Horizon">
  <div class="brand">GALAXY IMMA HORIZON</div>
  <h1>Market intelligence</h1>
  <p>Explore Indonesian property, company results, and a source-linked research brief.</p>
</section>
""", unsafe_allow_html=True)

packet = json.loads((EXAMPLES / 'Galaxy_IMMA_Example_Evidence.json').read_text(encoding='utf-8'))
note = packet['research_note']
evidence = {item['id']: item for item in note['evidence']}

st.caption(f"Public demo · Historical example · Evidence cutoff {note['cutoff']}")
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
    st.caption('The Windows edition supports live retrieval, local AI drafting, and report generation.')
