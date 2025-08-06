#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pages/main_page.py - メインページ（リファクタリング版）
4段階構成の制御とコーディネーション
データ表示の正規化機能を追加
"""
import sys
from pathlib import Path
import re
import pandas as pd

# プロジェクトルート設定
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

try:
    from config.settings import APP_CONFIG
except ImportError:
    APP_CONFIG = {"version": "33.0"}

# コンポーネントの安全なインポート
try:
    from pages.components.progress_indicator import ProgressIndicator
except ImportError as e:
    st.warning(f"ProgressIndicator インポートエラー: {str(e)}")
    ProgressIndicator = None

try:
    from pages.components.result_display import ResultDisplay
except ImportError as e:
    st.warning(f"ResultDisplay インポートエラー: {str(e)}")
    ResultDisplay = None

try:
    from pages.steps.step1_selection import Step1Selection
except ImportError as e:
    st.warning(f"Step1Selection インポートエラー: {str(e)}")
    Step1Selection = None

try:
    from pages.steps.step2_area import Step2Area
except ImportError as e:
    st.warning(f"Step2Area インポートエラー: {str(e)}")
    Step2Area = None

try:
    from pages.steps.step3_chiban import Step3Chiban
except ImportError as e:
    st.warning(f"Step3Chiban インポートエラー: {str(e)}")
    Step3Chiban = None

try:
    from pages.steps.step4_shp import Step4Shp
except ImportError as e:
    st.warning(f"Step4Shp インポートエラー: {str(e)}")
    Step4Shp = None

try:
    from src.address_builder import AddressBuilder
except ImportError as e:
    st.warning(f"AddressBuilder インポートエラー: {str(e)}")
    AddressBuilder = None

class MainPage:
    def __init__(self, app):
        self.app = app
        
        # コンポーネント初期化
        self._init_components()
        
        # セッション状態の初期化
        self._init_session_state()
    
    def normalize_area_name_for_display(self, name: str) -> str:
        """UI表示用のエリア名正規化関数"""
        try:
            if not name or pd.isna(name):
                return ""
            
            name_str = str(name).strip()
            
            # 空文字や"nan"をフィルター
            if not name_str or name_str.lower() == 'nan':
                return ""
            
            # 数字のみの場合の処理
            if name_str.isdigit():
                # 小さい数字（1-20）は丁目として処理
                if int(name_str) <= 20:
                    return f"{name_str}丁目"
                else:
                    # 大きい数字はコード変換を試行
                    return self.convert_area_code_for_display(name_str)
            
            # 001丁目、002丁目などのパターン
            if re.match(r'^\d{3}丁目$', name_str):
                # 先頭のゼロを削除
                number = str(int(name_str[:3]))
                return f"{number}丁目"
            
            # 沖縄県の大字コード変換
            converted = self.convert_area_code_for_display(name_str)
            if converted != name_str:
                return converted
            
            # 既に適切な文字列の場合はそのまま返す
            return name_str
            
        except Exception as e:
            return str(name) if name else ""

    def convert_area_code_for_display(self, code: str) -> str:
        """UI表示用のエリアコード変換関数"""
        try:
            # 沖縄県の大字・地区のパターンマッチング（拡張版）
            okinawa_patterns = {
                # 那覇市の大字例
                '01': '那覇',
                '001': '那覇',
                '02': '首里', 
                '002': '首里',
                '03': '真嘉比',
                '003': '真嘉比',
                '04': '泊',
                '004': '泊',
                '05': '久茂地',
                '005': '久茂地',
                '06': '牧志',
                '006': '牧志',
                '07': '安里',
                '007': '安里',
                '08': '上原',
                '008': '上原',
                '09': '古島',
                '009': '古島',
                '10': '銘苅',
                '010': '銘苅',
                # 浦添市の大字例
                '11': '宮里',
                '011': '宮里',
                '12': '普天間',
                '012': '普天間',
                '13': '内間',
                '013': '内間',
                '14': '経塚',
                '014': '経塚',
                '15': '港川',
                '015': '港川',
                '16': '牧港',
                '016': '牧港',
                # 宜野湾市の大字例
                '21': '大山',
                '021': '大山',
                '22': '宜野湾',
                '022': '宜野湾',
                '23': '新城',
                '023': '新城',
                '24': '我如古',
                '024': '我如古',
                '25': '嘉数',
                '025': '嘉数',
                '26': '真栄原',
                '026': '真栄原',
                # 西原町の大字例
                '31': '西原',
                '031': '西原',
                '32': '翁長',
                '032': '翁長',
                '33': '小那覇',
                '033': '小那覇',
                '34': '棚原',
                '034': '棚原'
            }
            
            # 直接マッチング
            if code in okinawa_patterns:
                return okinawa_patterns[code]
            
            # ゼロパディング/ゼロ除去での変換
            padded_code = code.zfill(3)
            if padded_code in okinawa_patterns:
                return okinawa_patterns[padded_code]
            
            stripped_code = code.lstrip('0') or '0'
            if stripped_code in okinawa_patterns:
                return okinawa_patterns[stripped_code]
            
            # 変換できない場合は元の値を返す
            return code
            
        except Exception as e:
            return code

    def normalize_area_data_for_display(self, area_data: dict) -> dict:
        """エリアデータ全体を表示用に正規化"""
        try:
            normalized_data = {}
            
            for oaza, chome_list in area_data.items():
                # 大字名を正規化
                normalized_oaza = self.normalize_area_name_for_display(oaza)
                
                if normalized_oaza:
                    # 丁目リストも正規化
                    normalized_chome_list = []
                    for chome in chome_list:
                        normalized_chome = self.normalize_area_name_for_display(chome)
                        if normalized_chome:
                            normalized_chome_list.append(normalized_chome)
                    
                    normalized_data[normalized_oaza] = sorted(list(set(normalized_chome_list))) if normalized_chome_list else ["丁目データなし"]
            
            return normalized_data
            
        except Exception as e:
            st.error(f"❌ データ正規化エラー: {str(e)}")
            return area_data  # エラー時は元データを返す
    
    def _init_components(self):
        """コンポーネントを初期化"""
        try:
            # コンポーネントの安全な初期化
            if ProgressIndicator:
                self.progress_indicator = ProgressIndicator()
            else:
                st.warning("⚠️ ProgressIndicator が利用できません")
                self.progress_indicator = None
            
            if ResultDisplay:
                self.result_display = ResultDisplay()
            else:
                st.warning("⚠️ ResultDisplay が利用できません")
                self.result_display = None
            
            if AddressBuilder:
                self.address_builder = AddressBuilder()
            else:
                st.warning("⚠️ AddressBuilder が利用できません")
                self.address_builder = None

            # 各ステップコンポーネント
            if Step1Selection:
                self.step1 = Step1Selection(self.app)
            else:
                st.warning("⚠️ Step1Selection が利用できません")
                self.step1 = None
            
            if Step2Area:
                self.step2 = Step2Area(self.app)
            else:
                st.warning("⚠️ Step2Area が利用できません")
                self.step2 = None
            
            if Step3Chiban:
                self.step3 = Step3Chiban(self.app)
            else:
                st.warning("⚠️ Step3Chiban が利用できません")
                self.step3 = None
            
            if Step4Shp:
                self.step4 = Step4Shp(self.app)
            else:
                st.warning("⚠️ Step4Shp が利用できません")
                self.step4 = None
            
            st.success("✅ 利用可能なコンポーネントを初期化しました")
            
        except Exception as e:
            st.error(f"コンポーネント初期化エラー: {str(e)}")
            # フォールバック：全て None に設定
            self.progress_indicator = None
            self.result_display = None
            self.address_builder = None
            self.step1 = None
            self.step2 = None  
            self.step3 = None
            self.step4 = None
    
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
            'gis_load_attempted': False,
            'step_completed': {
                'step1': False,
                'step2': False,
                'step3': False,
                'step4': False
            }
        }
        
        for key, default_value in init_keys.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def render(self):
        """メインページを描画"""
        # ヘッダー
        self._render_header()
        
        # データ読み込み確認
        if not st.session_state.get('data_loaded', False):
            self._render_no_data_state()
            return
        
        # 進捗インジケーター
        if self.progress_indicator:
            self.progress_indicator.render()
        else:
            self._render_fallback_progress()
        
        # 各ステップの描画
        self._render_steps()
        
        # 最終結果表示
        if st.session_state.step_completed['step4']:
            self._render_final_result()
    
    def _render_header(self):
        """ヘッダーを描画"""
        version = APP_CONFIG.get('version', '33.0') if 'APP_CONFIG' in globals() else '33.0'
        st.title(f"🏛️ 都道府県・市区町村選択ツール v{version}")
        st.markdown("**4段階の住所特定システム**")
    
    def _render_no_data_state(self):
        """データ未読み込み時の表示"""
        st.warning("📋 データが読み込まれていません")
        st.info("アプリケーションの初期化を待っています...")
        
        if st.button("🔄 データを再読み込み"):
            if hasattr(self.app, 'manual_reload_data'):
                self.app.manual_reload_data()
            else:
                st.rerun()
    
    def _render_fallback_progress(self):
        """フォールバック用進捗表示"""
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
    
    def _render_steps(self):
        """各ステップを描画"""
        try:
            # Step 1: 都道府県・市区町村選択
            if self.step1:
                self.step1.render()
            else:
                self._render_fallback_step1()
            
            # Step 2: 大字・丁目選択（Step1完了後）
            if st.session_state.step_completed['step1']:
                if self.step2:
                    self.step2.render()
                else:
                    self._render_fallback_step2()
            
            # Step 3: 地番入力（Step2完了後）
            if st.session_state.step_completed['step2']:
                if self.step3:
                    self.step3.render()
                else:
                    self._render_fallback_step3()
            
            # Step 4: shpファイル特定（Step3完了後）
            if st.session_state.step_completed['step3']:
                if self.step4:
                    self.step4.render()
                else:
                    self._render_fallback_step4()
                    
        except Exception as e:
            st.error(f"ステップ描画エラー: {str(e)}")
            st.info("一部の機能が利用できない状態です")
    
    def _render_fallback_step1(self):
        """Step1のフォールバック表示"""
        st.header("1️⃣ 都道府県・市区町村選択")
        st.warning("⚠️ Step1コンポーネントが読み込めませんでした")
        st.info("基本的な選択機能のみ利用可能です")
        
        # 基本的な選択UI
        prefecture_data = st.session_state.get('prefecture_data', {})
        if prefecture_data:
            prefectures = list(prefecture_data.keys())
            selected_prefecture = st.selectbox(
                "都道府県を選択:",
                ["選択してください"] + prefectures
            )
            
            if selected_prefecture != "選択してください":
                st.session_state.selected_prefecture = selected_prefecture
                
                cities = list(prefecture_data[selected_prefecture].keys())
                selected_city = st.selectbox(
                    "市区町村を選択:",
                    ["選択してください"] + cities
                )
                
                if selected_city != "選択してください":
                    st.session_state.selected_city = selected_city
                    st.session_state.step_completed['step1'] = True
                    st.success("✅ Step1完了")
    
    def _render_fallback_step2(self):
        """Step2のフォールバック表示（正規化機能付き）"""
        st.header("2️⃣ 大字・丁目選択")
        
        if 'area_data' not in st.session_state or not st.session_state.area_data:
            st.warning("⚠️ エリアデータが読み込まれていません")
            st.info("先にファイルをアップロードするか、ダミーデータで継続してください")
            
            if st.button("ダミーデータで続行"):
                st.session_state.area_data = {
                    "001": ["001丁目", "002丁目", "003丁目"],
                    "002": ["001丁目", "002丁目"],
                    "中央": ["1丁目", "2丁目"]
                }
                st.rerun()
            return
        
        # デバッグ用：生データを表示
        with st.expander("🔍 デバッグ: 元データ確認"):
            st.write("生データ:")
            for oaza, chome_list in list(st.session_state.area_data.items())[:3]:
                st.write(f"  {oaza}: {chome_list[:3]}...")
        
        # データを表示用に正規化
        try:
            normalized_area_data = self.normalize_area_data_for_display(st.session_state.area_data)
            
            # デバッグ用：正規化データを表示
            with st.expander("🔍 デバッグ: 正規化データ確認"):
                st.write("正規化データ:")
                for oaza, chome_list in list(normalized_area_data.items())[:3]:
                    st.write(f"  {oaza}: {chome_list[:3]}...")
            
        except Exception as e:
            st.error(f"❌ データ正規化エラー: {str(e)}")
            normalized_area_data = st.session_state.area_data  # フォールバック
        
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 🏞️ 大字選択")
            oaza_options = ["選択してください"] + list(normalized_area_data.keys())
            selected_oaza = st.selectbox(
                "大字を選択してください",
                options=oaza_options,
                key="oaza_selection_main"
            )
        
        with col2:
            st.write("### 🏘️ 丁目選択")
            if selected_oaza and selected_oaza != "選択してください":
                chome_options = ["選択してください"] + normalized_area_data[selected_oaza]
                selected_chome = st.selectbox(
                    "丁目を選択してください",
                    options=chome_options,
                    key="chome_selection_main"
                )
            else:
                st.selectbox(
                    "まず大字を選択してください",
                    options=["選択してください"],
                    disabled=True,
                    key="chome_selection_disabled"
                )
                selected_chome = None
        
        # 選択結果の処理
        if (selected_oaza and selected_oaza != "選択してください" and 
            selected_chome and selected_chome != "選択してください"):
            
            # セッション状態に保存
            st.session_state.selected_oaza = selected_oaza
            st.session_state.selected_chome = selected_chome
            st.session_state.step_completed['step2'] = True
            
            if selected_chome != "丁目データなし":
                st.success(f"✅ 選択完了: {selected_oaza} {selected_chome}")
            else:
                st.info(f"ℹ️ 選択完了: {selected_oaza} （丁目データなし）")
    
    def _render_fallback_step3(self):
        """Step3のフォールバック表示"""
        st.header("3️⃣ 地番入力")
        st.warning("⚠️ Step3コンポーネントが読み込めませんでした")
        
        chiban = st.text_input("地番を入力:")
        if st.button("確定") and chiban:
            st.session_state.input_chiban = chiban
            st.session_state.step_completed['step3'] = True
            st.rerun()
    
    def _render_fallback_step4(self):
        """Step4のフォールバック表示"""
        st.header("4️⃣ shpファイル特定")
        st.warning("⚠️ Step4コンポーネントが読み込けませんでした")
        
        if st.button("自動特定"):
            # 基本的なファイル名生成
            search_code = "47201"  # ダミー
            chiban = st.session_state.get('input_chiban', '1')
            st.session_state.target_shp_file = f"{search_code}_{chiban}.shp"
            st.session_state.step_completed['step4'] = True
            st.rerun()
    
    def _render_final_result(self):
        """最終結果を表示"""
        st.markdown("---")
        st.header("🎯 最終結果")
        
        if self.result_display and self.address_builder:
            # 完全な結果表示
            address_info = self.address_builder.build_complete_address_info()
            target_shp = st.session_state.get('target_shp_file', '')
            
            self.result_display.render(address_info, target_shp)
        else:
            # フォールバック表示
            self._render_fallback_result()
    
    def _render_fallback_result(self):
        """フォールバック用結果表示"""
        st.info("✅ 4段階の処理が完了しました")
        
        # 基本情報の表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**選択された情報:**")
            st.write(f"- 都道府県: {st.session_state.get('selected_prefecture', '')}")
            st.write(f"- 市区町村: {st.session_state.get('selected_city', '')}")
            st.write(f"- 大字: {st.session_state.get('selected_oaza', '')}")
            st.write(f"- 丁目: {st.session_state.get('selected_chome', '') or '指定なし'}")
            st.write(f"- 地番: {st.session_state.get('input_chiban', '')}")
        
        with col2:
            target_shp = st.session_state.get('target_shp_file', '')
            if target_shp:
                st.success(f"特定ファイル: {target_shp}")
            
            if st.button("🔄 全てリセット"):
                self._reset_all_steps()
                st.rerun()
    
    def _reset_all_steps(self):
        """全ステップをリセット"""
        reset_keys = [
            'selected_prefecture', 'selected_city', 'selected_oaza', 
            'selected_chome', 'input_chiban', 'area_data', 'target_shp_file',
            'gis_load_attempted'
        ]
        
        for key in reset_keys:
            if key == 'area_data':
                st.session_state[key] = {}
            elif key == 'gis_load_attempted':
                st.session_state[key] = False
            else:
                st.session_state[key] = ""
        
        # ステップ完了状態をリセット
        for step_key in st.session_state.step_completed:
            st.session_state.step_completed[step_key] = False
        
        st.success("✅ 全ステップをリセットしました")