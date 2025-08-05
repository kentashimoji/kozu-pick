#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src/utils.py - ユーティリティ関数とクラス

アプリケーション全体で使用される共通機能を提供
- セッション状態管理
- データ処理ヘルパー
- ファイル操作
- 文字列処理
- エラーハンドリング
"""

import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import zipfile
import tempfile
import shutil

class SessionStateManager:
    """Streamlitセッション状態の管理クラス"""
    
    def __init__(self):
        self.default_state = {
            'prefecture_data': {},
            'prefecture_codes': {},
            'city_codes': {},
            'data_loaded': False,
            'current_url': "",
            'selected_prefecture': "",
            'selected_city': "",
            'selected_file_path': "",
            'area_data': {},
            'selected_oaza': "",
            'selected_chome': "",
            'folder_path': ""
        }
    
    def init_session_state(self):
        """セッション状態を初期化"""
        for key, default_value in self.default_state.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def reset_session_state(self):
        """セッション状態をリセット"""
        for key, default_value in self.default_state.items():
            st.session_state[key] = default_value
    
    def clear_selection_data(self):
        """選択データのみクリア"""
        selection_keys = [
            'selected_prefecture', 'selected_city', 
            'selected_oaza', 'selected_chome'
        ]
        for key in selection_keys:
            st.session_state[key] = ""
    
    def clear_area_data(self):
        """大字・丁目データをクリア"""
        area_keys = ['area_data', 'selected_oaza', 'selected_chome', 'selected_file_path']
        for key in area_keys:
            if key in ['area_data']:
                st.session_state[key] = {}
            else:
                st.session_state[key] = ""
    
    def get_state_info(self) -> Dict[str, Any]:
        """現在のセッション状態情報を取得"""
        return {
            'data_loaded': st.session_state.get('data_loaded', False),
            'has_prefecture_data': bool(st.session_state.get('prefecture_data')),
            'has_area_data': bool(st.session_state.get('area_data')),
            'selected_prefecture': st.session_state.get('selected_prefecture', ''),
            'selected_city': st.session_state.get('selected_city', ''),
            'current_url': st.session_state.get('current_url', ''),
            'total_prefectures': len(st.session_state.get('prefecture_data', {})),
            'total_cities': sum(len(cities) for cities in st.session_state.get('prefecture_data', {}).values())
        }

class DataProcessor:
    """データ処理用のヘルパークラス"""
    
    @staticmethod
    def extract_area_from_dataframe(df: pd.DataFrame) -> Dict[str, List[str]]:
        """データフレームから大字・丁目を抽出（デバッグ強化版）"""
        import streamlit as st
        
        st.write(f"🔍 大字・丁目抽出開始")
        st.write(f"  - データ形状: {df.shape}")
        st.write(f"  - 列名: {list(df.columns)}")
        
        # 可能性のある列名パターン
        oaza_patterns = ['大字', 'おおあざ', 'オオアザ', 'OAZA', 'oaza', '字', '町名', 'TOWN', 'town', '大字名', '小字', '小字名']
        chome_patterns = ['丁目', 'ちょうめ', 'チョウメ', 'CHOME', 'chome', '丁', '番地', '丁目名']
        address_patterns = ['住所', 'address', 'ADDRESS', '所在地', '地名', 'name', 'NAME', '地区名', '町字名']
        
        area_data = {}
        
        # 列名を取得
        columns = [str(col).lower() for col in df.columns]
        
        # 大字・丁目の専用列を検索
        oaza_col = None
        chome_col = None
        address_col = None
        
        st.write(f"🔍 列名分析:")
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            # 大字列の検索
            if not oaza_col:
                for pattern in oaza_patterns:
                    if pattern.lower() in col_lower:
                        oaza_col = col
                        st.write(f"  ✅ 大字列発見: {col} (パターン: {pattern})")
                        break
            
            # 丁目列の検索
            if not chome_col:
                for pattern in chome_patterns:
                    if pattern.lower() in col_lower:
                        chome_col = col
                        st.write(f"  ✅ 丁目列発見: {col} (パターン: {pattern})")
                        break
            
            # 住所列の検索
            if not address_col:
                for pattern in address_patterns:
                    if pattern.lower() in col_lower:
                        address_col = col
                        st.write(f"  ✅ 住所列発見: {col} (パターン: {pattern})")
                        break
        
        st.write(f"🔍 検出結果:")
        st.write(f"  - 大字列: {oaza_col}")
        st.write(f"  - 丁目列: {chome_col}")
        st.write(f"  - 住所列: {address_col}")
        
        # データ抽出
        if oaza_col:
            st.write(f"📊 大字専用列から抽出中...")
            # 大字の専用列がある場合
            for idx, row in df.iterrows():
                oaza = str(row[oaza_col]) if pd.notna(row[oaza_col]) else ""
                oaza = oaza.strip()
                
                if oaza and oaza != 'nan' and len(oaza) > 0:
                    if oaza not in area_data:
                        area_data[oaza] = set()
                    
                    # 丁目データがある場合
                    if chome_col and pd.notna(row[chome_col]):
                        chome = str(row[chome_col]).strip()
                        if chome and chome != 'nan' and len(chome) > 0:
                            area_data[oaza].add(chome)
                
                # 進捗表示（最初の10行のみ）
                if idx < 10:
                    st.write(f"    行{idx+1}: 大字='{oaza}', 丁目='{str(row[chome_col]) if chome_col and pd.notna(row[chome_col]) else 'なし'}'")
        
        elif address_col:
            st.write(f"📊 住所列から正規表現で抽出中...")
            # 住所列から抽出
            import re
            
            for idx, row in df.iterrows():
                address = str(row[address_col]) if pd.notna(row[address_col]) else ""
                
                # 正規表現で大字・丁目を抽出
                oaza_matches = re.findall(r'大字(.+?)(?:[0-9]|丁目|番地|$)', address)
                chome_matches = re.findall(r'([0-9]+丁目)', address)
                
                for oaza_match in oaza_matches:
                    oaza = oaza_match.strip()
                    if oaza:
                        if oaza not in area_data:
                            area_data[oaza] = set()
                        
                        for chome in chome_matches:
                            area_data[oaza].add(chome)
                
                # 進捗表示（最初の10行のみ）
                if idx < 10:
                    st.write(f"    行{idx+1}: 住所='{address[:50]}...', 大字={oaza_matches}, 丁目={chome_matches}")
        
        else:
            st.write(f"📊 全列から住所情報を検索中...")
            # 全ての列から住所らしい情報を抽出
            import re
            
            for col in df.columns:
                if df[col].dtype == 'object':  # 文字列型の列のみ
                    st.write(f"  - 検索中の列: {col}")
                    found_count = 0
                    
                    for idx, row in df.iterrows():
                        value = str(row[col]) if pd.notna(row[col]) else ""
                        
                        # 大字・丁目パターンを検索
                        if '大字' in value or '丁目' in value or '小字' in value:
                            oaza_matches = re.findall(r'(?:大字|小字)(.+?)(?:[0-9]|丁目|番地|$)', value)
                            chome_matches = re.findall(r'([0-9]+丁目)', value)
                            
                            for oaza_match in oaza_matches:
                                oaza = oaza_match.strip()
                                if oaza and len(oaza) > 0:
                                    if oaza not in area_data:
                                        area_data[oaza] = set()
                                    
                                    for chome in chome_matches:
                                        area_data[oaza].add(chome)
                                    
                                    found_count += 1
                    
                    if found_count > 0:
                        st.write(f"    ✅ {found_count}件の住所情報を発見")
        
        # SetをListに変換してソート
        for oaza in area_data:
            area_data[oaza] = sorted(list(area_data[oaza]))
        
        st.write(f"✅ 抽出完了: {len(area_data)}個の大字")
        
        if area_data:
            # 抽出結果のサンプルを表示
            sample_items = list(area_data.items())[:3]
            for oaza, chome_list in sample_items:
                st.write(f"  - {oaza}: {len(chome_list)}個の丁目 {chome_list[:3] if chome_list else '(なし)'}")
        
        return area_data
    
    @staticmethod
    def sort_prefectures_with_okinawa_first(prefecture_data: Dict, prefecture_codes: Dict) -> Dict:
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
    
    @staticmethod
    def sort_cities_by_code(cities_dict: Dict) -> Dict:
        """市区町村を団体コード順にソート"""
        sorted_cities = sorted(cities_dict.keys(), 
                             key=lambda x: cities_dict[x]['full_code'])
        
        # ソート済みの市区町村辞書を作成
        sorted_cities_dict = {}
        for city in sorted_cities:
            sorted_cities_dict[city] = cities_dict[city]
        
        return sorted_cities_dict
        
    def organize_prefecture_data(df):
        """都道府県データを整理"""
        import streamlit as st
        import pandas as pd
        
        prefecture_data = {}
        prefecture_codes = {}
        city_codes = {}

        # 列名検索
        prefecture_cols = [col for col in df.columns if '都道府県' in col and '漢字' in col]
        city_cols = [col for col in df.columns if '市区町村' in col and '漢字' in col]
        code_col = '団体コード'

        if not prefecture_cols or not city_cols:
            st.error(f"適切な列が見つかりません。利用可能な列: {list(df.columns)}")
            return None, None, None

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
        sorted_prefecture_data = DataProcessor.sort_prefectures_with_okinawa_first(
            prefecture_data, prefecture_codes
        )

        return sorted_prefecture_data, prefecture_codes, city_codes

class FileHandler:
    """ファイル操作用のヘルパークラス"""
    
    @staticmethod
    def extract_zip_safely(zip_path: str, extract_to: str) -> List[str]:
        """ZIPファイルを安全に展開"""
        try:
            extracted_files = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 安全性チェック
                for member in zip_ref.namelist():
                    if os.path.isabs(member) or ".." in member:
                        continue  # 危険なパスをスキップ
                
                zip_ref.extractall(extract_to)
            
            # 展開されたファイルを検索
            for root, dirs, files in os.walk(extract_to):
                for file in files:
                    if file.lower().endswith(('.shp', '.kml', '.geojson', '.csv', '.xlsx')):
                        extracted_files.append(os.path.join(root, file))
            
            return extracted_files
            
        except Exception as e:
            raise Exception(f"ZIP展開エラー: {str(e)}")
    
    @staticmethod
    def create_temp_directory() -> str:
        """一時ディレクトリを作成"""
        return tempfile.mkdtemp()
    
    @staticmethod
    def cleanup_temp_directory(temp_dir: str):
        """一時ディレクトリをクリーンアップ"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass  # クリーンアップエラーは無視

