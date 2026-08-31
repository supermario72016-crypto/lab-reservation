import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time

# ================= 1. 資料庫初始化 (新增跨日欄位) =================
conn = sqlite3.connect('lab_reservations_v2.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        equipment TEXT,
        start_date TEXT,
        start_time TEXT,
        end_date TEXT,
        end_time TEXT,
        specific_details TEXT
    )
''')
conn.commit()

# ================= 2. 網頁標題 =================
st.set_page_config(page_title="實驗室機台預約系統", page_icon="🔬", layout="wide")
st.title("🔬 實驗室機台預約系統")

# ================= 3. 新增預約區塊 =================
st.header("📝 新增預約")

with st.form("reservation_form"):
    # 將排版改為左右兩排，方便對照開始與結束
    col1, col2 = st.columns(2)
    
    with col1:
        user_name = st.text_input("預約人姓名 / 學號", placeholder="請輸入姓名或學號")
        start_date = st.date_input("開始日期", min_value=date.today())
        start_time = st.time_input("開始時間", value=time(9, 0))
        
    with col2:
        equipment = st.selectbox("選擇機台", ["烘箱 (Oven)", "爐管 (Tube Furnace)", "CV (電容電壓量測)"])
        # 結束日期的最小值設為開始日期，防止選到過去的日子
        end_date = st.date_input("結束日期", min_value=start_date)
        end_time = st.time_input("結束時間", value=time(12, 0))

    st.markdown("---")
    st.subheader("⚙️ 機台專屬設定")
    
    specific_details = ""
    if equipment == "烘箱 (Oven)":
        target_temp = st.number_input("目標溫度 (°C)", min_value=25, max_value=300, value=100)
        share_oven = st.checkbox("是否開放同學共爐？(相同溫度下)")
        specific_details = f"溫度: {target_temp}°C | 開放共爐: {'是' if share_oven else '否'}"
    elif equipment == "爐管 (Tube Furnace)":
        gas_type = st.selectbox("通入氣體", ["N2 (氮氣)", "Ar (氬氣)", "O2 (氧氣)", "無"])
        max_temp = st.number_input("最高溫度 (°C)", min_value=25, max_value=1200, value=800)
        specific_details = f"氣氛: {gas_type} | 最高溫: {max_temp}°C"
    elif equipment == "CV (電容電壓量測)":
        sample_count = st.number_input("預計量測樣品數量 (片)", min_value=1, value=5)
        probe_type = st.selectbox("使用探針/治具類型", ["標準探針", "高頻探針", "自備治具"])
        specific_details = f"樣品數: {sample_count}片 | 治具: {probe_type}"

    submitted = st.form_submit_button("確認預約")
    
    if submitted:
        # 將日期與時間合併，才能精準判斷跨日與跨時
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)

        if not user_name:
            st.error("請輸入預約人姓名！")
        elif start_datetime >= end_datetime:
            st.error("結束時間必須晚於開始時間！（請檢查日期或時間）")
        else:
            # 寫入資料庫
            c.execute('''
                INSERT INTO reservations (user_name, equipment, start_date, start_time, end_date, end_time, specific_details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_name, equipment, str(start_date), str(start_time), str(end_date), str(end_time), specific_details))
            conn.commit()
            
            # 如果是跨日預約，顯示特別的提示訊息
            if start_date != end_date:
                st.success(f"✅ 跨日預約成功！ {user_name} 已預約 {equipment}，從 {start_date} {start_time.strftime('%H:%M')} 到 {end_date} {end_time.strftime('%H:%M')}。")
            else:
                st.success(f"✅ 成功預約！ {user_name} 已預約 {equipment} ({start_date})。")

# ================= 4. 預約紀錄總覽 =================
st.markdown("---")
st.header("📅 目前預約總覽")

df = pd.read_sql_query("SELECT * FROM reservations ORDER BY start_date DESC, start_time ASC", conn)

if not df.empty:
    df.columns = ["預約編號", "預約人", "機台", "開始日期", "開始時間", "結束日期", "結束時間", "機台設定與備註"]
    st.dataframe(df.drop(columns=["預約編號"]), use_container_width=True)
else:
    st.info("目前還沒有任何預約紀錄。")