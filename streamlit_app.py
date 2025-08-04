#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
都道府県・市区町村選択ツール v33.0 (Streamlit Cloud対応版)
メインアプリケーション
"""
import sys
from pathlib import Path

# プロジェクトルート
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


import streamlit as st
from src.data_loader import PrefectureCitySelector
from config.config import APP_CONFIG

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# これで正常にインポート
    try:
        from config.config import APP_CONFIG
        from src.data_loader import PrefectureCitySelector
    except ImportError as e:
        st.error(f"インポートエラー: {e}")
        st.stop()


# ページ設定
st.set_page_config(
    page_title=APP_CONFIG["title"],
    page_icon=APP_CONFIG["icon"],
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["sidebar_state"]
)

def main():
    """メイン関数"""
    if not IMPORTS_SUCCESS:
        st.title("⚠️ アプリケーション初期化エラー")
        st.error("必要なモジュールをインポートできませんでした。")
        
        # デバッグ情報
        with st.expander("デバッグ情報を表示"):
            st.write(f"**プロジェクトルート:** {project_root}")
            st.write(f"**Pythonパス (最初の3つ):**")
            for i, path in enumerate(sys.path[:3]):
                st.write(f"  [{i}]: {path}")
        
        return
    
    try:
        app = PrefectureCitySelector()
        app.run()
    except Exception as e:
        st.error(f"アプリケーション実行エラー: {str(e)}")
        st.info("ページを再読み込みしてください。")

if __name__ == "__main__":
    main()