class StringHelper:
    """文字列処理のヘルパークラス"""
    
    @staticmethod
    def clean_string(text: str) -> str:
        """文字列をクリーンアップ"""
        if not text or pd.isna(text):
            return ""
        return str(text).strip()
    
    @staticmethod
    def extract_code_from_filename(filename: str) -> Optional[str]:
        """ファイル名から団体コードを抽出"""
        # 6桁の数字パターンを検索
        pattern = r'(\d{6})'
        match = re.search(pattern, filename)
        return match.group(1) if match else None
    
    @staticmethod
    def format_address(prefecture: str, city: str, oaza: str = "", chome: str = "") -> str:
        """完全な住所を格式化"""
        parts = [prefecture, city]
        if oaza:
            parts.append(oaza)
        if chome:
            parts.append(chome)
        return "".join(parts)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 60) -> str:
        """テキストを指定長で切り詰め"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

class ValidationHelper:
    """バリデーション用のヘルパークラス"""
    
    @staticmethod
    def is_valid_github_url(url: str) -> bool:
        """GitHub URLが有効かチェック"""
        if not url:
            return False
        return "github.com" in url or "raw.githubusercontent.com" in url
    
    @staticmethod
    def is_valid_prefecture_code(code: str) -> bool:
        """都道府県コードが有効かチェック"""
        if not code or len(code) != 2:
            return False
        try:
            code_int = int(code)
            return 1 <= code_int <= 47
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_city_code(code: str) -> bool:
        """市区町村コードが有効かチェック"""
        if not code or len(code) != 3:
            return False
        try:
            int(code)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_dataframe_columns(df: pd.DataFrame, required_patterns: List[str]) -> Dict[str, bool]:
        """データフレームの列が要件を満たすかチェック"""
        results = {}
        columns = [str(col).lower() for col in df.columns]
        
        for pattern in required_patterns:
            results[pattern] = any(pattern.lower() in col for col in columns)
        
        return results

class ErrorHandler:
    """エラーハンドリング用のヘルパークラス"""
    
    @staticmethod
    def handle_import_error(module_name: str, error: Exception):
        """インポートエラーを処理"""
        st.error(f"モジュール '{module_name}' の読み込みに失敗しました: {error}")
        st.info("必要なライブラリがインストールされているか確認してください。")
    
    @staticmethod
    def handle_file_error(file_path: str, error: Exception):
        """ファイルエラーを処理"""
        st.error(f"ファイル '{file_path}' の処理に失敗しました: {error}")
        st.info("ファイルの形式やアクセス権限を確認してください。")
    
    @staticmethod
    def handle_network_error(url: str, error: Exception):
        """ネットワークエラーを処理"""
        st.error(f"ネットワークエラー: {error}")
        st.info(f"URL '{url}' にアクセスできません。インターネット接続を確認してください。")

class ProgressTracker:
    """進捗追跡のヘルパークラス"""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
    
    def update(self, step: int, message: str):
        """進捗を更新"""
        self.current_step = step
        progress = min(step / self.total_steps, 1.0)
        self.progress_bar.progress(progress)
        self.status_text.text(message)
    
    def complete(self, message: str = "完了しました"):
        """進捗を完了"""
        self.progress_bar.progress(1.0)
        self.status_text.text(f"✅ {message}")
    
    def error(self, message: str):
        """エラー状態に設定"""
        self.status_text.text(f"❌ {message}")

class ConfigHelper:
    """設定管理のヘルパークラス"""
    
    @staticmethod
    def get_default_github_config() -> Dict[str, Any]:
        """デフォルトのGitHub設定を取得"""
        return {
            "user_agent": "PrefectureCitySelector/33.0",
            "timeout": 30,
            "default_url": "https://raw.githubusercontent.com/USERNAME/REPOSITORY/main/000925835.xlsx"
        }
    
    @staticmethod
    def get_default_gis_config() -> Dict[str, Any]:
        """デフォルトのGIS設定を取得"""
        return {
            "supported_extensions": ['.zip', '.shp', '.shx', '.prj', '.dbf', '.cpg', '.kml'],
            "shapefile_required": ['.shp', '.shx', '.dbf']
        }
    
    @staticmethod
    def get_app_info() -> Dict[str, Any]:
        """アプリケーション情報を取得"""
        return {
            "name": "都道府県・市区町村選択ツール",
            "version": "33.0",
            "author": "AI Assistant",
            "description": "GitHub連携対応の都道府県・市区町村選択ツール",
            "last_updated": datetime.now().strftime('%Y-%m-%d')
        }

# 便利な関数（モジュールレベル）
def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式にフォーマット"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def safe_convert_to_int(value: Any, default: int = 0) -> int:
    """安全に整数に変換"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_convert_to_str(value: Any, default: str = "") -> str:
    """安全に文字列に変換"""
    try:
        return str(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def generate_timestamp() -> str:
    """現在時刻のタイムスタンプを生成"""
    return datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')

def debug_session_state():
    """セッション状態をデバッグ表示"""
    if st.checkbox("セッション状態をデバッグ表示"):
        st.json(dict(st.session_state))

def organize_prefecture_data(df):
        """都道府県データを整理（data_loaderから移動）"""
        prefecture_data = {}
        prefecture_codes = {}
        city_codes = {}

        # 列名検索
        prefecture_cols = [col for col in df.columns if '都道府県' in col and '漢字' in col]
        city_cols = [col for col in df.columns if '市区町村' in col and '漢字' in col]
        code_col = '団体コード'

        if not prefecture_cols or not city_cols:
            st.error(f"適切な列が見つかりません。利用可能な列: {list(df.columns)}")
            return None, None, None

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
        sorted_prefecture_data = DataProcessor.sort_prefectures_with_okinawa_first(
            prefecture_data, prefecture_codes
        )

        return sorted_prefecture_data, prefecture_codes, city_codes
