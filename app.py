import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date, time

# ================= 網頁基本設定 =================
st.set_page_config(page_title="實驗室機台預約系統", page_icon="🔬", layout="wide")
st.title("🔬 實驗室機台預約系統 (雲端版)")

# ================= 1. 連線至 Google Sheets =================
try:
    # 這裡會自動去讀取 Streamlit Secrets 裡面設定的金鑰與網址
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 已經加上 ttl=0，強制每次都抓取試算表最新資料
    df = conn.read(worksheet="工作表1", ttl=0)
except Exception as e:
    st.error("無法連線到 Google Sheets。請確認 Streamlit Secrets 金鑰設定是否正確，並確認已將機器人 Email 加入試算表編輯者！")
    st.stop()

# ================= 2. 新增預約區塊 =================
st.header("📝 新增預約")

with st.form("reservation_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        user_name = st.text_input("預約人姓名 / 學號", placeholder="請輸入姓名或學號")
        start_date = st.date_input("開始日期", min_value=date.today())
        start_time = st.time_input("開始時間", value=time(9, 0))
        
    with col2:
        equipment = st.selectbox("選擇機台", ["烘箱 (Oven)", "爐管 (Tube Furnace)", "CV (電容電壓量測)"])
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
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)

        if not user_name:
            st.error("請輸入預約人姓名！")
        elif start_datetime >= end_datetime:
            st.error("結束時間必須晚於開始時間！（請檢查日期或時間）")
        else:
            # 準備新寫入的一筆資料
            new_row = pd.DataFrame([{
                "預約人": user_name,
                "機台": equipment,
                "開始日期": str(start_date),
                "開始時間": str(start_time),
                "結束日期": str(end_date),
                "結束時間": str(end_time),
                "機台設定與備註": specific_details
            }])
            
            # 將新資料加到原本的表格下方
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # 覆寫回 Google Sheets
            conn.update(worksheet="工作表1", data=updated_df)
            
            # 清除快取，確保下一秒畫面重整時能抓到最新資料
            st.cache_data.clear()
            st.success("✅ 預約成功！資料已同步至實驗室 Google 試算表。")
            st.rerun()

# ================= 3. 預約紀錄總覽 =================
st.markdown("---")
st.header("📅 目前預約總覽")

if not df.empty and len(df.columns) >= 7:
    # 根據開始日期與時間進行排序 (新預約在上)
    df_sorted = df.sort_values(by=['開始日期', '開始時間'], ascending=[False, True])
    st.dataframe(df_sorted, use_container_width=True)
else:
    st.info("目前雲端試算表中還沒有任何預約紀錄。")
