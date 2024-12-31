import time
import random
from datetime import datetime, timedelta
from uuid import uuid4

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException


DATE_ADD = 22
RETRIES = 3
POSTGRES_CONN_ID = "flights_db"


def setup_chrome_options():
    """設置 Chrome 選項"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    )
    return options


def input_text_and_confirm(driver, by, value, text, wait_time=10):
    """輸入文字並按下 Enter 鍵"""
    try:
        input_box = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((by, value))
        )
        input_box.click()
        input_box.send_keys(text)
        time.sleep(random.uniform(1, 3))  # 等待選單出現
        input_box.send_keys(Keys.ENTER)
        time.sleep(random.uniform(2, 5))  # 等待輸入完成
    except Exception as e:
        print(f"輸入文字失敗: {e}")
        raise


def wait_and_click(driver, by, value, wait_time=10, wait_obj=None):
    """等待元素可點擊並執行點擊"""
    if not wait_obj:
        wait_obj = WebDriverWait(driver, wait_time)
    try:
        element = wait_obj.until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        time.sleep(random.uniform(1, 5))
        return wait_obj
    except Exception as e:
        print(f"等待和點擊元素失敗: {e}")
        raise


def run_selenium_task(**kwargs):
    id = kwargs.get("id")
    outbound_date = kwargs.get("outbound_date")
    inbound_date = kwargs.get("inbound_date")
    outbound_place = kwargs.get("outbound_place")
    inbound_place = kwargs.get("inbound_place")

    execution_date_obj = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    outbound_date_obj = datetime.strptime(outbound_date, "%Y-%m-%d")

    if not (outbound_date or inbound_date):
        print("There's no outbound_date or inbound_date in kwargs")
        return

    chrome_options = setup_chrome_options()
    for attempt in range(RETRIES):
        try:
            with webdriver.Remote("http://selenium:4444/wd/hub", options=chrome_options) as driver:
                outbound_place_list = outbound_place.split(",")
                inbound_place_list = inbound_place.split(",")

                driver.get("https://www.wego.tw/")
                time.sleep(random.uniform(2, 3))

                # 填寫出發地和目的地
                input_text_and_confirm(driver, By.ID, "outboundSearchQuery", random.choice(outbound_place_list))
                input_text_and_confirm(driver, By.ID, "inboundSearchQuery", random.choice(inbound_place_list))

                # 隨機點一個時間日期後，再次點選按鈕展開 date-picker
                wait_and_click(driver,
                               By.CSS_SELECTOR, 
                               f"div[data-testid='{(execution_date_obj + timedelta(days=DATE_ADD)).strftime("%Y-%m-%d")}']")
                wait_and_click(driver,
                               By.CSS_SELECTOR, 
                               "div[data-testid='from-input-value']")
                
                # 點擊多次以跳轉月份
                button_click_times = int((outbound_date_obj - execution_date_obj).days/30) + 2
                for _ in range(button_click_times):
                    wait_and_click(driver, 
                                   By.CSS_SELECTOR, 
                                   "div[data-testid='next-month-button']", 
                                   random.uniform(3, 10))
                
                # 重新點開後點選出發、回程日期並搜尋
                wait = WebDriverWait(driver, random.uniform(3, 10))
                wait = wait_and_click(driver, 
                                      By.CSS_SELECTOR,
                                      f"div[data-testid='{outbound_date}']", 
                                      random.uniform(3, 10), 
                                      wait)
                wait = wait_and_click(driver, 
                                      By.CSS_SELECTOR,
                                      f"div[data-testid='{inbound_date}']", 
                                      random.uniform(3, 10), 
                                      wait)

                wait = wait_and_click(driver, 
                                      By.XPATH, 
                                      "//button[text()='搜索']", 
                                      random.uniform(3, 10), 
                                      wait)
                try:
                    current_window = driver.current_window_handle
                    WebDriverWait(driver, 10).until(
                        lambda driver: len(driver.window_handles) > 1
                    )
                    
                    # 獲取所有打開的窗口句柄
                    all_windows = driver.window_handles

                    # 切換到新分頁
                    for window in all_windows:
                        if window != current_window:
                            driver.switch_to.window(window)
                            break

                    # 等待新分頁加載完成，這裡等待某個元素出現
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@data-testid="trip-card"]'))
                    )
                    time.sleep(random.uniform(5, 8))

                    trip_card_elements = wait.until(
                        EC.presence_of_all_elements_located((By.XPATH, '//div[@data-testid="trip-card"]'))
                    )
                    print(f"total_cnt: {len(trip_card_elements)}")
                    
                    # 遍歷所有找到的價格元素
                    total_list = []
                    for trip_card_element in trip_card_elements:
                        try:
                            # 取得航空公司名稱
                            airline_name_elements = trip_card_element.find_elements(By.CSS_SELECTOR, "span[data-pw='leg_airlineName']")
                            
                            # 取得出發時間
                            departure_time_elements = trip_card_element.find_elements(By.CSS_SELECTOR, "div[data-testid='depart-time']")
                            
                            # 取得抵達時間
                            arrival_time_elements = trip_card_element.find_elements(By.CSS_SELECTOR, "div[data-testid='arrive-time']")

                            # 提取價格內容
                            price_element = trip_card_element.find_element(By.CSS_SELECTOR, "div[data-testid='price']")
                            currency = price_element.find_element(By.XPATH, ".//span[1]").text
                            amount = price_element.find_element(By.XPATH, ".//span[2]").text

                            assert len(airline_name_elements) == len(departure_time_elements) == len(arrival_time_elements) == 2

                            idx = 0
                            current_airline_info = {}
                            for (airline, departure_time, arrival_time) in zip(airline_name_elements, departure_time_elements, arrival_time_elements):
                                if idx == 0:
                                    current_airline_info["id"] = id
                                    current_airline_info["outbound_date"] = outbound_date
                                    current_airline_info["outbound_airline"] = airline.text
                                    current_airline_info["currency"] = currency
                                    current_airline_info["amount"] = amount
                                    current_airline_info["outbound_depart_time"] = departure_time.text
                                    current_airline_info["outbound_arrive_time"] = arrival_time.text
                                else:
                                    current_airline_info["inbound_date"] = inbound_date
                                    current_airline_info["inbound_airline"] = airline.text
                                    current_airline_info["inbound_depart_time"] = departure_time.text
                                    current_airline_info["inbound_arrive_time"] = arrival_time.text
                                idx += 1
                            total_list.append(current_airline_info)
                        except Exception as e:
                            print(f"無法解析此價格元素: {e}")
                except Exception as e:
                    print("等待頁面加載超時")
                ti = kwargs["ti"]
                ti.xcom_push(key="airplane_price_list", value=total_list)
                print(f"total_list: {total_list}")
                return total_list
        except WebDriverException as e:
            print(f"Attempt {attempt + 1}/{RETRIES} failed: {e}")
            time.sleep(5)
    raise Exception("Failed to connect to Selenium service after retries.")


def insert_to_postgres(**kwargs):
    task_instance = kwargs["task_instance"]
    dag = kwargs["dag"]
    task_id = task_instance.task_id
    current_task = dag.get_task(task_id)
    
    # Get upstream task IDs
    upstream_task_ids = list(current_task.upstream_task_ids)[0] # 確認上游task只有一個
    print(f"Upstream task IDs for {task_id}: {upstream_task_ids}")

    # pull the house_price_list from task instance
    ti = kwargs["ti"]
    airplane_price_list = ti.xcom_pull(task_ids=upstream_task_ids, key="airplane_price_list")
    if not airplane_price_list:
        return f"Can not pull airplane_price_list from task instance"

    # set up connection to postgres_db with PostgresHook
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = hook.get_conn()
    cursor = conn.cursor()

    for x in airplane_price_list:
        # 定義航班組合作為 key
        flight_key = (
            x["outbound_date"],
            x["inbound_date"],
            x["outbound_airline"],
            x["inbound_airline"],
            x["outbound_depart_time"],
            x["outbound_arrive_time"],
            x["inbound_depart_time"],
            x["inbound_arrive_time"],
        )

        # 檢查是否已有相同的航班組合
        cursor.execute(
            """
            SELECT flight_id 
            FROM flights_history 
            WHERE outbound_date = %s 
              AND inbound_date = %s 
              AND outbound_airline = %s 
              AND inbound_airline = %s 
              AND outbound_depart_time = %s 
              AND outbound_arrive_time = %s 
              AND inbound_depart_time = %s 
              AND inbound_arrive_time = %s
            """,
            flight_key,
        )
        result = cursor.fetchone()

        # 如果存在，使用現有的 flight_id；否則生成新的 flight_id
        flight_id = result[0] if result else str(uuid4())

        # 插入資料
        cursor.execute(
            """
            INSERT INTO flights_history 
            (flight_id, outbound_date, inbound_date, outbound_airline, inbound_airline, 
             currency, amount, outbound_depart_time, outbound_arrive_time, 
             inbound_depart_time, inbound_arrive_time, parsed_timestamp, user_selected_flights_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                flight_id,
                x["outbound_date"],
                x["inbound_date"],
                x["outbound_airline"],
                x["inbound_airline"],
                x["currency"],
                float(x["amount"].replace(",", "")),
                x["outbound_depart_time"],
                x["outbound_arrive_time"],
                x["inbound_depart_time"],
                x["inbound_arrive_time"],
                datetime.now(),
                x["id"],
            ),
        )
    conn.commit()
    cursor.close()
    conn.close()


