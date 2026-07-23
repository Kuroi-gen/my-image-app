import streamlit as st
import pandas as pd
import os
import sqlite3
from PIL import Image

st.set_page_config(page_title="クラウド画像アプリ", layout="wide")

IMAGE_DIR = "images"
DB_PATH = "images.db"
os.makedirs(IMAGE_DIR, exist_ok=True)

# DB初期化と同期
@st.cache_resource
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            filepath TEXT,
            size_kb REAL
        )
    ''')
    conn.commit()

    # 既存ファイルの同期（起動時など）
    valid_extensions = (".png", ".jpg", ".jpeg")
    if os.path.exists(IMAGE_DIR):
        for file in os.listdir(IMAGE_DIR):
            if file.lower().endswith(valid_extensions):
                path = os.path.join(IMAGE_DIR, file)
                size_kb = round(os.path.getsize(path) / 1024, 1)
                c.execute('''
                    INSERT OR IGNORE INTO images (filename, filepath, size_kb)
                    VALUES (?, ?, ?)
                ''', (file, path, size_kb))
        conn.commit()
    conn.close()

init_db()

st.title("☁️ クラウド画像 検索・表示アプリ")

# --- 1. 画像のアップロード（スマホのカメラも起動可能） ---
with st.sidebar:
    st.header("📤 画像の登録")
    uploaded_file = st.file_uploader("写真をアップロード", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        save_path = os.path.join(IMAGE_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # データベースに登録
        size_kb = round(os.path.getsize(save_path) / 1024, 1)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT OR IGNORE INTO images (filename, filepath, size_kb)
            VALUES (?, ?, ?)
        ''', (uploaded_file.name, save_path, size_kb))
        conn.commit()
        conn.close()

        st.success(f"{uploaded_file.name} を保存しました！")

# --- 2. 検索バー ---
search_query = st.text_input("🔍 ファイル名で検索", "")

# --- 3. データベースからのデータ読み込み ---
def load_images_from_db(query=""):
    conn = sqlite3.connect(DB_PATH)
    if query:
        # 部分一致検索
        df = pd.read_sql_query(
            "SELECT id AS ID, filename AS ファイル名, filepath AS ファイルパス, size_kb AS 'サイズ(KB)' FROM images WHERE filename LIKE ?",
            conn,
            params=(f"%{query}%",)
        )
    else:
        df = pd.read_sql_query(
            "SELECT id AS ID, filename AS ファイル名, filepath AS ファイルパス, size_kb AS 'サイズ(KB)' FROM images",
            conn
        )
    conn.close()
    return df

df_filtered = load_images_from_db(search_query)

st.divider()

# --- 4. テーブル表示とプレビュー ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📋 登録済み画像一覧")
    if df_filtered.empty:
        st.warning("画像がありません。左のメニューからアップロードしてください。")
    else:
        st.caption("行をタップ（クリック）して選択してください")
        # 行選択機能付きのテーブル
        event = st.dataframe(
            df_filtered[["ID", "ファイル名", "サイズ(KB)"]],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        selected_rows = event.selection.rows

with col_right:
    st.subheader("🖼️ プレビュー")
    if not df_filtered.empty and 'selected_rows' in locals() and len(selected_rows) > 0:
        selected_row_data = df_filtered.iloc[selected_rows[0]]
        st.markdown(f"**{selected_row_data['ファイル名']}**")

        if os.path.exists(selected_row_data["ファイルパス"]):
            img = Image.open(selected_row_data["ファイルパス"])
            st.image(img, use_container_width=True)
        else:
            st.error("画像ファイルが見つかりません。")
    else:
        st.info("👈 左側のリストから画像を選択してください")
