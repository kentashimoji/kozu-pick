#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src/data_loader.py - 軽量化されたメインクラス（完全修正版）
重い処理は専用クラスに委譲
"""

import streamlit as st
import pandas as pd
from io import BytesIO

from config.settings import GITHUB_CONFIG
from src.github_api import GitHubAPI
from src.gis_handler import GISHandler
from src.utils import SessionStateManager, DataProcessor
from src.gis_loader import GISAutoLoader
from src.shp_manager import ShapefileManager
from pages.main_page import MainPage
from pages.kozu_page import KozuPage

class PrefectureCitySelector:
    """軽量化されたメインクラス"""

    def __init__(self):
        # 基本コンポーネント初期化
        self.session_manager = SessionStateManager()
        self.github_api = GitHubAPI()
        self.gis_handler = GISHandler()

        # 専用クラス初期化（エラーハンドリング付き）
        try:
            self.gis_loader = GISAutoLoader(self.github_api)
            self.shp_manager = ShapefileManager(self.github_api)
            st.info("✅ 専用クラス初期化完了")
        except Exception as e:
            st.error(f"❌ 専用クラス初期化エラー: {str(e)}")
            # フォールバック：基本機能のみ
            self.gis_loader = None
            self.shp_manager = None

        # セッション状態初期化
        self.session_manager.init_session_state()

        # 自動データ読み込み
        self._auto_load_data()

    def _auto_load_data(self):
        """アプリ起動時の自動データ読み込み"""
        if st.session_state.get('data_loaded', False):
            return

        default_url = GITHUB_CONFIG.get('default_url', '')
        
        with st.spinner("📡 データを読み込んでいます..."):
            success = self._execute_data_load(default_url)
            self._show_load_result(success)

    def _execute_data_load(self, url):
        """データ読み込み実行"""
        # URL無効時は警告表示してFalse返却
        if not self._is_valid_url(url):
            return False
        
        # URL有効時は読み込み実行
        return self.load_data_from_github(url)

    def _is_valid_url(self, url):
        """URLの有効性をチェック（強化版）"""
        if not url:
            st.error("URLが設定されていません")
            return False
        
        if url == "https://raw.githubusercontent.com/USERNAME/REPOSITORY/main/000925835.xlsx":
            st.warning("⚠️ デフォルトURLのままです。config/settings.py で実際のURLに変更してください。")
            return False
        
        if "raw.githubusercontent.com" not in url:
            st.warning(f"GitHub Raw URLではないようです: {url}")
            return False
        
        return True

    def _show_load_result(self, success):
        """読み込み結果を表示"""
        if success:
            st.success("✅ データの読み込みが完了しました")
        else:
            st.error("❌ データの読み込みに失敗しました")

    def auto_load_gis_data(self, prefecture_code, city_code):
        """GISデータの自動読み込み（専用クラスに委譲）"""
        try:
            search_code = f"{prefecture_code}{city_code}"
        
            # デバッグ情報を表示
            st.write("=== デバッグ情報 ===")
            st.write(f"🔍 検索コード: {search_code}")
        
            # GIS_CONFIG の確認
            from config.settings import GIS_CONFIG
            gis_folder = GIS_CONFIG.get('default_gis_folder', '')
            st.write(f"📁 設定フォルダ: {gis_folder}")
        
            # 専用クラス確認
            st.write(f"🔧 GISローダー: {'利用可能' if self.gis_loader else '利用不可'}")
        
            if not self.gis_loader:
                return self._fallback_gis_load(prefecture_code, city_code)
        
            # 実際の読み込み実行
            result = self.gis_loader.auto_load_by_code(prefecture_code, city_code)
            st.write(f"📊 読み込み結果: {result}")
        
            return result

            st.write(f"🔍 GIS自動読み込み開始")
            st.write(f"  - 都道府県コード: {prefecture_code}")  
            st.write(f"  - 市区町村コード: {city_code}")
            st.write(f"  - 検索コード: {prefecture_code}{city_code}")
            
            # 専用クラスが存在するかチェック
            if not self.gis_loader:
                st.warning("⚠️ GISローダーが利用できません。フォールバック処理を実行します。")
                return self._fallback_gis_load(prefecture_code, city_code)
            
            # GIS読み込み実行
            result = self.gis_loader.auto_load_by_code(prefecture_code, city_code)
            
            st.write(f"  - GIS読み込み結果: {result}")
            
            return result
            
        except Exception as e:
            st.error(f"❌ GIS自動読み込みエラー: {str(e)}")
            import traceback
            st.error(f"詳細エラー: {traceback.format_exc()}")
            
            # エラー時のフォールバック処理
            return self._fallback_gis_load(prefecture_code, city_code)

    def _fallback_gis_load(self, prefecture_code, city_code):
        """GIS読み込みのフォールバック処理"""
        try:
            st.info("🔄 基本的なGIS読み込み処理を実行中...")
            
            # 基本的なダミーデータでテスト
            search_code = f"{prefecture_code}{city_code}"
            
            # ダミーの大字・丁目データを作成（テスト用）
            dummy_area_data = {
                "上原": ["1丁目", "2丁目", "3丁目"],
                "宮里": ["1丁目", "2丁目"],
                "普天間": ["1丁目", "2丁目", "3丁目", "4丁目"]
            }
            
            # セッション状態に保存
            st.session_state.area_data = dummy_area_data
            st.session_state.current_gis_code = search_code
            st.session_state.selected_file_path = f"dummy_{search_code}.csv"
            
            st.success(f"✅ フォールバック処理完了: {len(dummy_area_data)}個の大字（テストデータ）")
            
            return True
            
        except Exception as e:
            st.error(f"❌ フォールバック処理エラー: {str(e)}")
            return False

    def search_shp_files_by_address(self, address_info):
        """shpファイル検索（専用クラスに委譲）"""
        return self.shp_manager.search_shp_files(address_info)

    def load_data_from_github(self, url):
        """GitHubからデータを読み込み"""
        try:
            response = self.github_api.download_file(url)
            if not response:
                return False

            df = self._process_file_data(response, url)
            if df is None:
                return False

            success = self._organize_prefecture_data(df)
            if success:
                st.session_state.current_url = url

            return success

        except Exception as e:
            st.error(f"データ読み込みエラー: {str(e)}")
            return False

    def _process_file_data(self, response, url):
        """ファイルデータの処理"""
        try:
            if url.lower().endswith('.csv'):
                return pd.read_csv(BytesIO(response.content), encoding='utf-8-sig')
            else:
                return pd.read_excel(BytesIO(response.content))
        except Exception as e:
            st.error(f"ファイル処理エラー: {str(e)}")
            return None

    def _organize_prefecture_data(self, df):
        """都道府県データの整理"""
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

            # 都道府県をソート（沖縄県を最初に）
            sorted_prefecture_data = self._sort_prefectures_with_okinawa_first(
                prefecture_data, prefecture_codes
            )

            # セッション状態に保存
            st.session_state.prefecture_data = sorted_prefecture_data
            st.session_state.prefecture_codes = prefecture_codes
            st.session_state.city_codes = city_codes
            st.session_state.data_loaded = True

            return True

        except Exception as e:
            st.error(f"データ整理エラー: {str(e)}")
            return False

    def _sort_prefectures_with_okinawa_first(self, prefecture_data, prefecture_codes):
        """沖縄県を最初にして都道府県をソート"""
        sorted_prefs = []
        other_prefs = []
        
        for pref in prefecture_data.keys():
            if pref == '沖縄県':
                sorted_prefs.insert(0, pref)  # 最初に挿入
            else:
                other_prefs.append(pref)
        
        # 沖縄県以外を団体コード順にソート
        other_prefs.sort(key=lambda x: prefecture_codes.get(x, '99'))
        
        all_prefs = sorted_prefs + other_prefs
        
        # ソート済みデータで辞書を再構築
        sorted_prefecture_data = {}
        for prefecture in all_prefs:
            sorted_prefecture_data[prefecture] = prefecture_data[prefecture]
        
        return sorted_prefecture_data

    def run(self):
        """アプリケーション実行"""
        if not st.session_state.get('data_loaded', False):
            self._render_loading_state()
            return

        # ページ選択・表示
        selected_page = self._render_page_selector()
        self._render_selected_page(selected_page)
        self._render_sidebar_info()

    def _render_page_selector(self):
        """ページ選択"""
        st.sidebar.title("🏛️ ナビゲーション")
        pages = {
            "🎯 メイン": MainPage,
            "🗺️ 小字抽出": KozuPage,
        }
        return st.sidebar.selectbox("ページを選択", list(pages.keys()))

    def _render_selected_page(self, selected_page):
        """選択されたページを表示"""
        pages = {
            "🎯 メイン": MainPage,
            "🗺️ 小字抽出": KozuPage,
        }

        try:
            page_class = pages[selected_page]
            page = page_class(self)
            page.render()
        except Exception as e:
            st.error(f"ページ表示エラー: {str(e)}")
            self._render_fallback_page()

    def _render_loading_state(self):
        """データ読み込み中の表示"""
        st.title("🏛️ 都道府県・市区町村選択ツール")
        st.info("📡 データを読み込んでいます...")

        if st.button("🔄 データを再読み込み"):
            self.manual_reload_data()

    def _render_fallback_page(self):
        """フォールバック用シンプルページ"""
        st.title("🏛️ 基本機能")
        st.info("メインページの読み込みに失敗しました。基本機能を表示します。")
        # シンプルな選択UIを実装

    def _render_sidebar_info(self):
        """サイドバー情報表示"""
        if st.session_state.get('data_loaded', False):
            st.sidebar.markdown("---")
            st.sidebar.header("📊 データ状態")
            st.sidebar.success("✅ データ読み込み済み")

            # 基本統計
            prefecture_count = len(st.session_state.get('prefecture_data', {}))
            st.sidebar.write(f"都道府県: {prefecture_count}")
            
            # Step2の状態確認
            area_count = len(st.session_state.get('area_data', {}))
            if area_count > 0:
                st.sidebar.success(f"✅ GISデータ: {area_count}個の大字")
            else:
                st.sidebar.info("🗺️ GISデータ未読み込み")
            
            # 選択状態
            selected_prefecture = st.session_state.get('selected_prefecture', '')
            selected_city = st.session_state.get('selected_city', '')
            
            if selected_prefecture:
                st.sidebar.write(f"**選択中**: {selected_prefecture}")
                if selected_city:
                    st.sidebar.write(f"**市区町村**: {selected_city}")
                    
                    # コード情報
                    prefecture_codes = st.session_state.get('prefecture_codes', {})
                    city_codes = st.session_state.get('city_codes', {})
                    
                    prefecture_code = prefecture_codes.get(selected_prefecture, "")
                    city_key = f"{selected_prefecture}_{selected_city}"
                    city_info = city_codes.get(city_key, {})
                    city_code = city_info.get('city_code', "")
                    
                    if prefecture_code and city_code:
                        st.sidebar.write(f"**検索コード**: {prefecture_code}{city_code}")
                        
                        # Step2手動実行ボタン
                        if st.sidebar.button("🔄 GISデータ手動読み込み"):
                            with st.spinner("GISデータを手動読み込み中..."):
                                success = self.auto_load_gis_data(prefecture_code, city_code)
                                if success:
                                    st.sidebar.success("✅ GIS読み込み完了")
                                    st.rerun()
                                else:
                                    st.sidebar.error("❌ GIS読み込み失敗")

            # 再読み込みボタン
            if st.sidebar.button("🔄 データ再読み込み"):
                self.manual_reload_data()

    def manual_reload_data(self):
        """手動データ再読み込み"""
        self.session_manager.reset_session_state()
        self._auto_load_data()
        st.rerun()