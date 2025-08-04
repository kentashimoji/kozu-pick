# -*- coding: utf-8 -*-

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).resolve().parent.parent  # 2階層上
sys.path.insert(0, str(project_root))


import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime
from config.settings import GITHUB_CONFIG
from src.github_api import GitHubAPI
from src.gis_handler import GISHandler
from src.utils import SessionStateManager
from pages.main_page import MainPage
from pages.data_management import DataManagementPage
from pages.about_page import AboutPage

class PrefectureCitySelector:
    def __init__(self):
        self.session_manager = SessionStateManager()
        self.github_api = GitHubAPI()
        self.gis_handler = GISHandler()
        self.session_manager.init_session_state()

    def load_data_from_github(self, url):
        """GitHubからデータを読み込み"""
        try:
            if not url:
                st.error("URLを入力してください")
                return False

            if "raw.githubusercontent.com" not in url:
                st.warning("GitHub Raw URLではないようです。")

            # プログレスバーを表示
            progress_bar = st.progress(0)
            status_text = st.empty()

            # データをダウンロード
            status_text.text("データをダウンロードしています...")
            progress_bar.progress(25)

            response = self.github_api.download_file(url)
            if not response:
                return False

            progress_bar.progress(50)
            status_text.text("ファイルを解析しています...")

            # ファイル読み込み処理
            df = self._process_file_data(response, url)
            if df is None:
                return False

            progress_bar.progress(75)
            status_text.text("データを処理しています...")

            # データ整理
            success = self._organize_prefecture_data(df)

            if success:
                progress_bar.progress(100)
                status_text.text("✅ データの読み込みが完了しました！")
                st.session_state.current_url = url
                return True

            return False

        except Exception as e:
            st.error(f"データの読み込みに失敗しました: {str(e)}")
            return False

    def _process_file_data(self, response, url):
        """ファイルデータを処理"""
        try:
            if url.lower().endswith('.csv'):
                return pd.read_csv(BytesIO(response.content), encoding='utf-8-sig')
            else:
                excel_data = BytesIO(response.content)
                return pd.read_excel(excel_data)
        except Exception as e:
            st.error(f"ファイル処理エラー: {str(e)}")
            return None

    def _organize_prefecture_data(self, df):
        """都道府県データを整理"""
        # データ整理ロジック（元のコードから抽出）
        try:
            prefecture_data = {}
            prefecture_codes = {}
            city_codes = {}

            # 列名検索
            prefecture_cols = [col for col in df.columns if '都道府県' in col and '漢字' in col]
            city_cols = [col for col in df.columns if '市区町村' in col and '漢字' in col]
            code_col = '団体コード'

            if not prefecture_cols or not city_cols:
                st.error(f"適切な列が見つかりません。利用可能な列: {list(df.columns)}")
                return False

            # データ処理ロジック（省略 - 元のコードと同じ）
            # ...

            # セッション状態に保存
            st.session_state.prefecture_data = prefecture_data
            st.session_state.prefecture_codes = prefecture_codes
            st.session_state.city_codes = city_codes
            st.session_state.data_loaded = True

            return True

        except Exception as e:
            st.error(f"データ整理エラー: {str(e)}")
            return False

    def run(self):
        """アプリケーションを実行"""
        # サイドバーでページ選択
        st.sidebar.title("🏛️ ナビゲーション")

        pages = {
            "🎯 メイン": MainPage,
            "📊 データ管理": DataManagementPage,
            "ℹ️ 情報": AboutPage
        }

        selected_page = st.sidebar.selectbox("ページを選択", list(pages.keys()))

        # 選択されたページを表示
        page_class = pages[selected_page]
        page = page_class(self)
        page.render()

        # サイドバー情報表示
        self._render_sidebar_info()

    def _render_sidebar_info(self):
        """サイドバー情報を表示"""
        from components.sidebar import SidebarInfo
        sidebar = SidebarInfo()
        sidebar.render()
