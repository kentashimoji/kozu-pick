# -*- coding: utf-8 -*-

"""
GIS処理機能
"""
import sys
from pathlib import Path


project_root = Path(__file__).resolve().parent.parent  # 2階層上
sys.path.insert(0, str(project_root))


import os
import zipfile
import tempfile
import streamlit as st
from config.config import GIS_CONFIG
from src.kozu_extractor import KozuWebExtractor

try:
    import geopandas as gpd
    import fiona
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

class GISHandler:
    def __init__(self):
        self.supported_extensions = GIS_CONFIG["supported_extensions"]
        self.shapefile_required = GIS_CONFIG["shapefile_required"]
        self.kozu_extractor = KozuWebExtractor()
    
    def is_gis_available(self):
        """GIS機能が利用可能かチェック"""
        return GEOPANDAS_AVAILABLE
    
    def load_gis_data(self, file_path_or_url):
        """GISデータを読み込み（ファイルパスまたはURL）"""
        if not self.is_gis_available():
            st.error("GIS機能が利用できません。GeoPandasをインストールしてください。")
            return None
        
        try:
            if file_path_or_url.startswith('http'):
                # URLの場合：一時ファイルにダウンロードしてから読み込み
                return self._load_from_url(file_path_or_url)
            else:
                # ローカルファイルの場合
                return self._load_from_file(file_path_or_url)
        except Exception as e:
            st.error(f"GISファイル読み込みエラー: {str(e)}")
            return None
    
    def _load_from_url(self, url):
        """URLからGISデータを読み込み"""
        import requests
        import tempfile
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            # 読み込み
            gdf = self._load_from_file(tmp_path)
            
            # 一時ファイルを削除
            os.unlink(tmp_path)
            
            return gdf
            
        except Exception as e:
            st.error(f"URL読み込みエラー: {str(e)}")
            return None
    
    def _load_from_file(self, file_path):
        """ファイルからGISデータを読み込み"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.zip':
            return self._load_from_zip(file_path)
        elif file_ext == '.shp':
            return gpd.read_file(file_path)
        elif file_ext == '.kml':
            return gpd.read_file(file_path, driver='KML')
        elif file_ext == '.geojson':
            return gpd.read_file(file_path)
        else:
            raise ValueError(f"対応していないファイル形式: {file_ext}")
    
    def _load_from_zip(self, zip_path):
        """ZIPファイルからShapefileを読み込み"""
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # ZIPファイルを展開
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)
                
                # Shapefileを検索
                shp_files = []
                for root, dirs, files in os.walk(tmp_dir):
                    for file in files:
                        if file.lower().endswith('.shp'):
                            shp_files.append(os.path.join(root, file))
                
                if not shp_files:
                    raise ValueError("ZIPファイル内にShapefileが見つかりません")
                
                # 最初のShapefileを読み込み
                return gpd.read_file(shp_files[0])
                
        except Exception as e:
            raise Exception(f"ZIP読み込みエラー: {str(e)}")
    
    def get_files_from_web_folder(self, folder_url, file_extensions=None):
        """Web上のフォルダからファイルを取得（KozuWebExtractorを使用）"""
        return self.kozu_extractor.get_files_from_web_folder(folder_url, file_extensions)
    
    def extract_kozu_data(self, gdf, oaza, chome, koaza, chiban, range_m):
        """小字データ抽出（KozuWebExtractorを使用）"""
        return self.kozu_extractor.extract_data(gdf, oaza, chome, koaza, chiban, range_m)
    
    def get_chome_options(self, gdf, selected_oaza):
        """丁目の選択肢を取得"""
        return self.kozu_extractor.get_chome_options(gdf, selected_oaza)
    
    def get_koaza_options(self, gdf, selected_oaza, selected_chome=None):
        """小字の選択肢を取得"""
        return self.kozu_extractor.get_koaza_options(gdf, selected_oaza, selected_chome)
