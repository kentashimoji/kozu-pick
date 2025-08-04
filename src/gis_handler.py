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

    def is_gis_available(self):
        """GIS機能が利用可能かチェック"""
        return GEOPANDAS_AVAILABLE

    def extract_zip_file(self, zip_path, temp_dir):
        """ZIPファイルを展開"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            extracted_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.shp', '.kml', '.geojson')):
                        extracted_files.append(os.path.join(root, file))

            return extracted_files
        except Exception as e:
            st.error(f"ZIPファイルの展開に失敗しました: {str(e)}")
            return []

    def load_gis_file(self, file_path):
        """GISファイルを読み込み"""
        if not self.is_gis_available():
            st.error("GIS機能が利用できません。GeoPandasをインストールしてください。")
            return None

        try:
            if file_path.lower().endswith('.shp'):
                return gpd.read_file(file_path)
            elif file_path.lower().endswith('.kml'):
                return gpd.read_file(file_path, driver='KML')
            else:
                return gpd.read_file(file_path)
        except Exception as e:
            st.error(f"GISファイル読み込みエラー: {str(e)}")
            return None
