# -*- coding: utf-8 -*-
"""
都道府県・市区町村選択ツール + 小字データ抽出 v33.0
"""

import sys
from pathlib import Path


# プロジェクトルート設定
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

#from src.sample_a import sample
from config.settings import APP_CONFIG
from src.data_loader import PrefectureCitySelector


# ページ設定
st.set_page_config(
    page_title=APP_CONFIG["title"],
    page_icon=APP_CONFIG["icon"],
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["sidebar_state"]
)

def main():
	app = PrefectureCitySelector()
	app.run()

if __name__ == "__main__":
	main()
