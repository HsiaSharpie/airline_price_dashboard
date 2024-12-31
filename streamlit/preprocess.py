import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from core import load_data

TOTAL_FLIGHTS = 6


def get_dropdown_selection():
    dropdown_data =  load_data(
        """
            select id, outbound_place, inbound_place, outbound_date, inbound_date
            from user_selected_flights
            where is_deleted = False;
        """,
    )
    return {
        f"{x['outbound_date']} {x['outbound_place']} 出發 / {x['inbound_date']} {x['inbound_place']} 抵達":
        x["id"]
        for x in dropdown_data
    }


def get_dropdown_data(dropdown_selection, page_selection):
    user_selected_flights_id = dropdown_selection[page_selection]

    df_avg_prices = load_data(f"""
        with recent_prices as (
            select *,
                   row_number() over (partition by flight_id order by parsed_timestamp desc) as row_num
            from flights_history
            where user_selected_flights_id = :user_selected_flights_id
        ),
        avg_prices AS (
            select flight_id, avg(amount) as avg_price
            from recent_prices
            where row_num <= :total_flights
            group by flight_id
            order by avg_price asc
            limit :total_flights
        )
        select flight_id, avg_price
        from avg_prices;
    """, params={
        "user_selected_flights_id": user_selected_flights_id,
        "total_flights": TOTAL_FLIGHTS,
    }, return_type="dataframe")

    # 取出前 TOTAL_FLIGHTS 組的航班資料
    flight_ids = tuple(df_avg_prices["flight_id"].tolist())
    df_flight_history_data = load_data(f"""
        select *
        from flights_history
        where flight_id IN {flight_ids}
        order by flight_id, parsed_timestamp desc;
    """, return_type="dataframe")

    df_avg_prices = df_flight_history_data.groupby("flight_id")["amount"].mean().reset_index()
    df_avg_prices = df_avg_prices.sort_values("amount", ascending=True)  # 根據價格排序
    df_avg_prices = df_avg_prices.reset_index(drop=True)

    return df_flight_history_data, df_avg_prices


def streamlit_history_data(
    df_flight_history_data,
    group_data,
    per_group_cnts):
    # 增加欄位數量，以便間隔更多空間
    columns = st.columns(per_group_cnts)

    current_group_cnt = 0
    for _, (flight_id, group) in enumerate(df_flight_history_data.groupby("flight_id")):
        if current_group_cnt >= per_group_cnts:
            break
        if flight_id in group_data["flight_id"].tolist():
            avg_price = group["amount"].mean()
            outbound_depart_time = group["outbound_depart_time"].iloc[0]
            outbound_arrive_time = group["outbound_arrive_time"].iloc[0]
            outbound_airline = group["outbound_airline"].iloc[0]

            inbound_depart_time = group["inbound_depart_time"].iloc[0]
            inbound_arrive_time = group["inbound_arrive_time"].iloc[0]
            inbound_airline = group["inbound_airline"].iloc[0]

            with columns[current_group_cnt]:  # 動態選擇對應的欄位
                st.subheader(f"航班 {flight_id[:5]}")
                st.markdown(f'<p style="font-size: 14px;">• 去程 / {outbound_airline} : {outbound_depart_time} → {outbound_arrive_time}</p>', unsafe_allow_html=True)
                st.markdown(f'<p style="font-size: 14px;">• 回程 / {inbound_airline} : {inbound_depart_time} → {inbound_arrive_time}</p>', unsafe_allow_html=True)
                
                # 繪製價格變化折線圖
                fig = px.line(
                    group,
                    x="parsed_timestamp",
                    y="amount",
                    # title=f"航班 {flight_id[:5]} 的價格變化",
                    labels={"parsed_timestamp": "時間", "amount": "價格 (NT$)"}
                )
                
                # 添加一條顯示平均價格的水平線
                fig.add_trace(go.Scatter(
                    x=group["parsed_timestamp"],  # 使用相同的 x 軸資料
                    y=[avg_price] * len(group),  # 生成一條所有 y 值為平均價格的線
                    mode="lines",
                    name="平均價格",
                    line=dict(color="red", dash="dash")  # 設定顏色為紅色，並使用虛線
                ))

                # 設置 hovertemplate 來顯示數值
                fig.update_traces(
                    hovertemplate="<b>%{x}</b><br>價格: %{y} NT$<extra></extra>"  # 顯示時間和價格
                )

                # 調整圖表大小
                fig.update_layout(
                    width=600,  # 設定圖表寬度
                    height=400,  # 設定圖表高度
                    margin=dict(l=20, r=20, t=40, b=20),  # 設定邊距來進一步控制大小
                )

                st.plotly_chart(fig, use_container_width=False)  # 設置圖表不等寬
            current_group_cnt += 1
    st.markdown("<br>", unsafe_allow_html=True)