with DAG(
    "selenium_dag",
    default_args={
        "start_date": datetime(2024, 1, 1),
        "retries": None,
        "retry_delay": timedelta(minutes=10),
    },
    schedule_interval="*/30 * * * *",
    catchup=False,
) as dag:
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = hook.get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
            select id, outbound_place, inbound_place, outbound_date, inbound_date
            from user_selected_flights
            where is_deleted is False;
        """,
    )
    result = cursor.fetchall()
    for row in result:
        id = row[0]
        outbound_place = row[1]
        inbound_place = row[2]
        outbound_date = row[3]
        inbound_date = row[4]
        
        selenium_task = PythonOperator(
            task_id=f"run_selenium_{outbound_place}_to_{inbound_place}_{str(id)}",
            python_callable=run_selenium_task,
            provide_context=True,  # 允許 Airflow 把 DAG 執行上下文（如 execution_date, dag_run 等）傳遞到函數中，並作為 kwargs
            op_kwargs={
                "id": id,
                "outbound_date": outbound_date,
                "inbound_date": inbound_date,
                "outbound_place": outbound_place,
                "inbound_place": inbound_place,
            },
        )
        insert_flights_data_task = PythonOperator(
            task_id=f"insert_flights_data__{outbound_place}_to_{inbound_place}_{str(id)}",
            python_callable=insert_to_postgres)
        
        selenium_task >> insert_flights_data_task