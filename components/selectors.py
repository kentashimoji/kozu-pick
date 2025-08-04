# -*- coding: utf-8 -*-

"""
選択UIコンポーネント
"""
import sys
from pathlib import Path

# プロジェクトルート
project_root = Path(__file__).resolve().parent.parent  # 2階層上
sys.path.insert(0, str(project_root))

import streamlit as st


class PrefectureSelector:
    def render(self):
        """都道府県選択UI"""
        if not st.session_state.prefecture_data:
            st.selectbox(
                "都道府県を選択してください:",
                ["データを読み込んでください"],
                disabled=True
            )
            return

        prefectures = list(st.session_state.prefecture_data.keys())
        prefecture_options = [f"{p} ({len(st.session_state.prefecture_data[p])}市区町村)"
                            for p in prefectures]

        selected_prefecture_display = st.selectbox(
            "都道府県を選択してください:",
            ["選択してください"] + prefecture_options,
            key="prefecture_select"
        )

        if selected_prefecture_display != "選択してください":
            prefecture_name = selected_prefecture_display.split(' (')[0]
            st.session_state.selected_prefecture = prefecture_name

class CitySelector:
    def render(self):
        """市区町村選択UI"""
        if not st.session_state.selected_prefecture:
            st.selectbox(
                "市区町村を選択してください:",
                ["まず都道府県を選択してください"],
                disabled=True
            )
            return

        cities_dict = st.session_state.prefecture_data[st.session_state.selected_prefecture]
        cities = list(cities_dict.keys())

        selected_city = st.selectbox(
            "市区町村を選択してください:",
            ["選択してください"] + cities,
            key="city_select"
        )

        if selected_city != "選択してください":
            st.session_state.selected_city = selected_city
