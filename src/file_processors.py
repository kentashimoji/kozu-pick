#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src/file_processors.py - ファイル処理専用クラス（完全修正版）
ZIPファイル内のShapefile処理に対応
大字・丁目の文字列表示を改善
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import zipfile
import io
import tempfile
import os
import re
from typing import Dict, List, Any, Optional

class FileProcessor:
    """ファイル処理のメインクラス"""

    def __init__(self):
        self.supported_extensions = ['.zip', '.csv', '.xlsx', '.xls', '.shp', '.kml', '.geojson']
        self.shapefile_extensions = ['.shp', '.dbf', '.shx', '.prj', '.cpg']

    def process_file(self, file_content: bytes, file_name: str, file_extension: str) -> bool:
        """ファイル処理のメインメソッド"""
        try:
            st.write(f"📁 処理開始: {file_name} ({file_extension})")
            
            if file_extension == '.zip':
                return self._process_zip_file(file_content, file_name)
            elif file_extension in ['.csv', '.xlsx', '.xls']:
                return self._process_data_file(file_content, file_extension)
            elif file_extension == '.shp':
                return self._process_shapefile(file_content, file_name)
            elif file_extension in ['.kml', '.geojson']:
                return self._process_gis_file(file_content, file_extension)
            else:
                st.warning(f"⚠️ 未対応の拡張子: {file_extension}")
                return False
                
        except Exception as e:
            st.error(f"❌ ファイル処理エラー: {str(e)}")
            return False

    def _normalize_area_name(self, name: str) -> str:
        """エリア名を正規化（数字コード対応）"""
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
                    return self._convert_area_code(name_str)
            
            # 沖縄県の大字コード変換
            converted = self._convert_area_code(name_str)
            if converted != name_str:
                return converted
            
            # 既に適切な文字列の場合はそのまま返す
            return name_str
            
        except Exception as e:
            st.warning(f"⚠️ エリア名正規化エラー ({name}): {str(e)}")
            return str(name) if name else ""

    def _convert_area_code(self, code: str) -> str:
        """エリアコードを文字列に変換"""
        try:
            # 沖縄県の大字・地区のパターンマッチング（サンプル）
            okinawa_patterns = {
                # 那覇市の大字例
                '01': '那覇',
                '02': '首里', 
                '03': '真嘉比',
                '04': '泊',
                '05': '久茂地',
                '06': '牧志',
                '07': '安里',
                '08': '上原',
                '09': '古島',
                '10': '銘苅',
                # 浦添市の大字例
                '11': '宮里',
                '12': '普天間',
                '13': '内間',
                '14': '経塚',
                '15': '港川',
                '16': '牧港',
                # 宜野湾市の大字例
                '21': '大山',
                '22': '宜野湾',
                '23': '新城',
                '24': '我如古',
                '25': '嘉数',
                '26': '真栄原'
            }
            
            # ゼロパディングされたコードもチェック
            padded_code = code.zfill(2)
            if padded_code in okinawa_patterns:
                return okinawa_patterns[padded_code]
            
            # 元のコードをチェック
            if code in okinawa_patterns:
                return okinawa_patterns[code]
            
            # 変換できない場合は元の値を返す
            return code
            
        except Exception as e:
            return code

    def _process_zip_file(self, zip_content: bytes, zip_name: str) -> bool:
        """ZIPファイル処理（完全修正版）"""
        try:
            st.write(f"📦 ZIP処理開始: {zip_name}")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # ZIPファイルを解凍
                with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
                    zip_file.extractall(temp_dir)
                    file_list = zip_file.namelist()
                    
                    st.write(f"📦 ZIP内ファイル一覧 ({len(file_list)}個):")
                    for file in file_list[:10]:
                        st.write(f"  📄 {file}")
                    if len(file_list) > 10:
                        st.write(f"  ... 他{len(file_list)-10}個")
                
                # 実際に解凍されたファイルを確認
                extracted_files = []
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, temp_dir)
                        extracted_files.append({
                            'name': file,
                            'path': file_path,
                            'relative_path': rel_path,
                            'extension': '.' + file.lower().split('.')[-1] if '.' in file else ''
                        })
                
                st.write(f"🗂️ 解凍されたファイル ({len(extracted_files)}個):")
                for file_info in extracted_files[:10]:
                    st.write(f"  📄 {file_info['name']} ({file_info['extension']})")
                if len(extracted_files) > 10:
                    st.write(f"  ... 他{len(extracted_files)-10}個")
                
                # 処理可能ファイルを順次チェック
                success = False
                
                # 1. Shapefileを最優先で処理
                success = self._try_process_shapefiles(extracted_files, temp_dir)
                if success:
                    return True
                
                # 2. CSVファイルを処理
                success = self._try_process_csv_files(extracted_files, temp_dir)
                if success:
                    return True
                
                # 3. Excelファイルを処理
                success = self._try_process_excel_files(extracted_files, temp_dir)
                if success:
                    return True
                
                # 4. その他のGISファイルを処理
                success = self._try_process_other_gis_files(extracted_files, temp_dir)
                if success:
                    return True
                
                # 5. 全て失敗した場合はダミーデータで継続
                st.warning("⚠️ 処理可能ファイルが見つかりませんが、ダミーデータで継続します")
                return self._create_dummy_area_data(zip_name)
                
        except zipfile.BadZipFile:
            st.error("❌ 無効なZIPファイルです")
            return False
        except Exception as e:
            st.error(f"❌ ZIP処理エラー: {str(e)}")
            return False

    def _try_process_shapefiles(self, extracted_files: List[Dict], temp_dir: str) -> bool:
        """Shapefileの処理を試行"""
        try:
            # Shapefileを探す
            shp_files = [f for f in extracted_files if f['extension'] == '.shp']
            
            if not shp_files:
                st.info("ℹ️ Shapefileが見つかりません")
                return False
            
            st.write(f"🗺️ Shapefile発見: {len(shp_files)}個")
            for shp_file in shp_files:
                st.write(f"  📍 {shp_file['name']}")
            
            # 最初のShapefileを処理
            shp_file = shp_files[0]
            shp_path = shp_file['path']
            
            st.write(f"📥 Shapefile読み込み: {shp_file['name']}")
            
            # GeoPandasで読み込み
            gdf = gpd.read_file(shp_path)
            
            st.write(f"📊 Shapefile情報:")
            st.write(f"  - レコード数: {len(gdf):,}")
            st.write(f"  - 列数: {len(gdf.columns)}")
            st.write(f"  - 座標系: {gdf.crs}")
            
            # 列名を表示
            st.write(f"  - 列名: {', '.join(gdf.columns[:10])}")
            if len(gdf.columns) > 10:
                st.write(f"    ... 他{len(gdf.columns)-10}個")
            
            # 大字・丁目データを抽出
            area_data = self._extract_area_data_from_gdf(gdf)
            if area_data:
                st.session_state.area_data = area_data
                st.success(f"✅ 大字・丁目データを抽出: {len(area_data)}個")
                return True
            else:
                st.info("ℹ️ 大字・丁目データが見つかりませんが、Shapefile読み込みは成功")
                # 基本的なエリアデータを作成
                return self._create_basic_area_data_from_gdf(gdf)
                
        except Exception as e:
            st.warning(f"⚠️ Shapefile処理エラー: {str(e)}")
            return False

    def _try_process_csv_files(self, extracted_files: List[Dict], temp_dir: str) -> bool:
        """CSVファイルの処理を試行"""
        try:
            csv_files = [f for f in extracted_files if f['extension'] == '.csv']
            
            if not csv_files:
                return False
            
            st.write(f"📄 CSVファイル発見: {len(csv_files)}個")
            
            # 最初のCSVファイルを処理
            csv_file = csv_files[0]
            
            # 複数のエンコーディングを試行
            encodings = ['utf-8', 'shift-jis', 'cp932', 'utf-8-sig']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_file['path'], encoding=encoding)
                    st.success(f"✅ CSV読み込み成功 (エンコーディング: {encoding})")
                    break
                except:
                    continue
            
            if df is None:
                st.error("❌ CSV読み込み失敗（エンコーディング問題）")
                return False
            
            st.write(f"📊 CSV情報:")
            st.write(f"  - 行数: {len(df):,}")
            st.write(f"  - 列数: {len(df.columns)}")
            st.write(f"  - 列名: {', '.join(df.columns[:5])}")
            
            # エリアデータを抽出
            area_data = self._extract_area_data_from_df(df)
            if area_data:
                st.session_state.area_data = area_data
                st.success(f"✅ エリアデータを抽出: {len(area_data)}個")
                return True
            
            return False
            
        except Exception as e:
            st.warning(f"⚠️ CSV処理エラー: {str(e)}")
            return False

    def _try_process_excel_files(self, extracted_files: List[Dict], temp_dir: str) -> bool:
        """Excelファイルの処理を試行"""
        try:
            excel_files = [f for f in extracted_files if f['extension'] in ['.xlsx', '.xls']]
            
            if not excel_files:
                return False
            
            st.write(f"📊 Excelファイル発見: {len(excel_files)}個")
            
            # 最初のExcelファイルを処理
            excel_file = excel_files[0]
            
            df = pd.read_excel(excel_file['path'])
            
            st.write(f"📊 Excel情報:")
            st.write(f"  - 行数: {len(df):,}")
            st.write(f"  - 列数: {len(df.columns)}")
            st.write(f"  - 列名: {', '.join(df.columns[:5])}")
            
            # エリアデータを抽出
            area_data = self._extract_area_data_from_df(df)
            if area_data:
                st.session_state.area_data = area_data
                st.success(f"✅ エリアデータを抽出: {len(area_data)}個")
                return True
            
            return False
            
        except Exception as e:
            st.warning(f"⚠️ Excel処理エラー: {str(e)}")
            return False

    def _try_process_other_gis_files(self, extracted_files: List[Dict], temp_dir: str) -> bool:
        """その他のGISファイルの処理を試行"""
        try:
            gis_files = [f for f in extracted_files if f['extension'] in ['.kml', '.geojson', '.gpx']]
            
            if not gis_files:
                return False
            
            st.write(f"🗺️ GISファイル発見: {len(gis_files)}個")
            
            # 最初のGISファイルを処理
            gis_file = gis_files[0]
            
            gdf = gpd.read_file(gis_file['path'])
            
            st.write(f"📊 GISファイル情報:")
            st.write(f"  - レコード数: {len(gdf):,}")
            st.write(f"  - 列数: {len(gdf.columns)}")
            st.write(f"  - 座標系: {gdf.crs}")
            
            # エリアデータを抽出
            area_data = self._extract_area_data_from_gdf(gdf)
            if area_data:
                st.session_state.area_data = area_data
                st.success(f"✅ エリアデータを抽出: {len(area_data)}個")
                return True
            
            return False
            
        except Exception as e:
            st.warning(f"⚠️ GISファイル処理エラー: {str(e)}")
            return False

    def _extract_area_data_from_gdf(self, gdf: gpd.GeoDataFrame) -> Optional[Dict[str, List[str]]]:
        """GeoPandasデータフレームから大字・丁目データを抽出（改善版）"""
        try:
            area_data = {}
            
            st.write("🔍 列データの詳細分析:")
            
            # 全列の詳細情報を表示
            for col in gdf.columns:
                if col != 'geometry':
                    unique_values = gdf[col].dropna().unique()
                    st.write(f"  📋 {col}: {len(unique_values)}種類 - {list(unique_values[:5])}{'...' if len(unique_values) > 5 else ''}")
            
            # 大字名列を探す（優先順位付き）
            oaza_columns = []
            priority_keywords = [
                ('大字', 10),
                ('oaza', 9),
                ('町名', 8),
                ('地区名', 7),
                ('区域', 6),
                ('name', 5),
                ('名称', 5),
                ('地域', 4),
                ('area', 3)
            ]
            
            for col in gdf.columns:
                if col == 'geometry':
                    continue
                    
                col_lower = str(col).lower()
                max_priority = 0
                
                for keyword, priority in priority_keywords:
                    if keyword in col_lower:
                        max_priority = max(max_priority, priority)
                
                if max_priority > 0:
                    oaza_columns.append((col, max_priority))
            
            # 優先度でソート
            oaza_columns.sort(key=lambda x: x[1], reverse=True)
            
            if not oaza_columns:
                st.info("ℹ️ 大字名に該当する列が見つかりません")
                return None
            
            oaza_col = oaza_columns[0][0]
            st.write(f"🏞️ 大字名列として使用: {oaza_col} (優先度: {oaza_columns[0][1]})")
            
            # 丁目名列を探す（優先順位付き）
            chome_columns = []
            chome_keywords = [
                ('丁目', 10),
                ('chome', 9),
                ('番地', 8),
                ('番', 7),
                ('小字', 6),
                ('koaza', 5),
                ('block', 4)
            ]
            
            for col in gdf.columns:
                if col == 'geometry' or col == oaza_col:
                    continue
                    
                col_lower = str(col).lower()
                max_priority = 0
                
                for keyword, priority in chome_keywords:
                    if keyword in col_lower:
                        max_priority = max(max_priority, priority)
                
                if max_priority > 0:
                    chome_columns.append((col, max_priority))
            
            # 優先度でソート
            chome_columns.sort(key=lambda x: x[1], reverse=True)
            
            # 大字名ごとに丁目を集計
            oaza_values = gdf[oaza_col].dropna().unique()
            st.write(f"📊 発見された大字数: {len(oaza_values)}")
            
            for oaza in oaza_values:
                normalized_oaza = self._normalize_area_name(oaza)
                
                if normalized_oaza:
                    area_data[normalized_oaza] = []
                    
                    if chome_columns:
                        chome_col = chome_columns[0][0]
                        st.write(f"🏘️ 丁目名列として使用: {chome_col} (優先度: {chome_columns[0][1]})")
                        
                        # 該当する大字の丁目データを取得
                        oaza_data = gdf[gdf[oaza_col] == oaza]
                        chome_values = oaza_data[chome_col].dropna().unique()
                        
                        chome_str_list = []
                        for chome in chome_values:
                            normalized_chome = self._normalize_area_name(chome)
                            if normalized_chome:
                                chome_str_list.append(normalized_chome)
                        
                        area_data[normalized_oaza] = sorted(list(set(chome_str_list))) if chome_str_list else ["丁目データなし"]
                    else:
                        area_data[normalized_oaza] = ["丁目データなし"]
            
            # 空のエリアデータを除外
            area_data = {k: v for k, v in area_data.items() if k and v}
            
            # デバッグ用：抽出されたデータを表示
            st.write("📋 抽出された大字・丁目データ:")
            for oaza, chome_list in list(area_data.items())[:5]:
                st.write(f"  🏞️ {oaza}: {', '.join(chome_list[:3])}{'...' if len(chome_list) > 3 else ''}")
            if len(area_data) > 5:
                st.write(f"  ... 他{len(area_data)-5}個")
            
            return area_data if area_data else None
            
        except Exception as e:
            st.error(f"❌ GDF大字・丁目データ抽出エラー: {str(e)}")
            return None

    def _extract_area_data_from_df(self, df: pd.DataFrame) -> Optional[Dict[str, List[str]]]:
        """Pandasデータフレームから大字・丁目データを抽出（改善版）"""
        try:
            area_data = {}
            
            st.write("🔍 データフレーム列の詳細分析:")
            
            # 全列の詳細情報を表示
            for col in df.columns:
                unique_values = df[col].dropna().unique()
                st.write(f"  📋 {col}: {len(unique_values)}種類 - {list(unique_values[:5])}{'...' if len(unique_values) > 5 else ''}")
            
            # 大字名列を探す（優先順位付き）
            oaza_columns = []
            priority_keywords = [
                ('大字', 10),
                ('oaza', 9),
                ('町名', 8),
                ('地区名', 7),
                ('区域', 6),
                ('name', 5),
                ('名称', 5),
                ('地域', 4),
                ('area', 3)
            ]
            
            for col in df.columns:
                col_lower = str(col).lower()
                max_priority = 0
                
                for keyword, priority in priority_keywords:
                    if keyword in col_lower:
                        max_priority = max(max_priority, priority)
                
                if max_priority > 0:
                    oaza_columns.append((col, max_priority))
            
            # 優先度でソート
            oaza_columns.sort(key=lambda x: x[1], reverse=True)
            
            if not oaza_columns:
                st.info("ℹ️ 大字名に該当する列が見つかりません")
                return None
            
            oaza_col = oaza_columns[0][0]
            st.write(f"🏞️ 大字名列として使用: {oaza_col} (優先度: {oaza_columns[0][1]})")
            
            # 丁目名列を探す
            chome_columns = []
            chome_keywords = [
                ('丁目', 10),
                ('chome', 9),
                ('番地', 8),
                ('番', 7),
                ('小字', 6),
                ('koaza', 5),
                ('block', 4)
            ]
            
            for col in df.columns:
                if col == oaza_col:
                    continue
                    
                col_lower = str(col).lower()
                max_priority = 0
                
                for keyword, priority in chome_keywords:
                    if keyword in col_lower:
                        max_priority = max(max_priority, priority)
                
                if max_priority > 0:
                    chome_columns.append((col, max_priority))
            
            # 大字名一覧を取得し正規化
            oaza_values = df[oaza_col].dropna().unique()
            st.write(f"📊 発見された大字候補数: {len(oaza_values)}")
            
            for oaza in oaza_values:
                normalized_oaza = self._normalize_area_name(oaza)
                
                if normalized_oaza:
                    if chome_columns:
                        chome_col = chome_columns[0][0]
                        st.write(f"🏘️ 丁目名列として使用: {chome_col}")
                        
                        # 該当する大字の丁目データを取得
                        oaza_data = df[df[oaza_col] == oaza]
                        chome_values = oaza_data[chome_col].dropna().unique()
                        
                        chome_str_list = []
                        for chome in chome_values:
                            normalized_chome = self._normalize_area_name(chome)
                            if normalized_chome:
                                chome_str_list.append(normalized_chome)
                        
                        area_data[normalized_oaza] = sorted(list(set(chome_str_list))) if chome_str_list else ["丁目データなし"]
                    else:
                        area_data[normalized_oaza] = ["丁目データなし"]
            
            # デバッグ用：抽出されたデータを表示
            st.write("📋 抽出された大字・丁目データ:")
            for oaza, chome_list in list(area_data.items())[:5]:
                st.write(f"  🏞️ {oaza}: {', '.join(chome_list[:3])}{'...' if len(chome_list) > 3 else ''}")
            if len(area_data) > 5:
                st.write(f"  ... 他{len(area_data)-5}個")
            
            return area_data if area_data else None
            
        except Exception as e:
            st.error(f"❌ DF大字・丁目データ抽出エラー: {str(e)}")
            return None

    def _create_basic_area_data_from_gdf(self, gdf: gpd.GeoDataFrame) -> bool:
        """GeoDataFrameから基本的なエリアデータを作成（改善版）"""
        try:
            # 地域に関連する列を探す
            area_columns = []
            keywords = [
                ('name', 10),
                ('名', 9),
                ('地区', 8),
                ('区域', 7),
                ('町', 6),
                ('村', 5),
                ('area', 4)
            ]
            
            for col in gdf.columns:
                if col == 'geometry':
                    continue
                    
                col_lower = str(col).lower()
                max_priority = 0
                
                for keyword, priority in keywords:
                    if keyword in col_lower:
                        max_priority = max(max_priority, priority)
                
                if max_priority > 0:
                    area_columns.append((col, max_priority))
            
            # 優先度でソート
            area_columns.sort(key=lambda x: x[1], reverse=True)
            
            if area_columns:
                area_col = area_columns[0][0]
                unique_areas = gdf[area_col].dropna().unique()
                
                area_data = {}
                for area in unique_areas[:20]:  # 最大20個まで
                    normalized_area = self._normalize_area_name(area)
                    if normalized_area:
                        area_data[normalized_area] = ["データなし"]
                
                if area_data:
                    st.session_state.area_data = area_data
                    st.success(f"✅ 基本エリアデータを作成: {len(area_data)}個")
                    return True
            
            # フォールバック：ダミーデータ
            return self._create_dummy_area_data("Shapefile")
            
        except Exception as e:
            st.warning(f"⚠️ 基本エリアデータ作成エラー: {str(e)}")
            return self._create_dummy_area_data("Shapefile")

    def _create_dummy_area_data(self, source_name: str) -> bool:
        """ダミーの大字・丁目データを作成（改善版）"""
        try:
            # 沖縄県のサンプルデータ（実在の大字・丁目）
            dummy_area_data = {
                "那覇": ["1丁目", "2丁目", "3丁目"],
                "首里": ["1丁目", "2丁目", "3丁目", "4丁目", "5丁目"],
                "真嘉比": ["1丁目", "2丁目", "3丁目"],
                "泊": ["1丁目", "2丁目", "3丁目"],
                "久茂地": ["1丁目", "2丁目", "3丁目"],
                "牧志": ["1丁目", "2丁目", "3丁目"],
                "安里": ["1丁目", "2丁目"],
                "上原": ["1丁目", "2丁目", "3丁目"],
                "宮里": ["1丁目", "2丁目", "3丁目", "4丁目"],
                "普天間": ["1丁目", "2丁目", "3丁目", "4丁目"],
                "内間": ["1丁目", "2丁目", "3丁目"],
                "経塚": ["1丁目", "2丁目"],
                "大山": ["1丁目", "2丁目", "3丁目", "4丁目", "5丁目", "6丁目", "7丁目"],
                "宜野湾": ["1丁目", "2丁目", "3丁目"],
                "新城": ["1丁目", "2丁目"],
                "我如古": ["1丁目", "2丁目", "3丁目", "4丁目"]
            }
            
            st.session_state.area_data = dummy_area_data
            st.warning(f"⚠️ {source_name}から適切なデータが抽出できませんでした")
            st.info(f"💡 ダミーデータで継続します（{len(dummy_area_data)}個の大字）")
            
            return True
            
        except Exception as e:
            st.error(f"❌ ダミーデータ作成エラー: {str(e)}")
            return False

    def _process_data_file(self, file_content: bytes, file_extension: str) -> bool:
        """データファイル（CSV/Excel）の処理"""
        try:
            if file_extension == '.csv':
                # 複数エンコーディングを試行
                encodings = ['utf-8', 'shift-jis', 'cp932', 'utf-8-sig']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                        st.success(f"✅ CSV読み込み成功 (エンコーディング: {encoding})")
                        break
                    except:
                        continue
                
                if df is None:
                    st.error("❌ CSV読み込み失敗")
                    return False
                    
            else:  # Excel
                df = pd.read_excel(io.BytesIO(file_content))
            
            st.write(f"📊 データファイル情報:")
            st.write(f"  - 行数: {len(df):,}")
            st.write(f"  - 列数: {len(df.columns)}")
            
            # エリアデータを抽出
            area_data = self._extract_area_data_from_df(df)
            if area_data:
                st.session_state.area_data = area_data
                st.success(f"✅ エリアデータを抽出: {len(area_data)}個")
                return True
            
            return self._create_dummy_area_data("データファイル")
            
        except Exception as e:
            st.error(f"❌ データファイル処理エラー: {str(e)}")
            return False

    def _process_shapefile(self, file_content: bytes, file_name: str) -> bool:
        """単体Shapefileの処理"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.shp', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file.flush()
                
                gdf = gpd.read_file(temp_file.name)
                
                area_data = self._extract_area_data_from_gdf(gdf)
                if area_data:
                    st.session_state.area_data = area_data
                    st.success(f"✅ Shapefile処理完了: {len(area_data)}個")
                    return True
                
                return self._create_dummy_area_data("Shapefile")
                
        except Exception as e:
            st.error(f"❌ Shapefile処理エラー: {str(e)}")
            return False
        finally:
            try:
                os.unlink(temp_file.name)
            except:
                pass

    def _process_gis_file(self, file_content: bytes, file_extension: str) -> bool:
        """GISファイル（KML/GeoJSON）の処理"""
        try:
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file.flush()
                
                gdf = gpd.read_file(temp_file.name)
                
                area_data = self._extract_area_data_from_gdf(gdf)
                if area_data:
                    st.session_state.area_data = area_data
                    st.success(f"✅ GISファイル処理完了: {len(area_data)}個")
                    return True
                
                return self._create_dummy_area_data("GISファイル")
                
        except Exception as e:
            st.error(f"❌ GISファイル処理エラー: {str(e)}")
            return False
        finally:
            try:
                os.unlink(temp_file.name)
            except:
                pass