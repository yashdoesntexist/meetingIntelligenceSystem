import json
from pathlib import Path
import pandas as pd
import streamlit as st
from config import DEFAULT_OUTPUT_JSON

st.set_page_config(page_title="Meeting Action Items", layout="wide")
st.title("Meeting Action Items")


json_path = st.text_input("Actions JSON path", value=str(DEFAULT_OUTPUT_JSON))

if Path(json_path).exists():
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    df = pd.DataFrame(data)
    with st.sidebar:
        meeting = st.selectbox("Filter by meeting", ["(all)"] + sorted(df["meeting"].dropna().unique().tolist()))
        assignee = st.selectbox("Filter by assignee", ["(all)"] + sorted(df["assignee"].dropna().unique().tolist()))
    view = df.copy()
    if meeting != "(all)":
        view = view[view["meeting"] == meeting]
    if assignee != "(all)":
        view = view[view["assignee"] == assignee]
    st.dataframe(view, use_container_width=True)
else:
    st.warning("JSON not found. Run extraction first.")
