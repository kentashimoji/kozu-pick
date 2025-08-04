#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
都道府県・市区町村選択ツール v33.0 (Streamlit Cloud対応版)
メインアプリケーション
"""
# パス設定
current_file = Path(__file__).resolve()
project_root = current_file.parent


import sys
from pathlib import Path
import streamlit as st
from src.data_loader import PrefectureCitySelector
from config.settings import APP_CONFIG

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# これで正常にインポート
    try:
        from config.settings import APP_CONFIG
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
    try:
        app = PrefectureCitySelector()
        app.run()
    except Exception as e:
        st.error(f"アプリケーションエラー: {str(e)}")
        st.info("ページを再読み込みしてください。")

if __name__ == "__main__":
    main()
