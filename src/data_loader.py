import sys
from pathlib import Path

# プロジェクトルート設定
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime

from config.settings import GITHUB_CONFIG


try:
    from src.github_api import GitHubAPI
except ImportError:
    class GitHubAPI:
        def __init__(self):
            self.headers = {'User-Agent': 'PrefectureCitySelector/33.0'}
            self.timeout = 30
        
        def download_file(self, url):
            try:
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                st.error(f"ネットワークエラー: {str(e)}")
                return None

try:
    from src.gis_handler import GISHandler
except ImportError:
    class GISHandler:
        def __init__(self):
            pass
        
        def is_gis_available(self):
            return False

try:
    from src.utils import SessionStateManager
except ImportError:
    class SessionStateManager:
        def init_session_state(self):
            session_keys = [
                'prefecture_data', 'prefecture_codes', 'city_codes', 'data_loaded',
                'current_url', 'selected_prefecture', 'selected_city',
                'selected_file_path', 'area_data', 'selected_oaza', 'selected_chome',
                'folder_path'
            ]
            
            for key in session_keys:
                if key not in st.session_state:
                    if key in ['prefecture_data', 'prefecture_codes', 'city_codes', 'area_data']:
                        st.session_state[key] = {}
                    elif key == 'data_loaded':
                        st.session_state[key] = False
                    else:
                        st.session_state[key] = ""

# ページクラスも同様にフォールバック
try:
    from pages.main_page import MainPage
except ImportError:
    # MainPageクラスを直接定義（上記のコードを使用）
    pass

try:
    from pages.data_management import DataManagementPage
except ImportError:
    # DataManagementPageクラスを直接定義
    pass

try:
    from pages.about_page import AboutPage  
except ImportError:
    # AboutPageクラスを直接定義
    pass

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

            prefecture_col = prefecture_cols[0]
            city_col = city_cols[0]

            for _, row in df.iterrows():
                prefecture = row.get(prefecture_col)
                city = row.get(city_col)
                code = row.get(code_col, '')

                if pd.notna(prefecture):
                    if prefecture not in prefecture_data:
                        prefecture_data[prefecture] = {}
                        if pd.notna(code):
                            prefecture_codes[prefecture] = str(code)[:2]

                    if pd.notna(city):
                        full_code = str(code) if pd.notna(code) else '999999'
                        prefecture_code = full_code[:2]
                        city_code = full_code[2:5] if len(full_code) >= 5 else '999'

                        prefecture_data[prefecture][city] = {
                            'full_code': full_code,
                            'city_code': city_code
                        }

                        city_codes[f"{prefecture}_{city}"] = {
                            'prefecture_code': prefecture_code,
                            'city_code': city_code,
                            'full_code': full_code
                        }

            # セッション状態に保存
            st.session_state.prefecture_data = prefecture_data
            st.session_state.prefecture_codes = prefecture_codes
            st.session_state.city_codes = city_codes
            st.session_state.data_loaded = True

            # 統計情報を表示
            total_prefectures = len(prefecture_data)
            total_cities = sum(len(cities) for cities in prefecture_data.values())
            st.success(f"📊 読み込み完了: {total_prefectures}都道府県, {total_cities}市区町村")

            return True

        except Exception as e:
            st.error(f"データ整理エラー: {str(e)}")
            return False

    def run(self):
        """アプリケーションを実行"""
        # シンプルなページ選択
        st.sidebar.title("🏛️ ナビゲーション")
        
        selected_page = st.sidebar.selectbox(
            "ページを選択", 
            ["🎯 メイン", "📊 データ管理", "ℹ️ 情報"]
        )

        # ページを表示
        if selected_page == "🎯 メイン":
            self._render_main_page()
        elif selected_page == "📊 データ管理":
            self._render_data_page()
        else:
            self._render_about_page()

        # サイドバー情報表示
        self._render_sidebar_info()

    def _render_main_page(self):
        """メインページを直接描画"""
        if MainPage:
            page = MainPage(self)
            page.render()
        else:
            # フォールバック：シンプルなメインページ
            st.title("🏛️ 都道府県・市区町村選択ツール v33.0")
            st.write("メインページを読み込み中...")

    def _render_data_page(self):
        """データ管理ページを直接描画"""
        if DataManagementPage:
            page = DataManagementPage(self)
            page.render()
        else:
            st.title("📊 データ管理")
            st.write("データ管理ページを読み込み中...")

    def _render_about_page(self):
        """情報ページを直接描画"""
        if AboutPage:
            page = AboutPage(self)
            page.render()
        else:
            st.title("ℹ️ アプリケーション情報")
            st.write("情報ページを読み込み中...")

    def _render_sidebar_info(self):
        """サイドバー情報を表示"""
        try:
            from components.sidebar import SidebarInfo
            sidebar = SidebarInfo()
            sidebar.render()
        except ImportError:
            # フォールバック：シンプルなサイドバー情報
            if st.session_state.get('data_loaded', False):
                st.sidebar.markdown("---")
                st.sidebar.header("📊 現在のデータ")
                st.sidebar.write("✅ データ読み込み済み")

    def run(self):
        """アプリケーションを実行"""
        # サイドバーでページ選択
        st.sidebar.title("🏛️ ナビゲーション")

        pages = {
            "🎯 メイン": MainPage,
            "🗺️ 小字抽出": KozuPage,  # 新しいページを追加
            "📊 データ管理": DataManagementPage,
            "ℹ️ 情報": AboutPage
        }

        selected_page = st.sidebar.selectbox("ページを選択", list(pages.keys()))

        # 選択されたページを表示
        try:
            page_class = pages[selected_page]
            page = page_class(self)
            page.render()
        except Exception as e:
            st.error(f"ページ表示エラー: {str(e)}")
            st.info("メインページに戻ってください")

        # サイドバー情報表示
        self._render_sidebar_info()
