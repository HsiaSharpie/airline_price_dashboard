import os

from dotenv import load_dotenv
import streamlit as st
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from core import get_engine

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

def submit_flight_tab():
    # Date Picker
    st.subheader("選擇航班日期範圍")
    outbound_date = st.date_input("出發日期").strftime("%Y-%m-%d")
    inbound_date = st.date_input("回程日期").strftime("%Y-%m-%d")


    # todo: 之後更改成下拉式選單
    # 出發地輸入
    st.subheader("輸入出發地")
    outbound_place = st.text_area("輸入出發地城市（一次請只輸入一個城市）")
    outbound_place_list = [x.strip() for x in outbound_place.split(",") if x.strip()]

    # 目的地輸入
    st.subheader("輸入目的地")
    inbound_place = st.text_area("輸入目的地城市（一次請只輸入一個城市）")
    inbound_place_list = [x.strip() for x in inbound_place.split(",") if x.strip()]

    # 提交按鈕
    if st.button("提交"):
        if outbound_place_list and inbound_place_list:
            try:
                with engine.connect() as conn:
                    data_to_insert = [
                        {
                            "outbound_place": outbound_place,
                            "inbound_place": inbound_place,
                            "outbound_date": outbound_date,
                            "inbound_date": inbound_date,
                        }
                        for outbound_place, inbound_place in zip(outbound_place_list, inbound_place_list)
                    ]
                    conn.execute(
                        text("""
                                INSERT INTO user_selected_flights (outbound_place, inbound_place, outbound_date, inbound_date) 
                                VALUES (:outbound_place, :inbound_place, :outbound_date, :inbound_date)"""
                        ),
                        data_to_insert,
                    )
                    conn.commit()
                st.success("航班已成功提交至追蹤列表！")
                # 觸發頁面刷新
                st.rerun()
            except SQLAlchemyError as e:
                st.error(f"資料庫操作失敗：{str(e)}")
        else:
            st.error("請至少填寫一個航班號碼！")