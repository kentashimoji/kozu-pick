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

# 安全なインポート
try:
    from config.settings import APP_CONFIG
    from src.data_loader import PrefectureCitySelector
    IMPORTS_SUCCESS = True
except ImportError as e:
    st.error(f"インポートエラー: {e}")
    IMPORTS_SUCCESS = False
    
    # フォールバック設定
    APP_CONFIG = {
        "title": "都道府県・市区町村選択ツール + 小字抽出 v33.0",
        "icon": "🏛️",
        "layout": "wide",
        "sidebar_state": "expanded"
    }

# ページ設定
st.set_page_config(
    page_title=APP_CONFIG["title"],
    page_icon=APP_CONFIG["icon"],
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["sidebar_state"]
)

def main():
    """メインアプリケーション"""
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
