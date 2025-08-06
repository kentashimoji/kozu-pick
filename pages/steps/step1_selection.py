#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pages/steps/step1_selection.py - Step1: 都道府県・市区町村選択
"""

import streamlit as st

class Step1Selection:
    def __init__(self, app):
        self.app = app
    
    def render(self):
        """Step1を描画"""
        st.header("1️⃣ 都道府県・市区町村選択")
        st.markdown("**指定されたExcelファイルからプルダウンを構成**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_prefecture_selection()
        
        with col2:
            self._render_city_selection()
        
        # Step1完了表示
        if st.session_state.step_completed['step1']:
            self._render_completion_status()
    
    def _render_prefecture_selection(self):
        """都道府県選択を描画"""
        prefecture_data = st.session_state.get('prefecture_data', {})
        
        if not prefecture_data:
            st.selectbox(
                "都道府県を選択してください:",
                ["データを読み込んでください"],
                disabled=True
            )
            return
        
        prefectures = list(prefecture_data.keys())
        prefecture_options = [f"{pref} ({len(prefecture_data[pref])}市区町村)" for pref in prefectures]
        
        # 現在の選択を保持
        current_prefecture = st.session_state.get('selected_prefecture', '')
        prefecture_index = 0
        if current_prefecture:
            for i, option in enumerate(prefecture_options):
                if option.startswith(current_prefecture):
                    prefecture_index = i + 1
                    break
        
        selected_prefecture_display = st.selectbox(
            "都道府県を選択してください:",
            ["選択してください"] + prefecture_options,
            index=prefecture_index,
            key="step1_prefecture"
        )
        
        if selected_prefecture_display != "選択してください":
            prefecture_name = selected_prefecture_display.split(' (')[0]
            
            # 都道府県が変更された場合の処理
            if st.session_state.get('selected_prefecture') != prefecture_name:
                self._reset_from_prefecture_change()
                st.session_state.selected_prefecture = prefecture_name
                st.rerun()
    
    def _render_city_selection(self):
        """市区町村選択を描画"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        
        if not selected_prefecture:
            st.selectbox(
                "市区町村を選択してください:",
                ["まず都道府県を選択してください"],
                disabled=True
            )
            return
        
        prefecture_data = st.session_state.get('prefecture_data', {})
        cities_dict = prefecture_data.get(selected_prefecture, {})
        cities = list(cities_dict.keys())
        
        # 現在の選択を保持
        current_city = st.session_state.get('selected_city', '')
        city_index = 0
        if current_city and current_city in cities:
            city_index = cities.index(current_city) + 1
        
        selected_city = st.selectbox(
            "市区町村を選択してください:",
            ["選択してください"] + cities,
            index=city_index,
            key="step1_city"
        )
        
        if selected_city != "選択してください":
            # 市区町村が変更された場合の処理
            if st.session_state.get('selected_city') != selected_city:
                self._handle_city_selection(selected_city)
    
    def _handle_city_selection(self, selected_city):
        """市区町村選択時の処理"""
        # 後続ステップをリセット
        self._reset_subsequent_steps()
        
        # 新しい市区町村を設定
        st.session_state.selected_city = selected_city
        st.session_state.step_completed['step1'] = True
        
        # Step2のデータを自動読み込み
        self._auto_load_step2_data()
        st.rerun()
    
    def _auto_load_step2_data(self):
        """Step2用のデータを自動読み込み"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        if not (selected_prefecture and selected_city):
            return
        
        # コード情報を取得
        prefecture_codes = st.session_state.get('prefecture_codes', {})
        city_codes = st.session_state.get('city_codes', {})
        
        prefecture_code = prefecture_codes.get(selected_prefecture, "")
        city_key = f"{selected_prefecture}_{selected_city}"
        city_info = city_codes.get(city_key, {})
        city_code = city_info.get('city_code', "")
        
        if prefecture_code and city_code:
            # 読み込み試行フラグを設定
            st.session_state.gis_load_attempted = True
            
            # 自動GIS読み込みを実行
            if hasattr(self.app, 'auto_load_gis_data'):
                with st.spinner(f"🔍 {selected_prefecture}{selected_city}のGISデータを自動読み込み中..."):
                    success = self.app.auto_load_gis_data(prefecture_code, city_code)
                
                # 読み込み結果を処理
                self._process_gis_load_result(success)
    
    def _process_gis_load_result(self, success):
        """GIS読み込み結果を処理"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        if success:
            area_data = st.session_state.get('area_data', {})
            area_count = len(area_data)
            
            if area_count > 0:
                st.success(f"✅ GISデータ読み込み完了: {area_count}個の大字")
                st.info("🎯 Step2（大字・丁目選択）の準備が完了しました")
            else:
                st.warning("⚠️ 大字・丁目データが見つかりませんでした")
        else:
            st.warning(f"⚠️ {selected_prefecture}{selected_city}の対応するGISファイルが見つかりませんでした")
            st.info("💡 Step2で手動読み込みを試行できます")
    
    def _render_completion_status(self):
        """完了状況を表示"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        st.success(f"✅ 選択完了: {selected_prefecture} {selected_city}")
        
        # コード情報表示
        prefecture_codes = st.session_state.get('prefecture_codes', {})
        city_codes = st.session_state.get('city_codes', {})
        
        prefecture_code = prefecture_codes.get(selected_prefecture, "")
        city_key = f"{selected_prefecture}_{selected_city}"
        city_info = city_codes.get(city_key, {})
        city_code = city_info.get('city_code', "")
        search_code = f"{prefecture_code}{city_code}"
        
        st.info(f"🔍 検索用5桁コード: **{search_code}**")
        
        # 詳細情報の表示（折りたたみ）
        with st.expander("📊 詳細情報"):
            st.write(f"**都道府県コード**: {prefecture_code}")
            st.write(f"**市区町村コード**: {city_code}")
            st.write(f"**完全団体コード**: {city_info.get('full_code', '')}")
            
            # GIS読み込み状況
            area_data = st.session_state.get('area_data', {})
            if area_data:
                st.write(f"**読み込み済み大字数**: {len(area_data)}")
                
                # 大字一覧（最初の5個まで）
                oaza_list = sorted(area_data.keys())
                display_oaza = oaza_list[:5]
                if len(oaza_list) > 5:
                    display_oaza.append(f"... 他{len(oaza_list)-5}個")
                st.write(f"**大字一覧**: {', '.join(display_oaza)}")
    
    def _reset_from_prefecture_change(self):
        """都道府県変更時のリセット処理"""
        reset_keys = [
            'selected_city', 'selected_oaza', 'selected_chome', 
            'input_chiban', 'area_data', 'target_shp_file', 'gis_load_attempted'
        ]
        
        for key in reset_keys:
            if key == 'area_data':
                st.session_state[key] = {}
            elif key == 'gis_load_attempted':
                st.session_state[key] = False
            else:
                st.session_state[key] = ""
        
        # ステップ完了状態をリセット
        for step_key in ['step1', 'step2', 'step3', 'step4']:
            st.session_state.step_completed[step_key] = False
    
    def _reset_subsequent_steps(self):
        """後続ステップのリセット処理"""
        reset_keys = [
            'selected_oaza', 'selected_chome', 'input_chiban', 'target_shp_file'
        ]
        
        for key in reset_keys:
            st.session_state[key] = ""
        
        # ステップ完了状態をリセット
        for step_key in ['step2', 'step3', 'step4']:
            st.session_state.step_completed[step_key] = False