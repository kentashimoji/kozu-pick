#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
都道府県・市区町村選択ツール v33.0 (GIS対応版)
GitHub ExcelファイルからデータをダウンロードしてWebアプリケーションを作成
GISファイル（ZIP、Shapefile、KML）から大字・丁目データを抽出

必要なライブラリ:
pip install streamlit pandas openpyxl requests geopandas fiona lxml

実行方法:
streamlit run prefecture_city_selector_streamlit.py
"""

import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime
import os
import glob
import zipfile
import tempfile
import re
import shutil

# GIS関連ライブラリのインポート
try:
    import geopandas as gpd
    import fiona
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    st.warning("⚠️ GeoPandasが利用できません。GISファイルの読み込みにはGeoPandasのインストールが必要です。")

try:
    from lxml import etree
    XML_AVAILABLE = True
except ImportError:
    XML_AVAILABLE = False

# ページ設定
st.set_page_config(
    page_title="都道府県・市区町村選択ツール v33.0",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class PrefectureCitySelectorGIS:
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """セッション状態を初期化"""
        if 'prefecture_data' not in st.session_state:
            st.session_state.prefecture_data = {}
        if 'prefecture_codes' not in st.session_state:
            st.session_state.prefecture_codes = {}
        if 'city_codes' not in st.session_state:
            st.session_state.city_codes = {}
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'current_url' not in st.session_state:
            st.session_state.current_url = ""
        if 'selected_prefecture' not in st.session_state:
            st.session_state.selected_prefecture = ""
        if 'selected_city' not in st.session_state:
            st.session_state.selected_city = ""
        if 'selected_file_path' not in st.session_state:
            st.session_state.selected_file_path = ""
        if 'area_data' not in st.session_state:
            st.session_state.area_data = {}
        if 'selected_oaza' not in st.session_state:
            st.session_state.selected_oaza = ""
        if 'selected_chome' not in st.session_state:
            st.session_state.selected_chome = ""
        if 'folder_path' not in st.session_state:
            st.session_state.folder_path = ""
    
    def load_data_from_github(self, url):
        """GitHubからデータを読み込み"""
        try:
            if not url:
                st.error("URLを入力してください")
                return False
                
            if "raw.githubusercontent.com" not in url:
                st.warning("GitHub Raw URLではないようです。正しいURLは 'raw.githubusercontent.com' を含んでいます。")
            
            # プログレスバーを表示
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # データをダウンロード
            status_text.text("データをダウンロードしています...")
            progress_bar.progress(25)
            
            headers = {'User-Agent': 'PrefectureCitySelector/33.0'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            progress_bar.progress(50)
            status_text.text("ファイルを解析しています...")
            
            # ファイル形式を判定して読み込み
            if url.lower().endswith('.csv'):
                df = pd.read_csv(BytesIO(response.content), encoding='utf-8-sig')
            else:
                excel_data = BytesIO(response.content)
                df = pd.read_excel(excel_data)
            
            progress_bar.progress(75)
            status_text.text("データを処理しています...")
            
            # データを整理（団体コードと共に保存）
            prefecture_data = {}
            prefecture_codes = {}
            city_codes = {}
            
            prefecture_cols = [col for col in df.columns if '都道府県' in col and '漢字' in col]
            city_cols = [col for col in df.columns if '市区町村' in col and '漢字' in col]
            code_col = '団体コード'
            
            if not prefecture_cols or not city_cols:
                st.error(f"適切な列が見つかりません。利用可能な列: {list(df.columns)}")
                return False
            
            prefecture_col = prefecture_cols[0]
            city_col = city_cols[0]
            
            for _, row in df.iterrows():
                prefecture = row.get(prefecture_col)
                city = row.get(city_col)
                code = row.get(code_col, '')
                
                if pd.notna(prefecture):
                    if prefecture not in prefecture_data:
                        prefecture_data[prefecture] = {}
                        # 都道府県コードを保存（最初の2桁）
                        if pd.notna(code):
                            prefecture_codes[prefecture] = str(code)[:2]
                    
                    if pd.notna(city):
                        # 市区町村の詳細情報を保存
                        full_code = str(code) if pd.notna(code) else '999999'
                        prefecture_code = full_code[:2]  # 1-2桁目
                        city_code = full_code[2:5] if len(full_code) >= 5 else '999'  # 3-5桁目
                        
                        prefecture_data[prefecture][city] = {
                            'full_code': full_code,
                            'city_code': city_code
                        }
                        
                        # 全体のコード情報を保存
                        city_codes[f"{prefecture}_{city}"] = {
                            'prefecture_code': prefecture_code,
                            'city_code': city_code,
                            'full_code': full_code
                        }
            
            # 都道府県を団体コード順にソート（沖縄県を最初に）
            def sort_prefectures(prefectures_dict):
                # 沖縄県を特別扱い
                sorted_prefs = []
                other_prefs = []
                
                for pref in prefectures_dict.keys():
                    if pref == '沖縄県':
                        sorted_prefs.insert(0, pref)  # 最初に挿入
                    else:
                        other_prefs.append(pref)
                
                # 沖縄県以外を団体コード順にソート
                other_prefs.sort(key=lambda x: prefecture_codes.get(x, '99'))
                
                return sorted_prefs + other_prefs
            
            # 市区町村を団体コード順にソート
            for prefecture in prefecture_data:
                cities_with_info = prefecture_data[prefecture]
                sorted_cities = sorted(cities_with_info.keys(), 
                                     key=lambda x: cities_with_info[x]['full_code'])
                # ソート済みの市区町村辞書を作成
                sorted_cities_dict = {}
                for city in sorted_cities:
                    sorted_cities_dict[city] = cities_with_info[city]
                prefecture_data[prefecture] = sorted_cities_dict
            
            # ソート済みデータで辞書を再構築
            sorted_prefecture_data = {}
            sorted_prefectures = sort_prefectures(prefecture_data)
            for prefecture in sorted_prefectures:
                sorted_prefecture_data[prefecture] = prefecture_data[prefecture]
            
            # セッション状態にコード情報も保存
            st.session_state.prefecture_data = sorted_prefecture_data
            st.session_state.prefecture_codes = prefecture_codes
            st.session_state.city_codes = city_codes
            st.session_state.data_loaded = True
            st.session_state.current_url = url
            
            progress_bar.progress(100)
            status_text.text("✅ データの読み込みが完了しました！")
            
            # 統計情報を表示
            total_prefectures = len(sorted_prefecture_data)
            total_cities = sum(len(cities) for cities in sorted_prefecture_data.values())
            
            st.success(f"📊 読み込み完了: {total_prefectures}都道府県, {total_cities}市区町村")
            
            return True
            
        except requests.RequestException as e:
            st.error(f"ネットワークエラー: {str(e)}")
            return False
        except Exception as e:
            st.error(f"データの読み込みに失敗しました: {str(e)}")
            return False
    
    def find_files_by_code(self, folder_path, prefecture_code, city_code):
        """団体コードに基づいてGISファイルを検索"""
        if not folder_path or not os.path.exists(folder_path):
            return [], {}
        
        # 検索パターンを作成
        search_code = f"{prefecture_code}{city_code}"
        
        # 対応するGISファイル拡張子
        extensions = ['*.zip', '*.shp', '*.kml', '*.shx', '*.prj', '*.dbf', '*.cpg']
        found_files = []
        
        for ext in extensions:
            pattern = os.path.join(folder_path, f"*{search_code}*{ext}")
            files = glob.glob(pattern, recursive=False)
            found_files.extend(files)
        
        # Shapefileセットを優先的にグループ化
        shapefile_sets = self.group_shapefile_sets(found_files)
        
        return sorted(list(set(found_files))), shapefile_sets
    
    def group_shapefile_sets(self, files):
        """Shapefileの関連ファイルをセットでグループ化"""
        shapefile_sets = {}
        
        for file_path in files:
            base_name = os.path.splitext(file_path)[0]
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.shp', '.shx', '.prj', '.dbf', '.cpg']:
                if base_name not in shapefile_sets:
                    shapefile_sets[base_name] = []
                shapefile_sets[base_name].append(file_path)
        
        # 完全なShapefileセット（.shp, .shx, .dbfが全て揃っている）のみを返す
        complete_sets = {}
        for base_name, file_list in shapefile_sets.items():
            extensions = [os.path.splitext(f)[1].lower() for f in file_list]
            if '.shp' in extensions and '.shx' in extensions and '.dbf' in extensions:
                complete_sets[base_name] = file_list
        
        return complete_sets
    
    def extract_zip_file(self, zip_path, temp_dir):
        """ZIPファイルを一時ディレクトリに展開"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 展開されたファイルからGISファイルを検索
            extracted_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.shp', '.kml', '.geojson')):
                        extracted_files.append(os.path.join(root, file))
            
            return extracted_files
        except Exception as e:
            st.error(f"ZIPファイルの展開に失敗しました: {str(e)}")
            return []
    
    def load_area_data(self, file_path):
        """選択されたGISファイルから大字・丁目データを読み込み"""
        try:
            if not GEOPANDAS_AVAILABLE:
                st.error("GeoPandasがインストールされていません。GISファイルの読み込みにはGeoPandasが必要です。")
                return False
            
            if not file_path or not os.path.exists(file_path):
                st.error("ファイルが存在しません。")
                return False
            
            # ファイル拡張子に基づいて読み込み方法を決定
            file_ext = os.path.splitext(file_path)[1].lower()
            gdf = None
            temp_dir = None
            
            try:
                if file_ext == '.zip':
                    # ZIPファイルの場合は展開してからShapefileを読み込み
                    temp_dir = tempfile.mkdtemp()
                    extracted_files = self.extract_zip_file(file_path, temp_dir)
                    
                    if not extracted_files:
                        st.error("ZIPファイル内にGISファイルが見つかりませんでした")
                        return False
                    
                    # 最初に見つかったGISファイルを使用
                    gdf = gpd.read_file(extracted_files[0])
                    
                elif file_ext == '.shp':
                    # Shapefileの読み込み
                    gdf = gpd.read_file(file_path)
                    
                elif file_ext == '.kml':
                    # KMLファイルの読み込み
                    if XML_AVAILABLE:
                        gdf = gpd.read_file(file_path, driver='KML')
                    else:
                        st.error("KMLファイルの読み込みにはlxmlライブラリが必要です")
                        return False
                
                else:
                    st.error(f"対応していないファイル形式です: {file_ext}")
                    return False
                
                if gdf is None or gdf.empty:
                    st.error("ファイルからデータを読み込めませんでした")
                    return False
                
                # 大字・丁目の列を検索
                area_data = self.extract_area_from_gis(gdf)
                
                if not area_data:
                    st.error("大字・丁目情報を抽出できませんでした")
                    return False
                
                st.session_state.area_data = area_data
                st.session_state.selected_file_path = file_path
                
                # ファイル情報を表示
                st.info(f"📊 読み込み完了: {len(gdf)}件のデータ、{len(area_data)}個の大字を検出")
                
                return True
                
            finally:
                # 一時ディレクトリをクリーンアップ
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            st.error(f"GISファイルの読み込みに失敗しました: {str(e)}")
            return False
    
    def extract_area_from_gis(self, gdf):
        """GISデータから大字・丁目を抽出"""
        # 可能性のある列名パターン
        oaza_patterns = ['大字', 'おおあざ', 'オオアザ', 'OAZA', 'oaza', '字', '町名', 'TOWN', 'town']
        chome_patterns = ['丁目', 'ちょうめ', 'チョウメ', 'CHOME', 'chome', '丁', '番地']
        address_patterns = ['住所', 'address', 'ADDRESS', '所在地', '地名', 'name', 'NAME']
        
        area_data = {}
        
        # 列名を取得
        columns = [str(col).lower() for col in gdf.columns]
        
        # 大字・丁目の専用列を検索
        oaza_col = None
        chome_col = None
        address_col = None
        
        for col in gdf.columns:
            col_lower = str(col).lower()
            
            # 大字列の検索
            if not oaza_col and any(pattern.lower() in col_lower for pattern in oaza_patterns):
                oaza_col = col
            
            # 丁目列の検索
            if not chome_col and any(pattern.lower() in col_lower for pattern in chome_patterns):
                chome_col = col
            
            # 住所列の検索
            if not address_col and any(pattern.lower() in col_lower for pattern in address_patterns):
                address_col = col
        
        # データ抽出
        if oaza_col:
            # 大字の専用列がある場合
            for _, row in gdf.iterrows():
                oaza = str(row[oaza_col]) if pd.notna(row[oaza_col]) else ""
                oaza = oaza.strip()
                
                if oaza and oaza != 'nan':
                    if oaza not in area_data:
                        area_data[oaza] = set()
                    
                    # 丁目データがある場合
                    if chome_col and pd.notna(row[chome_col]):
                        chome = str(row[chome_col]).strip()
                        if chome and chome != 'nan':
                            area_data[oaza].add(chome)
        
        elif address_col:
            # 住所列から抽出
            for _, row in gdf.iterrows():
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
        
        else:
            # 全ての列から住所らしい情報を抽出
            for col in gdf.columns:
                if gdf[col].dtype == 'object':  # 文字列型の列のみ
                    for _, row in gdf.iterrows():
                        value = str(row[col]) if pd.notna(row[col]) else ""
                        
                        # 大字・丁目パターンを検索
                        if '大字' in value or '丁目' in value:
                            oaza_matches = re.findall(r'大字(.+?)(?:[0-9]|丁目|番地|$)', value)
                            chome_matches = re.findall(r'([0-9]+丁目)', value)
                            
                            for oaza_match in oaza_matches:
                                oaza = oaza_match.strip()
                                if oaza:
                                    if oaza not in area_data:
                                        area_data[oaza] = set()
                                    
                                    for chome in chome_matches:
                                        area_data[oaza].add(chome)
        
        # SetをListに変換してソート
        for oaza in area_data:
            area_data[oaza] = sorted(list(area_data[oaza]))
        
        return area_data
    
    def render_main_page(self):
        """メインページを描画"""
        st.title("🏛️ 都道府県・市区町村選択ツール v33.0")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("**GitHub ExcelファイルからデータをダウンロードしてWebアプリケーションを作成**")
        with col2:
            st.metric("バージョン", "33.0")
        with col3:
            st.metric("プラットフォーム", "Streamlit + GIS")
        
        st.markdown("---")
        
        # データ読み込みセクション
        st.header("📡 データソース設定")
        
        default_url = "https://raw.githubusercontent.com/USERNAME/REPOSITORY/main/000925835.xlsx"
        url = st.text_input(
            "GitHub ExcelファイルURL:",
            value=st.session_state.current_url or default_url,
            help="GitHubでファイルを開き、'Raw'ボタンをクリックした時のURLを入力してください"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 データを読み込み", type="primary"):
                self.load_data_from_github(url)
        
        with col2:
            if st.button("🗑️ データをクリア"):
                st.session_state.prefecture_data = {}
                st.session_state.prefecture_codes = {}
                st.session_state.city_codes = {}
                st.session_state.data_loaded = False
                st.session_state.current_url = ""
                st.session_state.selected_prefecture = ""
                st.session_state.selected_city = ""
                st.session_state.selected_file_path = ""
                st.session_state.area_data = {}
                st.session_state.selected_oaza = ""
                st.session_state.selected_chome = ""
                st.success("データをクリアしました")
                st.experimental_rerun()
        
        # データが読み込まれている場合の選択UI
        if st.session_state.data_loaded and st.session_state.prefecture_data:
            st.markdown("---")
            st.header("🎯 地域選択")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 都道府県は既にソート済み（沖縄県が最初、その後団体コード順）
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
            
            with col2:
                if st.session_state.selected_prefecture:
                    # 市区町村は既に団体コード順でソート済み
                    cities_dict = st.session_state.prefecture_data[st.session_state.selected_prefecture]
                    cities = list(cities_dict.keys())
                    
                    selected_city = st.selectbox(
                        "市区町村を選択してください:",
                        ["選択してください"] + cities,
                        key="city_select"
                    )
                    
                    if selected_city != "選択してください":
                        st.session_state.selected_city = selected_city
                else:
                    st.selectbox(
                        "市区町村を選択してください:",
                        ["まず都道府県を選択してください"],
                        disabled=True
                    )
            
            # 選択結果の表示
            if st.session_state.selected_prefecture and st.session_state.selected_city:
                st.markdown("---")
                st.header("📍 選択結果")
                
                # コード情報を取得
                prefecture_code = st.session_state.prefecture_codes.get(st.session_state.selected_prefecture, "不明")
                city_key = f"{st.session_state.selected_prefecture}_{st.session_state.selected_city}"
                city_info = st.session_state.city_codes.get(city_key, {})
                city_code = city_info.get('city_code', "不明")
                full_code = city_info.get('full_code', "不明")
                
                result_data = {
                    "都道府県": st.session_state.selected_prefecture,
                    "都道府県コード": prefecture_code,
                    "市区町村": st.session_state.selected_city,
                    "市区町村コード": city_code,
                    "完全な住所": f"{st.session_state.selected_prefecture}{st.session_state.selected_city}",
                    "団体コード（完全）": full_code,
                    "選択日時": datetime.now().strftime('%Y年%m月%d日 %H:%M:%S'),
                    "データソース": st.session_state.current_url[:60] + "..." if len(st.session_state.current_url) > 60 else st.session_state.current_url
                }
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # 重要な情報を強調表示
                    st.subheader("🏛️ 基本情報")
                    st.write(f"**都道府県:** {result_data['都道府県']}")
                    st.write(f"**市区町村:** {result_data['市区町村']}")
                    st.write(f"**完全な住所:** {result_data['完全な住所']}")
                    
                    st.subheader("🔢 コード情報")
                    st.write(f"**都道府県コード:** {result_data['都道府県コード']}")
                    st.write(f"**市区町村コード:** {result_data['市区町村コード']}")
                    st.write(f"**団体コード（完全）:** {result_data['団体コード（完全）']}")
                    
                    st.subheader("ℹ️ その他")
                    st.write(f"**選択日時:** {result_data['選択日時']}")
                    if st.session_state.current_url:
                        st.write(f"**データソース:** {result_data['データソース']}")
                
                with col2:
                    if st.button("📋 結果をコピー"):
                        result_text = "\n".join([f"{k}: {v}" for k, v in result_data.items()])
                        st.code(result_text)
                        st.success("結果を表示しました。上記のテキストをコピーしてください。")
                
                # 大字・丁目選択セクション
                if prefecture_code != "不明" and city_code != "不明":
                    st.markdown("---")
                    st.header("🏘️ 詳細住所選択（GISファイル対応）")
                    
                    # フォルダパス入力
                    folder_path = st.text_input(
                        "📁 GISファイル検索フォルダパス:",
                        value=st.session_state.folder_path,
                        help="大字・丁目データが含まれるGISファイル（ZIP、Shapefile、KML）があるフォルダのパスを入力してください"
                    )
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        if st.button("🔍 GISファイルを検索"):
                            if folder_path:
                                st.session_state.folder_path = folder_path
                                files, shapefile_sets = self.find_files_by_code(folder_path, prefecture_code, city_code)
                                
                                if files or shapefile_sets:
                                    total_files = len(files) + len(shapefile_sets)
                                    st.success(f"✅ {total_files}個のファイル/セットが見つかりました")
                                    
                                    # ファイル選択
                                    selected_file_option = st.selectbox(
                                        "ファイルを選択してください:",
                                        file_options,
                                        key="file_select"
                                    )
                                    
                                    if selected_file_option != "選択してください":
                                        selected_file_path = file_mapping[selected_file_option]
                                        
                                        # ファイル情報を表示
                                        file_info = f"**選択されたファイル:** {os.path.basename(selected_file_path)}"
                                        if selected_file_option.startswith("🗺️"):
                                            # Shapefileセットの場合、構成ファイルを表示
                                            base_name = os.path.splitext(selected_file_path)[0]
                                            related_files = shapefile_sets.get(base_name, [])
                                            if related_files:
                                                file_info += f"\n\n**構成ファイル:**"
                                                for rf in sorted(related_files):
                                                    file_info += f"\n• {os.path.basename(rf)}"
                                        
                                        st.info(file_info)
                                        
                                        if st.button("📖 GISファイルを読み込み"):
                                            with st.spinner("GISファイルを読み込んでいます..."):
                                                if self.load_area_data(selected_file_path):
                                                    st.success("✅ GISファイルの読み込みが完了しました")
                                                    st.experimental_rerun()
                                else:
                                    st.warning(f"⚠️ 団体コード「{prefecture_code}{city_code}」を含むGISファイルが見つかりませんでした")
                                    st.info("**対応ファイル形式:** ZIP, Shapefile(.shp), KML, および関連ファイル(.shx, .prj, .dbf, .cpg)")
                            else:
                                st.error("フォルダパスを入力してください")
                    
                    with col2:
                        # 大字・丁目選択UI
                        if st.session_state.area_data:
                            st.subheader("🏘️ 大字・丁目選択")
                            
                            # 大字選択
                            oaza_list = sorted(st.session_state.area_data.keys())
                            selected_oaza = st.selectbox(
                                "大字を選択してください:",
                                ["選択してください"] + oaza_list,
                                key="oaza_select"
                            )
                            
                            if selected_oaza != "選択してください":
                                st.session_state.selected_oaza = selected_oaza
                                
                                # 丁目選択
                                chome_list = st.session_state.area_data.get(selected_oaza, [])
                                if chome_list:
                                    selected_chome = st.selectbox(
                                        "丁目を選択してください:",
                                        ["選択してください"] + chome_list,
                                        key="chome_select"
                                    )
                                    
                                    if selected_chome != "選択してください":
                                        st.session_state.selected_chome = selected_chome
                                        
                                        # 完全な住所表示
                                        complete_address = f"{st.session_state.selected_prefecture}{st.session_state.selected_city}{selected_oaza}{selected_chome}"
                                        
                                        st.success("🎯 完全な住所が選択されました")
                                        st.write(f"**完全な住所:** {complete_address}")
                                        
                                        # 詳細結果
                                        detailed_result = {
                                            "都道府県": st.session_state.selected_prefecture,
                                            "都道府県コード": prefecture_code,
                                            "市区町村": st.session_state.selected_city,
                                            "市区町村コード": city_code,
                                            "大字": selected_oaza,
                                            "丁目": selected_chome,
                                            "完全な住所": complete_address,
                                            "団体コード": full_code,
                                            "使用ファイル": os.path.basename(st.session_state.selected_file_path),
                                            "選択日時": datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
                                        }
                                        
                                        if st.button("📋 詳細結果をコピー"):
                                            detailed_text = "\n".join([f"{k}: {v}" for k, v in detailed_result.items()])
                                            st.code(detailed_text)
                                            st.success("詳細結果を表示しました")
                                else:
                                    st.info("選択された大字に丁目データがありません")
                        else:
                            st.info("まずGISファイルを検索・読み込みしてください")
    
    def render_data_page(self):
        """データ管理ページを描画"""
        st.title("📊 データ管理")
        
        if not st.session_state.data_loaded or not st.session_state.prefecture_data:
            st.warning("データが読み込まれていません。メインページでデータを読み込んでください。")
            return
        
        # 現在のデータ状態のみ表示
        st.header("ℹ️ 現在の状態")
        
        st.success("✅ データが正常に読み込まれています")
        
        if st.session_state.current_url:
            st.info(f"📡 データソース: {st.session_state.current_url}")
        
        # GISファイル情報
        if st.session_state.selected_file_path:
            st.info(f"🗺️ 読み込み済みGISファイル: {os.path.basename(st.session_state.selected_file_path)}")
        
        # データクリア機能のみ
        st.header("🗑️ データ管理")
        
        if st.button("🗑️ 読み込まれたデータをクリア", type="secondary"):
            if st.session_state.data_loaded:
                st.session_state.prefecture_data = {}
                st.session_state.prefecture_codes = {}
                st.session_state.city_codes = {}
                st.session_state.data_loaded = False
                st.session_state.current_url = ""
                st.session_state.selected_prefecture = ""
                st.session_state.selected_city = ""
                st.session_state.selected_file_path = ""
                st.session_state.area_data = {}
                st.session_state.selected_oaza = ""
                st.session_state.selected_chome = ""
                st.success("データをクリアしました")
                st.experimental_rerun()
            else:
                st.warning("クリアするデータがありません")
    
    def render_about_page(self):
        """情報ページを描画"""
        st.title("ℹ️ アプリケーション情報")
        
        st.markdown("""
        ## 🏛️ 都道府県・市区町村選択ツール v33.0 (GIS対応版)
        
        ### 概要
        GitHubにアップロードされたExcelファイルから日本の都道府県・市区町村データを
        読み込み、さらにGISファイルから大字・丁目レベルまでの詳細な住所選択を可能にする
        Webアプリケーションです。
        
        ### 主な機能
        ✅ **GitHub対応**: GitHub上のExcelファイルの直接読み込み  
        ✅ **階層選択**: 都道府県選択による市区町村の絞り込み  
        ✅ **GIS対応**: ZIP、Shapefile、KMLファイルから大字・丁目を抽出  
        ✅ **団体コード**: 都道府県コード・市区町村コードの表示  
        ✅ **詳細住所**: 大字・丁目レベルまでの完全な住所選択  
        ✅ **リアルタイム**: 選択結果の即時表示  
        ✅ **レスポンシブ**: モバイル・デスクトップ対応  
        ✅ **シンプル**: 直感的で使いやすいインターフェース
        
        ### 必要なライブラリ
        ```bash
        pip install streamlit pandas openpyxl requests geopandas fiona lxml
        ```
        
        ### 実行方法
        ```bash
        streamlit run prefecture_city_selector_streamlit.py
        ```
        
        ### GitHub Raw URLの取得方法
        1. GitHubでファイルを開く
        2. 「Raw」ボタンをクリック  
        3. ブラウザのアドレスバーからURLをコピー
        
        ### 対応ファイル形式
        **基本データ:**
        - Excel (.xlsx, .xls)
        - CSV (.csv)
        
        **GISデータ:**
        - **ZIP**: 圧縮されたShapefileセット
        - **Shapefile**: .shp, .shx, .prj, .dbf, .cpg
        - **KML**: GoogleEarth形式のGISデータ
        
        ### 団体コード体系
        ```
        団体コード（6桁）の構造:
        472016 の場合:
        ├─ 47:   都道府県コード（沖縄県）
        ├─ 201:  市区町村コード（那覇市）
        └─ 6:    チェックデジット
        ```
        
        ### 使用手順
        1. **基本選択**: GitHub URLを入力してデータを読み込み
        2. **地域選択**: 都道府県・市区町村を選択
        3. **詳細選択**: GISファイルから大字・丁目を選択
        4. **結果取得**: 完全な住所情報と団体コードを取得
        
        ### 注意事項
        - インターネット接続が必要です
        - GIS機能にはGeoPandasが必要です
        - プライベートリポジトリの場合は適切なアクセス権限が必要です
        - 大きなGISファイルは読み込みに時間がかかる場合があります
        
        ### 更新履歴
        - **v33.0**: GIS対応、Shapefile・KML・ZIP読み込み機能追加
        - **v12.0**: 団体コード対応、沖縄県優先表示
        - **v4.0**: Streamlit対応、シンプル設計に特化
        - **v3.0**: GitHub対応、エラーハンドリング強化  
        - **v2.0**: GUI改善、保存機能追加  
        - **v1.0**: 初期バージョン
        
        ---
        
        **作成**: AI Assistant  
        **ライセンス**: MIT  
        **プラットフォーム**: Streamlit Cloud対応  
        **GIS対応**: GeoPandas + Fiona
        """)
        
        # システム情報
        st.header("🔧 システム情報")
        
        import sys
        import platform
        
        system_info = {
            "Python バージョン": sys.version,
            "プラットフォーム": platform.platform(),
            "Streamlit バージョン": st.__version__,
            "GeoPandas": "利用可能" if GEOPANDAS_AVAILABLE else "利用不可",
            "XML処理": "利用可能" if XML_AVAILABLE else "利用不可",
            "現在時刻": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        for key, value in system_info.items():
            st.write(f"**{key}**: {value}")
        
        # 必要なライブラリの状態
        st.header("📦 ライブラリ状態")
        
        libraries = [
            ("streamlit", True),
            ("pandas", True),
            ("requests", True),
            ("geopandas", GEOPANDAS_AVAILABLE),
            ("fiona", GEOPANDAS_AVAILABLE),
            ("lxml", XML_AVAILABLE)
        ]
        
        for lib_name, available in libraries:
            status = "✅ 利用可能" if available else "❌ 未インストール"
            st.write(f"**{lib_name}**: {status}")
    
    def run(self):
        """アプリケーションを実行"""
        # サイドバーでページ選択
        st.sidebar.title("🏛️ ナビゲーション")
        
        pages = {
            "🎯 メイン": self.render_main_page,
            "📊 データ管理": self.render_data_page,
            "ℹ️ 情報": self.render_about_page
        }
        
        selected_page = st.sidebar.selectbox("ページを選択", list(pages.keys()))
        
        # 選択されたページを表示
        pages[selected_page]()
        
        # サイドバーに基本情報のみ表示
        if st.session_state.data_loaded and st.session_state.prefecture_data:
            st.sidebar.markdown("---")
            st.sidebar.header("📊 現在のデータ")
            st.sidebar.write("✅ データ読み込み済み")
            
            if st.session_state.selected_prefecture:
                st.sidebar.write(f"選択中: {st.session_state.selected_prefecture}")
                if st.session_state.selected_city:
                    st.sidebar.write(f"市区町村: {st.session_state.selected_city}")
                    if st.session_state.selected_oaza:
                        st.sidebar.write(f"大字: {st.session_state.selected_oaza}")
                        if st.session_state.selected_chome:
                            st.sidebar.write(f"丁目: {st.session_state.selected_chome}")
        
        # GISファイル情報
        if st.session_state.selected_file_path:
            st.sidebar.markdown("---")
            st.sidebar.header("🗺️ GISデータ")
            st.sidebar.write(f"ファイル: {os.path.basename(st.session_state.selected_file_path)}")
            if st.session_state.area_data:
                st.sidebar.write(f"大字数: {len(st.session_state.area_data)}")
        
        # フッター
        st.sidebar.markdown("---")
        st.sidebar.markdown("**都道府県・市区町村選択ツール v33.0**")
        st.sidebar.markdown("Powered by Streamlit + GeoPandas")

def main():
    """メイン関数"""
    try:
        app = PrefectureCitySelectorGIS()
        app.run()
    except Exception as e:
        st.error(f"アプリケーションエラー: {str(e)}")
        st.info("ページを再読み込みしてください。")

if __name__ == "__main__":
    main()"選択オプションを作成"
                                    file_options = ["選択してください"]
                                    file_mapping = {}
                                    
                                    # 個別ファイル
                                    for f in files:
                                        base_name = os.path.basename(f)
                                        file_options.append(f"📄 {base_name}")
                                        file_mapping[f"📄 {base_name}"] = f
                                    
                                    # Shapefileセット
                                    for base_name, file_list in shapefile_sets.items():
                                        set_name = f"🗺️ {os.path.basename(base_name)}.shp (セット)"
                                        file_options.append(set_name)
                                        # Shapefileセットの場合は.shpファイルを代表として選択
                                        shp_file = next((f for f in file_list if f.endswith('.shp')), file_list[0])
                                        file_mapping[set_name] = shp_file
                                    
                                    # ファイル
