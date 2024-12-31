import os

from dotenv import load_dotenv
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from core import get_engine
from submit_flight import submit_flight_tab
from tracked_flights import tracked_flights_tab
from preprocess import get_dropdown_selection, get_dropdown_data, streamlit_history_data

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "flights_db")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")


engine = get_engine(
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    ip=POSTGRES_HOST,
    port=POSTGRES_PORT,
    database=POSTGRES_DB,
    connect_type="POSTGRESQL",
)

# Streamlit 介面
st.set_page_config(
    page_title="航班趨勢追蹤 Dashboard",
    layout="wide",
)
st.title("航班趨勢追蹤 Dashboard")

# 分頁功能
tabs = st.tabs(["提交航班號碼", "關注航班資訊", "機票價格歷史記錄"])

# 分頁1: 提交航班號碼
with tabs[0]:
    submit_flight_tab()


# 分頁2: 顯示已關注航班區塊
with tabs[1]:
    tracked_flights_tab()


# 分頁3: 顯示爬蟲價格記錄變化
with tabs[2]:
    # set page settings
    st.subheader("追蹤記錄")
    st.markdown("<h1 style='text-align: center;'>Airline Price Comparison Dashboard</h1>", unsafe_allow_html=True)
    with st.sidebar:
        st.header("⚙️ Settings")
        refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 60)
        st_autorefresh(interval=refresh_interval * 1000, key="auto")

    # 下拉式選單部分選項
    dropdown_selection = get_dropdown_selection()
    page_selection = st.selectbox("選擇頁面", dropdown_selection.keys())
    st.markdown("<br>", unsafe_allow_html=True)

    # 取得下拉式選單內容
    df_flight_history_data, df_avg_prices = get_dropdown_data(
        dropdown_selection, page_selection)

    if df_flight_history_data.empty:
        st.write("目前沒有資料可供顯示。")
    else:
        st.write(df_avg_prices)
        st.markdown("<br>", unsafe_allow_html=True)

        # 根據平均價格分成兩組
        per_group_cnts = len(df_avg_prices) // 2
        top_group = df_avg_prices[:per_group_cnts]  # 平均價格較低的組
        bottom_group = df_avg_prices[per_group_cnts:]  # 平均價格較高的組

        for group in [top_group, bottom_group]:
            streamlit_history_data(df_flight_history_data, group, per_group_cnts)