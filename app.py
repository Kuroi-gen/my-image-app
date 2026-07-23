import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="クラウド画像アプリ", layout="wide")

IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

st.title("☁️ クラウド画像 検索・表示アプリ")

# --- 1. 画像のアップロード（スマホのカメラも起動可能） ---
with st.sidebar:
    st.header("📤 画像の登録")
    uploaded_file = st.file_uploader("写真をアップロード", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        save_path = os.path.join(IMAGE_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"{uploaded_file.name} を保存しました！")

# --- 2. 保存されている画像のデータ化 ---
def load_images():
    valid_extensions = (".png", ".jpg", ".jpeg")
    files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(valid_extensions)]
    data = []
    for i, file in enumerate(files):
        path = os.path.join(IMAGE_DIR, file)
        size_kb = round(os.path.getsize(path) / 1024, 1)
        data.append({"ID": i + 1, "ファイル名": file, "ファイルパス": path, "サイズ(KB)": size_kb})
    return pd.DataFrame(data)

df_all = load_images()

# --- 3. 検索バー ---
search_query = st.text_input("🔍 ファイル名で検索", "")
if not df_all.empty and search_query:
    df_filtered = df_all[df_all["ファイル名"].str.contains(search_query, case=False, na=False)]
else:
    df_filtered = df_all

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
        img = Image.open(selected_row_data["ファイルパス"])
        st.image(img, use_container_width=True)
    else:
        st.info("👈 左側のリストから画像を選択してください")
