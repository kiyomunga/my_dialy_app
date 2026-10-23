import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.title("My Diary App 📓")

# クラウドDBへの接続
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0).dropna(how="all")

# --- 1. 日次ログの入力モジュール ---
st.header("📝 新しいログの記録")
with st.form("input_form", clear_on_submit=True):
    entry_date = st.date_input("日付", datetime.date.today())
    entry_title = st.text_input("タイトル（※重要な出来事があった日のみ入力）")
    entry_content = st.text_area("内容（※必須）")
    submitted = st.form_submit_button("データベースにコミット")

    if submitted and entry_content.strip() != "":
        new_data = pd.DataFrame({
            'date': [entry_date.strftime('%Y-%m-%d')],
            'title': [entry_title],
            'content': [entry_content]
        })
        updated_df = pd.concat([df, new_data], ignore_index=True)
        conn.update(data=updated_df)
        st.success("クラウドDBに保存しました。")
        st.rerun()
    elif submitted:
        st.error("エラー：内容が入力されていません。")

# --- 2. 検索・抽出モジュール ---
st.header("🔍 ログの静的解析")
col1, col2 = st.columns(2)
with col1: search_month = st.text_input("年月フィルタ (例: 2026-10)")
with col2: search_keyword = st.text_input("キーワード")

# フィルタリング処理（クエリ実行）
filtered_df = df.copy()
if search_month: 
    filtered_df = filtered_df[filtered_df['date'].str.contains(search_month, na=False)]
if search_keyword: 
    filtered_df = filtered_df[filtered_df['content'].str.contains(search_keyword, na=False) | filtered_df['title'].str.contains(search_keyword, na=False)]

# 【追加パッチ】検索クエリがない場合は、タイトル付きの行のみに絞り込む
is_searching = bool(search_month or search_keyword)
if not is_searching:
    filtered_df = filtered_df[
        filtered_df['title'].notna() & 
        (filtered_df['title'].astype(str).str.strip() != "")
    ]

# --- 3. 出力モジュール ---
st.subheader(f"抽出件数: {len(filtered_df)} 件")
for _, row in filtered_df.sort_values('date', ascending=False).iterrows():
    title_text = f"🔥 {row['title']}" if pd.notna(row['title']) and str(row['title']).strip() != "" else "Daily Log"
    with st.expander(f"{row['date']} | {title_text}"):
        st.write(row['content'])