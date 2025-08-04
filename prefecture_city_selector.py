#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
都道府県・市区町村選択ツール v4.0 (Streamlit版)
GitHub ExcelファイルからデータをダウンロードしてWebアプリケーションを作成

必要なライブラリ:
pip install streamlit pandas openpyxl requests

実行方法:
streamlit run prefecture_city_selector_streamlit.py
"""

import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="都道府県・市区町村選択ツール v4.0",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class PrefectureCitySelectorWeb:
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """セッション状態を初期化"""
        if 'prefecture_data' not in st.session_state:
            st.session_state.prefecture_data = {}
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'current_url' not in st.session_state:
            st.session_state.current_url = ""
        if 'selected_prefecture' not in st.session_state:
            st.session_state.selected_prefecture = ""
        if 'selected_city' not in st.session_state:
            st.session_state.selected_city = ""
    
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
            
            headers = {'User-Agent': 'PrefectureCitySelector/4.0'}
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
            
            # データを整理
            prefecture_data = {}
            prefecture_cols = [col for col in df.columns if '都道府県' in col and '漢字' in col]
            city_cols = [col for col in df.columns if '市区町村' in col and '漢字' in col]
            
            if not prefecture_cols or not city_cols:
                st.error(f"適切な列が見つかりません。利用可能な列: {list(df.columns)}")
                return False
            
            prefecture_col = prefecture_cols[0]
            city_col = city_cols[0]
            
            for _, row in df.iterrows():
                prefecture = row.get(prefecture_col)
                city = row.get(city_col)
                
                if pd.notna(prefecture):
                    if prefecture not in prefecture_data:
                        prefecture_data[prefecture] = set()
                    
                    if pd.notna(city):
                        prefecture_data[prefecture].add(city)
            
            # SetをListに変換してソート
            for prefecture in prefecture_data:
                prefecture_data[prefecture] = sorted(list(prefecture_data[prefecture]))
            
            # セッション状態を更新
            st.session_state.prefecture_data = prefecture_data
            st.session_state.data_loaded = True
            st.session_state.current_url = url
            
            progress_bar.progress(100)
            status_text.text("✅ データの読み込みが完了しました！")
            
            # 統計情報を表示
            total_prefectures = len(prefecture_data)
            total_cities = sum(len(cities) for cities in prefecture_data.values())
            
            st.success(f"📊 読み込み完了: {total_prefectures}都道府県, {total_cities}市区町村")
            
            return True
            
        except requests.RequestException as e:
            st.error(f"ネットワークエラー: {str(e)}")
            return False
        except Exception as e:
            st.error(f"データの読み込みに失敗しました: {str(e)}")
            return False
    
    def create_download_link(self, data, filename, file_type="json"):
        """ダウンロードリンクを作成（現在は使用しない）"""
        # この機能は削除されました
        pass
    
    def render_main_page(self):
        """メインページを描画"""
        st.title("🏛️ 都道府県・市区町村選択ツール v4.0")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("**GitHub ExcelファイルからデータをダウンロードしてWebアプリケーションを作成**")
        with col2:
            st.metric("バージョン", "4.0")
        with col3:
            st.metric("プラットフォーム", "Streamlit")
        
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
                st.session_state.data_loaded = False
                st.session_state.selected_prefecture = ""
                st.session_state.selected_city = ""
                st.success("データをクリアしました")
                st.experimental_rerun()
        
        # データが読み込まれている場合の選択UI
        if st.session_state.data_loaded and st.session_state.prefecture_data:
            st.markdown("---")
            st.header("🎯 地域選択")
            
            col1, col2 = st.columns(2)
            
            with col1:
                prefectures = sorted(st.session_state.prefecture_data.keys())
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
                    cities = st.session_state.prefecture_data[st.session_state.selected_prefecture]
                    
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
                
                result_data = {
                    "都道府県": st.session_state.selected_prefecture,
                    "市区町村": st.session_state.selected_city,
                    "完全な住所": f"{st.session_state.selected_prefecture}{st.session_state.selected_city}",
                    "選択日時": datetime.now().strftime('%Y年%m月%d日 %H:%M:%S'),
                    "データソース": st.session_state.current_url[:60] + "..." if len(st.session_state.current_url) > 60 else st.session_state.current_url
                }
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    for key, value in result_data.items():
                        st.write(f"**{key}:** {value}")
                
                with col2:
                    if st.button("📋 結果をコピー"):
                        result_text = "\n".join([f"{k}: {v}" for k, v in result_data.items()])
                        st.code(result_text)
                        st.success("結果を表示しました。上記のテキストをコピーしてください。")
    
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
        
        # データクリア機能のみ
        st.header("🗑️ データ管理")
        
        if st.button("🗑️ 読み込まれたデータをクリア", type="secondary"):
            if st.session_state.data_loaded:
                st.session_state.prefecture_data = {}
                st.session_state.data_loaded = False
                st.session_state.current_url = ""
                st.session_state.selected_prefecture = ""
                st.session_state.selected_city = ""
                st.success("データをクリアしました")
                st.experimental_rerun()
            else:
                st.warning("クリアするデータがありません")
    
    def render_about_page(self):
        """情報ページを描画"""
        st.title("ℹ️ アプリケーション情報")
        
        st.markdown("""
        ## 🏛️ 都道府県・市区町村選択ツール v4.0
        
        ### 概要
        GitHubにアップロードされたExcelファイルから日本の都道府県・市区町村データを
        読み込み、階層的な選択を可能にするWebアプリケーションです。
        
        ### 主な機能
        ✅ **GitHub対応**: GitHub上のExcelファイルの直接読み込み  
        ✅ **階層選択**: 都道府県選択による市区町村の絞り込み  
        ✅ **リアルタイム**: 選択結果の即時表示  
        ✅ **レスポンシブ**: モバイル・デスクトップ対応  
        ✅ **シンプル**: 必要最小限の機能に特化  
        
        ### 必要なライブラリ
        ```bash
        pip install streamlit pandas openpyxl requests
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
        - Excel (.xlsx, .xls)
        - CSV (.csv)
        
        ### 注意事項
        - インターネット接続が必要です
        - プライベートリポジトリの場合は適切なアクセス権限が必要です
        - ファイルサイズが大きい場合は読み込みに時間がかかります
        
        ### 更新履歴
        - **v4.0**: Streamlit対応、シンプル設計に特化
        - **v3.0**: GitHub対応、エラーハンドリング強化  
        - **v2.0**: GUI改善、保存機能追加  
        - **v1.0**: 初期バージョン  
        
        ---
        
        **作成**: AI Assistant  
        **ライセンス**: MIT  
        **プラットフォーム**: Streamlit Cloud対応
        """)
        
        # システム情報
        st.header("🔧 システム情報")
        
        import sys
        import platform
        
        system_info = {
            "Python バージョン": sys.version,
            "プラットフォーム": platform.platform(),
            "Streamlit バージョン": st.__version__,
            "現在時刻": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        for key, value in system_info.items():
            st.write(f"**{key}**: {value}")
    
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
        
        # フッター
        st.sidebar.markdown("---")
        st.sidebar.markdown("**都道府県・市区町村選択ツール v4.0**")
        st.sidebar.markdown("Powered by Streamlit")

def main():
    """メイン関数"""
    try:
        app = PrefectureCitySelectorWeb()
        app.run()
    except Exception as e:
        st.error(f"アプリケーションエラー: {str(e)}")
        st.info("ページを再読み込みしてください。")

if __name__ == "__main__":
    main()