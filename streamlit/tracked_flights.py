import streamlit as st

from core import load_data


def tracked_flights_tab():
    # 顯示用戶已選擇的航班
    st.subheader("已關注的航班資訊")

    # 這裡從資料庫載入關注的航班資訊
    flights_data = load_data("""
        select outbound_place, inbound_place, outbound_date, inbound_date
        from user_selected_flights 
        where is_deleted = FALSE;
    """, return_type="dataframe")

    if flights_data is not None and not flights_data.empty:
        st.dataframe(flights_data)
    else:
        st.write("目前沒有已關注的航班資訊。")