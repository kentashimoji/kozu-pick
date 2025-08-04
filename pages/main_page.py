# -*- coding: utf-8 -*-

import sys
from pathlib import Path


# プロジェクトルート
project_root = Path(__file__).resolve().parent.parent  # 2階層上
sys.path.insert(0, str(project_root))


import streamlit as st
from datetime import datetime
from components.selectors import PrefectureSelector, CitySelector


class MainPage:
    def __init__(self, app):
        self.app = app

    def render(self):
        """メインページを描画"""
        st.title("🏛️ 都道府県・市区町村選択ツール v33.0")

        self._render_header()
        self._render_data_source_section()

        if st.session_state.data_loaded and st.session_state.prefecture_data:
            self._render_selection_section()

    def _render_header(self):
        """ヘッダー部分を描画"""
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("**GitHub ExcelファイルからデータをダウンロードしてWebアプリケーションを作成**")
        with col2:
            st.metric("バージョン", "33.0")
        with col3:
            st.metric("プラットフォーム", "Streamlit + GitHub")

        st.markdown("---")

    def _render_data_source_section(self):
        """データソース設定セクション"""
        st.header("📡 データソース設定")

        from config.settings import GITHUB_CONFIG
        default_url = GITHUB_CONFIG["default_url"]

        url = st.text_input(
            "GitHub ExcelファイルURL:",
            value=st.session_state.current_url or default_url,
            help="GitHubでファイルを開き、'Raw'ボタンをクリックした時のURLを入力してください"
        )

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 データを読み込み", type="primary"):
                self.app.load_data_from_github(url)

        with col2:
            if st.button("🗑️ データをクリア"):
                self._clear_data()

    def _render_selection_section(self):
        """地域選択セクション"""
        st.markdown("---")
        st.header("🎯 地域選択")

        col1, col2 = st.columns(2)

        with col1:
            prefecture_selector = PrefectureSelector()
            prefecture_selector.render()

        with col2:
            city_selector = CitySelector()
            city_selector.render()

        # 選択結果表示
        if st.session_state.selected_prefecture and st.session_state.selected_city:
            self._render_results()

    def _clear_data(self):
        """データをクリア"""
        keys_to_clear = [
            'prefecture_data', 'prefecture_codes', 'city_codes', 'data_loaded',
            'current_url', 'selected_prefecture', 'selected_city',
            'selected_file_path', 'area_data', 'selected_oaza', 'selected_chome'
        ]

        for key in keys_to_clear:
            if key in st.session_state:
                if key.endswith('_data') or key.endswith('_codes'):
                    st.session_state[key] = {}
                elif key == 'data_loaded':
                    st.session_state[key] = False
                else:
                    st.session_state[key] = ""

        st.success("データをクリアしました")
        st.experimental_rerun()

    def _render_results(self):
        """選択結果を表示"""
        st.markdown("---")
        st.header("📍 選択結果")

        # 結果表示ロジック
        # （元のコードから抽出）
