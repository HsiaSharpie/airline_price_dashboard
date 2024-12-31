-- CREATE DATABASE flights;

\c flights;


-- CREATE TABLE flights (
--     flight_id SERIAL PRIMARY KEY,   -- 自增的唯一識別符號
--     airline VARCHAR(255),           -- 航空公司名稱
--     currency VARCHAR(10),           -- 貨幣單位
--     amount DECIMAL(10, 2),          -- 價格
--     outbound_time VARCHAR(20),      -- 出發時間
--     inbound_time VARCHAR(20),       -- 返回時間
--     timestamp TIMESTAMP,            -- 記錄時間戳
--     UNIQUE(airline, outbound_time, inbound_time)  -- 唯一約束來標識航班
-- );


CREATE TABLE user_selected_flights (
    id SERIAL PRIMARY KEY,                  -- primary key
    user_id INT,                            -- 對應到的使用者id (後續考量加入)
    departure_place VARCHAR(255),           -- 出發地點
    destination_place VARCHAR(255),         -- 目的地點
    outbound_date VARCHAR(255),             -- 去程日期
    inbound_date VARCHAR(255),              -- 回程日期
    is_deleted BOOLEAN DEFAULT FALSE        -- 是否刪除
);

-- todo: normalization
CREATE TABLE flights_history (
    id SERIAL PRIMARY KEY,                  -- primary key
    flight_id  VARCHAR(255),                -- 用來辨識爬取的航班組合(uuid)可重複 (考慮是否刪除)
    departure_place VARCHAR(255),           -- 出發地點
    destination_place VARCHAR(255),         -- 目的地點
    outbound_date VARCHAR(255),             -- 去程日期
    inbound_date VARCHAR(255),              -- 回程日期
    outbound_airline VARCHAR(255),          -- 去程航空公司名稱
    inbound_airline VARCHAR(255),           -- 回程航空公司名稱
    currency VARCHAR(10),                   -- 貨幣單位
    amount DECIMAL(10, 2),                  -- 價格
    outbound_depart_time VARCHAR(20),       -- 去程出發時間
    outbound_arrive_time VARCHAR(20),       -- 去程抵達時間
    inbound_depart_time VARCHAR(20),        -- 回程出發時間
    inbound_arrive_time VARCHAR(20),        -- 回程抵達時間
    parsed_timestamp TIMESTAMP,             -- 記錄時間戳
    user_selected_flights INT               -- 對應到 user_selected_flights 表格的 id
);

CREATE INDEX idx_flight_combination 
ON flights_history (outbound_date, inbound_date, outbound_airline, inbound_airline, 
                    outbound_depart_time, outbound_arrive_time, 
                    inbound_depart_time, inbound_arrive_time);