# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# プロジェクトルート設定
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

class SidebarInfo:
    def render(self):
        """サイドバー情報を表示"""
        # 基本データ情報
        if st.session_state.get('data_loaded', False):
            st.sidebar.markdown("---")
            st.sidebar.header("📊 都道府県データ")
            st.sidebar.write("✅ データ読み込み済み")

            if st.session_state.get('selected_prefecture'):
                st.sidebar.write(f"選択中: {st.session_state.selected_prefecture}")
                if st.session_state.get('selected_city'):
                    st.sidebar.write(f"市区町村: {st.session_state.selected_city}")

        # GISデータ情報
        if st.session_state.get('gdf') is not None:
            st.sidebar.markdown("---")
            st.sidebar.header("🗺️ GISデータ")
            gdf = st.session_state.gdf
            st.sidebar.write("✅ GISデータ読み込み済み")
            st.sidebar.write(f"レコード数: {len(gdf)}")

            # 大字の種類数
            if '大字名' in gdf.columns:
                oaza_count = gdf['大字名'].nunique()
                st.sidebar.write(f"大字数: {oaza_count}")

        # 抽出結果情報
        if st.session_state.get('extraction_results'):
            st.sidebar.markdown("---")
            st.sidebar.header("🎯 抽出結果")
            results = st.session_state.extraction_results
            st.sidebar.write(f"対象筆: {len(results['target'])}件")
            st.sidebar.write(f"周辺筆: {len(results['surrounding'])}件")

            conditions = results['conditions']
            st.sidebar.write(f"条件: {conditions['oaza']}")
            if conditions['chiban']:
                st.sidebar.write(f"地番: {conditions['chiban']}")

        st.sidebar.markdown("---")
        st.sidebar.markdown("**都道府県・市区町村選択ツール v33.0**")
        st.sidebar.markdown("+ 小字データ抽出機能")
        st.sidebar.markdown("Powered by Streamlit + GitHub + GeoPandas")
