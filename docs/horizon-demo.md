# Galaxy IMMA Horizon online research

The **Research workspace** generates a downloadable PDF, editable PowerPoint
and evidence JSON for stocks, a macro topic, or both. It uses a rolling 30-day
window, open to any provider-supported ticker. The Indonesia convention adds
`.JK` to bare stock symbols. Choose Global to enter other markets' symbols as
listed by Yahoo Finance. Each request supports up to five stocks.

Market data uses unadjusted daily prices from Yahoo Finance. The latest daily
bar may still be forming. Headlines use Google News RSS. The macro search also
looks for indexed releases from BI, BPS and the Ministry of Finance. Publication
dates reflect the index and should be verified at the source. Headlines are leads,
and prices are a snapshot. A missing or throttled provider is shown in the brief.
Evidence is cached for 15 minutes. The former demo remains under **Historical
example**.

The source-backed structured brief and exports require no model credentials.
To enable optional Llama analysis, set `GROQ_API_KEY` in Streamlit Community
Cloud's app secrets. Optionally set `GROQ_MODEL` to an available Groq chat model
that supports JSON mode. The default is `llama-3.3-70b-versatile`. Use a free-tier
provider project if the deployment must stay free. The key stays server-side.
The app sends the public topic and evidence labels to the model when enabled,
validates its citation IDs, and falls back to a structured brief if a request is
limited or fails. In-process limits are 100 attempts per UTC day and at least
20 seconds between attempts. The provider's project limits apply across restarts.

Deploy on Streamlit Community Cloud with **app.py** as the entry point and
Python 3.12. Public viewers can use the workspace without signing in.
To preview locally, install `requirements.txt` and run `streamlit run app.py`.
