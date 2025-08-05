#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pages/main_page.py - 4段階構成のメインページ（GIS読み込み対応修正版）
① 都道府県・市区町村選択（Excelから）
② 大字・丁目選択（5桁コードでファイル特定・読み込み）
③ 地番入力
④ shpファイル特定
"""

import streamlit as st
from datetime import datetime
import os
import re

try:
    from config.settings import APP_CONFIG, UI_CONFIG, MESSAGES, GIS_CONFIG
    from src.utils import StringHelper
except ImportError:
    # フォールバック設定
    APP_CONFIG = {"version": "33.0"}
    UI_CONFIG = {"show_debug_info": False}
    MESSAGES = {
        "select_prefecture": "都道府県を選択してください",
        "select_city": "市区町村を選択してください"
    }
    GIS_CONFIG = {"default_gis_folder": ""}

class MainPage:
    def __init__(self, app):
        self.app = app
        
        # セッション状態の初期化
        self._init_session_state()
    
    def _init_session_state(self):
        """セッション状態の初期化"""
        init_keys = {
            'selected_prefecture': "",
            'selected_city': "",
            'selected_oaza': "",
            'selected_chome': "",
            'input_chiban': "",
            'area_data': {},
            'target_shp_file': "",
            'current_gis_code': "",
            'gis_files_list': [],
            'gis_load_attempted': False,  # 追加：GIS読み込み試行フラグ
            'step_completed': {
                'step1': False,  # 都道府県・市区町村選択
                'step2': False,  # 大字・丁目選択
                'step3': False,  # 地番入力
                'step4': False   # shpファイル特定
            }
        }
        
        for key, default_value in init_keys.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def render(self):
        """メインページを描画"""
        st.title("🏛️ 都道府県・市区町村選択ツール v33.0")
        st.markdown("**4段階の住所特定システム**")
        
        # データ読み込み確認
        if not st.session_state.get('data_loaded', False):
            self._render_no_data_state()
            return
        
        # 進捗インジケーター
        self._render_progress_indicator()
        
        # Step 1: 都道府県・市区町村選択
        self._render_step1_prefecture_city()
        
        # Step 2: 大字・丁目選択（Step1完了後）
        if st.session_state.step_completed['step1']:
            self._render_step2_area_selection()
        
        # Step 3: 地番入力（Step2完了後）
        if st.session_state.step_completed['step2']:
            self._render_step3_chiban_input()
        
        # Step 4: shpファイル特定（Step3完了後）
        if st.session_state.step_completed['step3']:
            self._render_step4_shp_identification()
        
        # 最終結果表示
        if st.session_state.step_completed['step4']:
            self._render_final_result()
    
    def _render_no_data_state(self):
        """データ未読み込み時の表示"""
        st.warning("📋 データが読み込まれていません")
        st.info("アプリケーションの初期化を待っています...")
        
        if st.button("🔄 データを再読み込み"):
            if hasattr(self.app, 'manual_reload_data'):
                self.app.manual_reload_data()
            else:
                st.rerun()
    
    def _render_progress_indicator(self):
        """進捗インジケーターを表示"""
        st.markdown("### 📊 進捗状況")
        
        steps = [
            ("1️⃣", "都道府県・市区町村", st.session_state.step_completed['step1']),
            ("2️⃣", "大字・丁目", st.session_state.step_completed['step2']),
            ("3️⃣", "地番入力", st.session_state.step_completed['step3']),
            ("4️⃣", "shpファイル特定", st.session_state.step_completed['step4'])
        ]
        
        cols = st.columns(4)
        for i, (icon, title, completed) in enumerate(steps):
            with cols[i]:
                if completed:
                    st.success(f"{icon} {title} ✅")
                else:
                    st.info(f"{icon} {title}")
        
        st.markdown("---")
    
    def _render_step1_prefecture_city(self):
        """Step 1: 都道府県・市区町村選択"""
        st.header("1️⃣ 都道府県・市区町村選択")
        st.markdown("**指定されたExcelファイルからプルダウンを構成**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 都道府県選択
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
                    self._reset_from_step(1)
                    st.session_state.selected_prefecture = prefecture_name
                    st.rerun()
        
        with col2:
            # 市区町村選択
            selected_prefecture = st.session_state.get('selected_prefecture', '')
            
            if not selected_prefecture:
                st.selectbox(
                    "市区町村を選択してください:",
                    ["まず都道府県を選択してください"],
                    disabled=True
                )
            else:
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
                        self._reset_from_step(2)
                        st.session_state.selected_city = selected_city
                        st.session_state.step_completed['step1'] = True
                        
                        # 自動的にStep2のデータ読み込みを開始
                        self._auto_load_step2_data()
                        st.rerun()
        
        # Step1の完了状況表示
        if st.session_state.step_completed['step1']:
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
    
    def _auto_load_step2_data(self):
        """Step2用のデータを自動読み込み（修正版）"""
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
        """GIS読み込み結果を処理（新規追加）"""
        if success:
            area_data = st.session_state.get('area_data', {})
            area_count = len(area_data)
            
            if area_count > 0:
                st.success(f"✅ GISデータ読み込み完了: {area_count}個の大字")
                
                # 大字データがある場合は、最初の大字を自動選択（オプション）
                if not st.session_state.get('selected_oaza'):
                    first_oaza = sorted(area_data.keys())[0]
                    st.session_state.selected_oaza = first_oaza
                    st.info(f"💡 最初の大字「{first_oaza}」を自動選択しました")
                
                # Step2準備完了を表示
                st.info("🎯 Step2（大字・丁目選択）の準備が完了しました")
            else:
                st.warning("⚠️ 大字・丁目データが見つかりませんでした")
        else:
            selected_prefecture = st.session_state.get('selected_prefecture', '')
            selected_city = st.session_state.get('selected_city', '')
            st.warning(f"⚠️ {selected_prefecture}{selected_city}の対応するGISファイルが見つかりませんでした")
            st.info("💡 手動でGISデータの読み込みを試行できます")
    
    def _render_step2_area_selection(self):
        """Step 2: 大字・丁目選択（修正版）"""
        st.markdown("---")
        st.header("2️⃣ 大字・丁目選択")
        st.markdown("**5桁コードで特定されたファイルから大字・丁目を表示**")
        
        area_data = st.session_state.get('area_data', {})
        gis_load_attempted = st.session_state.get('gis_load_attempted', False)
        
        # GISデータ状態の表示
        if not area_data and not gis_load_attempted:
            st.info("⏳ GISデータの自動読み込みを待っています...")
            return
        elif not area_data and gis_load_attempted:
            st.warning("⚠️ 大字・丁目データが読み込まれていません")
            
            # 手動読み込みボタン
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 GISデータを手動読み込み"):
                    self._manual_reload_gis_data()
            
            with col2:
                if st.button("⏭️ ダミーデータで続行"):
                    self._use_dummy_area_data()
                    st.rerun()
            return
        
        # GISデータが存在する場合の処理
        st.success(f"✅ {len(area_data)}個の大字が利用可能です")
        
        # GISファイル情報の表示
        current_gis_code = st.session_state.get('current_gis_code', '')
        selected_file_path = st.session_state.get('selected_file_path', '')
        if current_gis_code or selected_file_path:
            with st.expander("📄 読み込み済みGISファイル情報"):
                if current_gis_code:
                    st.write(f"**検索コード**: {current_gis_code}")
                if selected_file_path:
                    st.write(f"**ファイル**: {selected_file_path}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 大字選択
            oaza_list = sorted(area_data.keys())
            
            current_oaza = st.session_state.get('selected_oaza', '')
            oaza_index = 0
            if current_oaza and current_oaza in oaza_list:
                oaza_index = oaza_list.index(current_oaza) + 1
            
            selected_oaza = st.selectbox(
                "大字を選択してください:",
                ["選択してください"] + oaza_list,
                index=oaza_index,
                key="step2_oaza"
            )
            
            if selected_oaza != "選択してください":
                if st.session_state.get('selected_oaza') != selected_oaza:
                    st.session_state.selected_oaza = selected_oaza
                    st.session_state.selected_chome = ""  # 丁目をリセット
                    st.rerun()
        
        with col2:
            # 丁目選択
            selected_oaza = st.session_state.get('selected_oaza', '')
            
            if not selected_oaza:
                st.selectbox(
                    "丁目を選択してください:",
                    ["まず大字を選択してください"],
                    disabled=True
                )
            else:
                chome_list = area_data.get(selected_oaza, [])
                
                if not chome_list or chome_list == ["丁目データなし"] or chome_list == ["データなし"]:
                    st.info("この大字には丁目データがありません")
                    st.selectbox(
                        "丁目を選択してください:",
                        ["丁目データなし"],
                        disabled=True
                    )
                    # 大字のみ選択でStep2完了
                    if not st.session_state.step_completed['step2']:
                        st.session_state.step_completed['step2'] = True
                        st.success("✅ 大字選択完了（丁目データなし）")
                        st.rerun()
                else:
                    current_chome = st.session_state.get('selected_chome', '')
                    chome_index = 0
                    if current_chome and current_chome in chome_list:
                        chome_index = chome_list.index(current_chome) + 1
                    
                    selected_chome = st.selectbox(
                        "丁目を選択してください:",
                        ["選択してください"] + chome_list,
                        index=chome_index,
                        key="step2_chome"
                    )
                    
                    if selected_chome != "選択してください":
                        if st.session_state.get('selected_chome') != selected_chome:
                            st.session_state.selected_chome = selected_chome
                            st.session_state.step_completed['step2'] = True
                            st.rerun()
        
        # Step2完了表示
        if st.session_state.step_completed['step2']:
            selected_oaza = st.session_state.get('selected_oaza', '')
            selected_chome = st.session_state.get('selected_chome', '')
            
            address_parts = [selected_oaza]
            if selected_chome and selected_chome not in ["丁目データなし", "データなし"]:
                address_parts.append(selected_chome)
            
            st.success(f"✅ 選択完了: {' '.join(address_parts)}")
    
    def _manual_reload_gis_data(self):
        """手動でGISデータを再読み込み（新規追加）"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        if not (selected_prefecture and selected_city):
            st.error("❌ 都道府県・市区町村が選択されていません")
            return
        
        # コード情報を取得
        prefecture_codes = st.session_state.get('prefecture_codes', {})
        city_codes = st.session_state.get('city_codes', {})
        
        prefecture_code = prefecture_codes.get(selected_prefecture, "")
        city_key = f"{selected_prefecture}_{selected_city}"
        city_info = city_codes.get(city_key, {})
        city_code = city_info.get('city_code', "")
        
        if prefecture_code and city_code:
            if hasattr(self.app, 'auto_load_gis_data'):
                with st.spinner("🔄 GISデータを手動読み込み中..."):
                    success = self.app.auto_load_gis_data(prefecture_code, city_code)
                
                if success:
                    area_count = len(st.session_state.get('area_data', {}))
                    st.success(f"✅ 手動読み込み完了: {area_count}個の大字")
                    st.rerun()
                else:
                    st.error("❌ 手動読み込みも失敗しました")
        else:
            st.error("❌ 検索コードが取得できません")
    
    def _use_dummy_area_data(self):
        """ダミー大字・丁目データを使用（新規追加）"""
        selected_city = st.session_state.get('selected_city', '')
        
        # 市区町村名に応じたダミーデータ
        if "那覇" in selected_city:
            dummy_data = {
                "那覇": ["1丁目", "2丁目", "3丁目"],
                "首里": ["1丁目", "2丁目", "3丁目", "4丁目", "5丁目"],
                "真嘉比": ["1丁目", "2丁目", "3丁目"],
                "泊": ["1丁目", "2丁目", "3丁目"],
                "久茂地": ["1丁目", "2丁目", "3丁目"]
            }
        elif "宜野湾" in selected_city:
            dummy_data = {
                "上原": ["1丁目", "2丁目", "3丁目"],
                "宮里": ["1丁目", "2丁目"],
                "普天間": ["1丁目", "2丁目", "3丁目", "4丁目"],
                "長田": ["1丁目", "2丁目"],
                "中原": ["1丁目", "2丁目", "3丁目"]
            }
        else:
            dummy_data = {
                "中央": ["1丁目", "2丁目", "3丁目"],
                "東": ["1丁目", "2丁目"],
                "西": ["1丁目", "2丁目"],
                "南": ["1丁目", "2丁目"],
                "北": ["1丁目", "2丁目"]
            }
        
        st.session_state.area_data = dummy_data
        st.session_state.gis_load_attempted = True
        st.warning(f"⚠️ ダミーデータを使用します（{len(dummy_data)}個の大字）")
    
    def _render_step3_chiban_input(self):
        """Step 3: 地番入力"""
        st.markdown("---")
        st.header("3️⃣ 地番入力")
        st.markdown("**地番を入力してください**")
        
        # 選択された住所の確認表示
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        selected_oaza = st.session_state.get('selected_oaza', '')
        selected_chome = st.session_state.get('selected_chome', '')
        
        current_address = f"{selected_prefecture}{selected_city}{selected_oaza}"
        if selected_chome and selected_chome not in ["丁目データなし", "データなし"]:
            current_address += selected_chome
        
        st.info(f"📍 現在の住所: **{current_address}**")
        
        # 地番入力フィールド
        current_chiban = st.session_state.get('input_chiban', '')
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            input_chiban = st.text_input(
                "地番を入力してください:",
                value=current_chiban,
                placeholder="例: 123-4, 45番地6, 78-9-10",
                help="地番は数字とハイフン、番地などの形式で入力してください"
            )
        
        with col2:
            if st.button("✅ 地番を確定"):
                if input_chiban.strip():
                    # 地番の形式チェック
                    if self._validate_chiban(input_chiban.strip()):
                        st.session_state.input_chiban = input_chiban.strip()
                        st.session_state.step_completed['step3'] = True
                        st.success(f"✅ 地番確定: {input_chiban.strip()}")
                        st.rerun()
                    else:
                        st.error("❌ 地番の形式が正しくありません")
                else:
                    st.error("❌ 地番を入力してください")
        
        # 地番入力例の表示
        with st.expander("📝 地番入力例"):
            st.markdown("""
            **有効な地番形式:**
            - `123-4` (基本的な地番)
            - `45番地6` (番地形式)  
            - `78-9-10` (枝番付き)
            - `100` (単一番号)
            - `5番地` (番地のみ)
            
            **注意事項:**
            - 数字、ハイフン(-)、番地の文字を使用
            - 全角・半角どちらでも可
            """)
        
        # Step3完了表示
        if st.session_state.step_completed['step3']:
            input_chiban = st.session_state.get('input_chiban', '')
            complete_address = f"{current_address}{input_chiban}"
            st.success(f"✅ 完全住所: **{complete_address}**")
    
    def _validate_chiban(self, chiban):
        """地番の形式をチェック"""
        if not chiban:
            return False
        
        # 地番の一般的なパターンをチェック
        patterns = [
            r'^\d+(-\d+)*$',  # 123-4-5形式
            r'^\d+番地\d*$',   # 123番地4形式
            r'^\d+$',         # 123形式
            r'^\d+番地$',     # 123番地形式
        ]
        
        for pattern in patterns:
            if re.match(pattern, chiban):
                return True
        
        return False
    
    def _render_step4_shp_identification(self):
        """Step 4: shpファイル特定"""
        st.markdown("---")
        st.header("4️⃣ shpファイル特定")
        st.markdown("**特定された住所情報から対象shpファイルを特定**")
        
        # 完全な住所情報を構築
        complete_address_info = self._build_complete_address_info()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📍 特定条件")
            
            for key, value in complete_address_info.items():
                if value and value != "なし":
                    if key == "検索コード":
                        st.write(f"**{key}**: `{value}`")
                    else:
                        st.write(f"**{key}**: {value}")
        
        with col2:
            if st.button("🔍 shpファイルを特定"):
                self._identify_target_shp()
        
        # shpファイル特定結果の表示
        target_shp = st.session_state.get('target_shp_file', '')
        if target_shp:
            st.success(f"✅ 特定されたshpファイル: **{target_shp}**")
            if not st.session_state.step_completed['step4']:
                st.session_state.step_completed['step4'] = True
                st.rerun()
            
            # ファイル詳細情報
            with st.expander("📄 ファイル詳細情報"):
                st.write(f"**ファイル名**: {target_shp}")
                st.write(f"**特定日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
                
                # ファイルパスの推定
                if complete_address_info:
                    estimated_path = self._estimate_shp_file_path(complete_address_info)
                    st.write(f"**推定パス**: {estimated_path}")
    
    def _build_complete_address_info(self):
        """完全な住所情報を構築"""
        selected_chome = st.session_state.get('selected_chome', '')
        if selected_chome in ["丁目データなし", "データなし", ""]:
            selected_chome = "なし"
        
        return {
            "都道府県": st.session_state.get('selected_prefecture', ''),
            "市区町村": st.session_state.get('selected_city', ''),
            "大字": st.session_state.get('selected_oaza', ''),
            "丁目": selected_chome,
            "地番": st.session_state.get('input_chiban', ''),
            "団体コード": self._get_full_code(),
            "検索コード": self._get_search_code()
        }
    
    def _get_full_code(self):
        """完全な団体コードを取得"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        if not (selected_prefecture and selected_city):
            return ""
        
        city_codes = st.session_state.get('city_codes', {})
        city_key = f"{selected_prefecture}_{selected_city}"
        city_info = city_codes.get(city_key, {})
        
        return city_info.get('full_code', '')
    
    def _get_search_code(self):
        """検索用5桁コードを取得"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        if not (selected_prefecture and selected_city):
            return ""
        
        prefecture_codes = st.session_state.get('prefecture_codes', {})
        city_codes = st.session_state.get('city_codes', {})
        
        prefecture_code = prefecture_codes.get(selected_prefecture, "")
        city_key = f"{selected_prefecture}_{selected_city}"
        city_info = city_codes.get(city_key, {})
        city_code = city_info.get('city_code', "")
        
        return f"{prefecture_code}{city_code}"
    
    def _identify_target_shp(self):
        """対象shpファイルを特定"""
        try:
            address_info = self._build_complete_address_info()
            
            # shpファイル名のパターンを生成
            shp_patterns = self._generate_shp_patterns(address_info)
            
            # 実際のファイル検索を試行
            if hasattr(self.app, 'search_shp_files_by_address'):
                with st.spinner("🔍 shpファイルを検索中..."):
                    found_files = self.app.search_shp_files_by_address(address_info)
                
                if found_files:
                    # 最も適切なファイルを選択
                    target_shp = found_files[0].get('name', '')
                    st.session_state.target_shp_file = target_shp
                    st.success(f"🎯 shpファイルを特定しました: {target_shp}")
                    
                    # 複数ファイルが見つかった場合の表示
                    if len(found_files) > 1:
                        with st.expander(f"📄 他の候補ファイル ({len(found_files)-1}個)"):
                            for i, file_info in enumerate(found_files[1:], 1):
                                st.write(f"{i}. {file_info.get('name', 'Unknown')}")
                    return
            
            # フォールバック：パターンベースの特定
            target_shp = self._select_best_shp_pattern(shp_patterns)
            
            if target_shp:
                st.session_state.target_shp_file = target_shp
                st.success(f"🎯 shpファイルを特定しました（パターンベース）: {target_shp}")
            else:
                st.warning("⚠️ 条件に一致するshpファイルが特定できませんでした")
                
                # デバッグ情報の表示
                with st.expander("🔧 デバッグ情報"):
                    st.write("**生成されたパターン:**")
                    for i, pattern in enumerate(shp_patterns, 1):
                        st.write(f"{i}. {pattern}")
                    
                    # 手動入力オプション
                    manual_shp = st.text_input(
                        "shpファイル名を手動入力:",
                        placeholder="例: 47201_那覇_1174.shp"
                    )
                    if st.button("手動設定") and manual_shp:
                        st.session_state.target_shp_file = manual_shp
                        st.success(f"✅ 手動設定完了: {manual_shp}")
                        st.rerun()
                
        except Exception as e:
            st.error(f"❌ shpファイル特定エラー: {str(e)}")
            
            # エラー時のフォールバック
            address_info = self._build_complete_address_info()
            fallback_shp = self._create_fallback_shp_name(address_info)
            st.session_state.target_shp_file = fallback_shp
            st.info(f"💡 フォールバックファイル名: {fallback_shp}")
    
    def _generate_shp_patterns(self, address_info):
        """shpファイル名のパターンを生成"""
        patterns = []
        
        # 基本情報
        search_code = address_info.get('検索コード', '')
        prefecture = address_info.get('都道府県', '')
        city = address_info.get('市区町村', '')
        oaza = address_info.get('大字', '')
        chome = address_info.get('丁目', '')
        chiban = address_info.get('地番', '')
        
        # パターン1: 最も詳細な住所ベース
        if all([search_code, oaza, chiban]):
            detailed_name = f"{search_code}_{oaza}"
            if chome and chome != "なし":
                detailed_name += f"_{chome}"
            detailed_name += f"_{chiban}.shp"
            patterns.append(detailed_name)
        
        # パターン2: 大字・丁目ベース
        if search_code and oaza:
            area_name = f"{search_code}_{oaza}"
            if chome and chome != "なし":
                area_name += f"_{chome}"
            area_name += ".shp"
            patterns.append(area_name)
        
        # パターン3: 市区町村名込み
        if search_code and city:
            city_name = f"{search_code}_{city.replace('市', '').replace('区', '').replace('町', '').replace('村', '')}"
            if oaza:
                city_name += f"_{oaza}"
            city_name += ".shp"
            patterns.append(city_name)
        
        # パターン4: 市区町村コードベース
        if search_code:
            patterns.extend([
                f"{search_code}_地籍.shp",
                f"{search_code}_筆.shp", 
                f"{search_code}.shp",
                f"cadastral_{search_code}.shp",
                f"parcel_{search_code}.shp"
            ])
        
        # パターン5: 都道府県コードベース（47201 → 47）
        if search_code and len(search_code) >= 2:
            prefecture_code = search_code[:2]
            patterns.extend([
                f"{prefecture_code}_{prefecture.replace('県', '').replace('府', '').replace('都', '')}.shp",
                f"{prefecture_code}_all.shp",
                f"{prefecture_code}.shp"
            ])
        
        return patterns
    
    def _select_best_shp_pattern(self, patterns):
        """最適なshpファイルパターンを選択"""
        # 実際の実装では、ここでファイルシステムやAPIを使って
        # 存在するファイルをチェックする
        
        # 優先度順に返す
        if patterns:
            return patterns[0]  # 最も詳細なパターンを優先
        
        return None
    
    def _create_fallback_shp_name(self, address_info):
        """フォールバック用のshpファイル名を作成"""
        search_code = address_info.get('検索コード', '99999')
        city = address_info.get('市区町村', 'Unknown')
        chiban = address_info.get('地番', '1')
        
        # 基本的なフォールバック名
        fallback_name = f"{search_code}_{city}_{chiban}.shp"
        return fallback_name
    
    def _estimate_shp_file_path(self, address_info):
        """shpファイルパスを推定"""
        gis_folder = GIS_CONFIG.get('default_gis_folder', '')
        target_shp = st.session_state.get('target_shp_file', '')
        
        if gis_folder and target_shp:
            # GitHub Raw URLの場合
            if 'github' in gis_folder.lower():
                return f"{gis_folder}/{target_shp}"
            else:
                return f"{gis_folder}/{target_shp}"
        
        return "パス推定不可"
    
    def _render_final_result(self):
        """最終結果を表示"""
        st.markdown("---")
        st.header("🎯 最終結果")
        st.markdown("**4段階の住所特定が完了しました**")
        
        address_info = self._build_complete_address_info()
        target_shp = st.session_state.get('target_shp_file', '')
        
        # 結果サマリー
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📍 完全な住所情報")
            
            # 完全住所の構築
            complete_address_parts = []
            for key in ["都道府県", "市区町村", "大字", "丁目", "地番"]:
                value = address_info.get(key, '')
                if value and value != "なし":
                    complete_address_parts.append(value)
            
            complete_address = "".join(complete_address_parts)
            st.success(f"**完全住所**: {complete_address}")
            
            # 詳細情報の表示
            st.markdown("**詳細情報:**")
            for key, value in address_info.items():
                if key not in ['団体コード', '検索コード'] and value:
                    if value == "なし":
                        st.write(f"- **{key}**: *指定なし*")
                    else:
                        st.write(f"- **{key}**: {value}")
            
            # コード情報
            st.markdown("**識別コード:**")
            team_code = address_info.get('団体コード', '')
            search_code = address_info.get('検索コード', '')
            if team_code:
                st.write(f"- **団体コード**: `{team_code}`")
            if search_code:
                st.write(f"- **検索コード**: `{search_code}`")
            
            # shpファイル情報
            if target_shp:
                st.markdown("**特定ファイル:**")
                st.success(f"- **shpファイル**: `{target_shp}`")
                
                estimated_path = self._estimate_shp_file_path(address_info)
                if estimated_path != "パス推定不可":
                    st.write(f"- **推定パス**: `{estimated_path}`")
        
        with col2:
            st.subheader("📋 操作")
            
            # 結果出力ボタン
            if st.button("📋 結果をテキスト表示", use_container_width=True):
                self._show_result_text(address_info, target_shp)
            
            # JSONダウンロード
            if st.button("💾 JSON形式でダウンロード", use_container_width=True):
                self._download_result_json(address_info, target_shp)
            
            # 全リセットボタン
            if st.button("🔄 全てリセット", use_container_width=True):
                self._reset_all_steps()
                st.rerun()
            
            # 新しい住所で再開始
            if st.button("🆕 新しい住所で開始", use_container_width=True):
                self._reset_from_step(1)
                st.rerun()
        
        # 処理統計
        with st.expander("📊 処理統計"):
            self._show_processing_stats()
    
    def _show_result_text(self, address_info, target_shp):
        """結果をテキスト形式で表示"""
        result_lines = [
            "=" * 50,
            "🏛️ 都道府県・市区町村選択ツール v33.0",
            "📍 住所特定結果",
            "=" * 50,
        ]
        
        # 住所情報
        result_lines.append("\n【住所情報】")
        for key, value in address_info.items():
            if value and value != "なし":
                result_lines.append(f"{key}: {value}")
        
        # ファイル情報
        if target_shp:
            result_lines.append(f"\n【特定ファイル】")
            result_lines.append(f"shpファイル: {target_shp}")
            
            estimated_path = self._estimate_shp_file_path(address_info)
            if estimated_path != "パス推定不可":
                result_lines.append(f"推定パス: {estimated_path}")
        
        # 処理情報
        result_lines.append(f"\n【処理情報】")
        result_lines.append(f"処理完了日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        result_lines.append(f"バージョン: {APP_CONFIG.get('version', '33.0')}")
        
        result_lines.append("=" * 50)
        
        result_text = "\n".join(result_lines)
        st.code(result_text, language="text")
        st.success("✅ 結果をコピーしてご利用ください")
    
    def _download_result_json(self, address_info, target_shp):
        """結果をJSON形式でダウンロード"""
        import json
        
        result_data = {
            "address_info": address_info,
            "target_shp_file": target_shp,
            "estimated_path": self._estimate_shp_file_path(address_info),
            "processing_info": {
                "completion_time": datetime.now().isoformat(),
                "version": APP_CONFIG.get('version', '33.0'),
                "steps_completed": st.session_state.step_completed
            }
        }
        
        json_str = json.dumps(result_data, ensure_ascii=False, indent=2)
        
        # ファイル名生成
        search_code = address_info.get('検索コード', 'unknown')
        chiban = address_info.get('地番', 'unknown')
        filename = f"address_result_{search_code}_{chiban}.json"
        
        st.download_button(
            label="📥 JSONファイルダウンロード",
            data=json_str,
            file_name=filename,
            mime="application/json",
            use_container_width=True
        )
    
    def _show_processing_stats(self):
        """処理統計を表示"""
        stats = {
            "処理完了ステップ数": sum(st.session_state.step_completed.values()),
            "総ステップ数": len(st.session_state.step_completed),
            "完了率": f"{sum(st.session_state.step_completed.values()) / len(st.session_state.step_completed) * 100:.1f}%"
        }
        
        # GISデータ統計
        area_data = st.session_state.get('area_data', {})
        if area_data:
            stats["読み込み済み大字数"] = len(area_data)
            total_chome = sum(len(chome_list) for chome_list in area_data.values())
            stats["読み込み済み丁目数"] = total_chome
        
        # セッションデータサイズ
        session_keys = ['prefecture_data', 'city_codes', 'area_data']
        data_size = sum(len(str(st.session_state.get(key, {}))) for key in session_keys)
        stats["セッションデータサイズ"] = f"{data_size:,} 文字"
        
        for key, value in stats.items():
            st.write(f"- **{key}**: {value}")
    
    def _reset_from_step(self, step_number):
        """指定されたステップ以降をリセット"""
        reset_keys = {
            1: ['selected_prefecture', 'selected_city', 'selected_oaza', 'selected_chome', 
                'input_chiban', 'area_data', 'target_shp_file', 'gis_load_attempted'],
            2: ['selected_oaza', 'selected_chome', 'input_chiban', 'target_shp_file'],
            3: ['input_chiban', 'target_shp_file'],
            4: ['target_shp_file']
        }
        
        step_keys = {
            1: ['step1', 'step2', 'step3', 'step4'],
            2: ['step2', 'step3', 'step4'],
            3: ['step3', 'step4'],
            4: ['step4']
        }
        
        # セッション状態をリセット
        for key in reset_keys.get(step_number, []):
            if key in ['area_data']:
                st.session_state[key] = {}
            elif key == 'gis_load_attempted':
                st.session_state[key] = False
            else:
                st.session_state[key] = ""
        
        # ステップ完了状態をリセット
        for step_key in step_keys.get(step_number, []):
            st.session_state.step_completed[step_key] = False
    
    def _reset_all_steps(self):
        """全ステップをリセット"""
        self._reset_from_step(1)
        st.success("✅ 全ステップをリセットしました")