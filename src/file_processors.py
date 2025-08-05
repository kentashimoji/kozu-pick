#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src/file_processors.py - ファイル処理専用クラス（完全修正版）
ZIPファイル内のShapefile処理に対応
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import zipfile
import io
import tempfile
import os
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
                    for file in file_list[:10]:  # 最初の10個まで表示
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
        """GeoPandasデータフレームから大字・丁目データを抽出"""
        try:
            area_data = {}
            
            # 大字名列を探す（複数パターン）
            oaza_columns = []
            for col in gdf.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['大字', 'oaza', '地区', '町名']):
                    oaza_columns.append(col)
            
            # 丁目名列を探す
            chome_columns = []
            for col in gdf.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['丁目', 'chome', '番地']):
                    chome_columns.append(col)
            
            if not oaza_columns:
                st.info("ℹ️ 大字名に該当する列が見つかりません")
                return None
            
            oaza_col = oaza_columns[0]
            st.write(f"🏞️ 大字名列として使用: {oaza_col}")
            
            # 大字名ごとに丁目を集計
            for oaza in gdf[oaza_col].dropna().unique():
                oaza_str = str(oaza).strip()
                if oaza_str and oaza_str != 'nan':
                    area_data[oaza_str] = []
                    
                    if chome_columns:
                        chome_col = chome_columns[0]
                        st.write(f"🏘️ 丁目名列として使用: {chome_col}")
                        
                        # 該当する大字の丁目データを取得
                        oaza_data = gdf[gdf[oaza_col] == oaza]
                        chome_list = oaza_data[chome_col].dropna().unique()
                        
                        chome_str_list = []
                        for chome in chome_list:
                            chome_str = str(chome).strip()
                            if chome_str and chome_str != 'nan':
                                chome_str_list.append(chome_str)
                        
                        area_data[oaza_str] = sorted(chome_str_list) if chome_str_list else ["丁目データなし"]
                    else:
                        area_data[oaza_str] = ["丁目データなし"]
            
            # 空のエリアデータを除外
            area_data = {k: v for k, v in area_data.items() if k and v}
            
            return area_data if area_data else None
            
        except Exception as e:
            st.error(f"❌ GDF大字・丁目データ抽出エラー: {str(e)}")
            return None

    def _extract_area_data_from_df(self, df: pd.DataFrame) -> Optional[Dict[str, List[str]]]:
        """Pandasデータフレームから大字・丁目データを抽出"""
        try:
            area_data = {}
            
            # 大字名列を探す
            oaza_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(keyword in col_str for keyword in ['大字', 'oaza', '地区', '町名']):
                    oaza_columns.append(col)
            
            if not oaza_columns:
                st.info("ℹ️ 大字名に該当する列が見つかりません")
                return None
            
            oaza_col = oaza_columns[0]
            st.write(f"🏞️ 大字名列として使用: {oaza_col}")
            
            # 大字名一覧を取得
            for oaza in df[oaza_col].dropna().unique():
                oaza_str = str(oaza).strip()
                if oaza_str and oaza_str != 'nan':
                    area_data[oaza_str] = ["丁目データなし"]
            
            return area_data if area_data else None
            
        except Exception as e:
            st.error(f"❌ DF大字・丁目データ抽出エラー: {str(e)}")
            return None

    def _create_basic_area_data_from_gdf(self, gdf: gpd.GeoDataFrame) -> bool:
        """GeoDataFrameから基本的なエリアデータを作成"""
        try:
            # 地域に関連する列を探す
            area_columns = []
            for col in gdf.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['名', 'name', '地', '区', '町', '村']):
                    area_columns.append(col)
            
            if area_columns:
                area_col = area_columns[0]
                unique_areas = gdf[area_col].dropna().unique()
                
                area_data = {}
                for area in unique_areas[:20]:  # 最大20個まで
                    area_str = str(area).strip()
                    if area_str and area_str != 'nan':
                        area_data[area_str] = ["データなし"]
                
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
        """ダミーの大字・丁目データを作成"""
        try:
            # 沖縄県のサンプルデータ
            dummy_area_data = {
                "那覇": ["1丁目", "2丁目", "3丁目"],
                "首里": ["1丁目", "2丁目", "3丁目", "4丁目", "5丁目"],
                "真嘉比": ["1丁目", "2丁目", "3丁目"],
                "泊": ["1丁目", "2丁目", "3丁目"],
                "久茂地": ["1丁目", "2丁目", "3丁目"],
                "牧志": ["1丁目", "2丁目", "3丁目"],
                "安里": ["1丁目", "2丁目"],
                "上原": ["1丁目", "2丁目", "3丁目"],
                "宮里": ["1丁目", "2丁目"],
                "普天間": ["1丁目", "2丁目", "3丁目", "4丁目"]
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