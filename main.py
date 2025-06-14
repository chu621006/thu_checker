import streamlit as st
import pandas as pd
from utils.credit_rules import analyze_pdf, check_requirements

st.set_page_config(page_title="東海日文系學分查詢", layout="wide")
st.title("📘 東海日文系學分查詢網站")

uploaded_file = st.file_uploader("請上傳成績單 PDF", type="pdf")

if uploaded_file:
    st.success("PDF 已上傳，正在處理中...")
    results = analyze_pdf(uploaded_file)

    st.subheader("✅ 成績解析結果")
    st.dataframe(results["course_table"], use_container_width=True)

    st.subheader("📊 學分統計結果")
    st.dataframe(results["summary_table"], use_container_width=True)

    st.subheader("🚦 學分檢查狀態")
    st.dataframe(check_requirements(results["summary_table"]), use_container_width=True)