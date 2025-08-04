# -*- coding: utf-8 -*-

"""
小字データ抽出機能
元のKojiWebExtractorの機能を統合
"""
import sys
from pathlib import Path

# プロジェクトルート設定
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import streamlit as st
import geopandas as gpd
import pandas as pd
import requests
import json
import os
from shapely.geometry import Point
from pathlib import Path

class KozuWebExtractor:
    def __init__(self):
        """コンストラクタ - セッション状態を初期化"""
        if 'gdf' not in st.session_state:
            st.session_state.gdf = None
        if 'web_files_cache' not in st.session_state:
            st.session_state.web_files_cache = {}

    def get_files_from_web_folder(self, folder_url, file_extensions=None):
        """Web上のフォルダからファイル一覧を取得"""
        if file_extensions is None:
            file_extensions = ['.zip', '.shp']

        try:
            # キャッシュをチェック
            cache_key = f"{folder_url}_{','.join(file_extensions)}"
            if cache_key in st.session_state.web_files_cache:
                return st.session_state.web_files_cache[cache_key]

            # GitHubのフォルダの場合
            if 'github.com' in folder_url:
                return self._get_github_folder_files(folder_url, file_extensions)

            # 通常のWebフォルダの場合
            return self._get_generic_web_folder_files(folder_url, file_extensions)

        except Exception as e:
            st.error(f"フォルダからのファイル取得に失敗しました: {str(e)}")
            return []

    def _get_github_folder_files(self, folder_url, file_extensions):
        """GitHubフォルダからファイル一覧を取得（GitHub API使用 + レート制限対策）"""
        try:
            # GitHub URLを解析
            parts = folder_url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                raise Exception("無効なGitHub URLです")

            user = parts[0]
            repo = parts[1]

            # ブランチとパスを特定
            if len(parts) > 3 and parts[2] == 'tree':
                branch = parts[3]
                path = '/'.join(parts[4:]) if len(parts) > 4 else ''
            else:
                branch = 'main'
                path = '/'.join(parts[2:]) if len(parts) > 2 else ''

            # まずAPIを試行し、失敗した場合はraw.githubusercontent.comを使用
            try:
                # GitHub API URL構築
                api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{path}"
                if branch != 'main':
                    api_url += f"?ref={branch}"

                # GitHub APIトークンがある場合は使用（環境変数から取得）
                headers = {}
                github_token = os.environ.get('GITHUB_TOKEN')
                if github_token:
                    headers['Authorization'] = f'token {github_token}'

                response = requests.get(api_url, headers=headers, timeout=30)

                if response.status_code == 403:
                    # レート制限の場合、代替方法を使用
                    st.warning("⚠️ GitHub APIのレート制限に達しました。代替方法でファイルを取得します...")
                    return self._get_github_files_alternative(user, repo, branch, path, file_extensions)

                response.raise_for_status()
                files_data = response.json()
                files = []

                for item in files_data:
                    if item['type'] == 'file':
                        file_name = item['name']
                        if any(file_name.lower().endswith(ext.lower()) for ext in file_extensions):
                            # rawファイルURLを生成
                            raw_url = item['download_url']
                            files.append({
                                'name': file_name,
                                'url': raw_url,
                                'size': item.get('size', 0),
                                'description': f"GitHubファイル ({item.get('size', 0)} bytes)"
                            })

                # キャッシュに保存
                cache_key = f"{folder_url}_{','.join(file_extensions)}"
                st.session_state.web_files_cache[cache_key] = files

                return files

            except requests.exceptions.RequestException as e:
                if "403" in str(e) or "rate limit" in str(e).lower():
                    # APIレート制限の場合、代替方法を使用
                    st.warning("⚠️ GitHub APIのレート制限に達しました。代替方法でファイルを取得します...")
                    return self._get_github_files_alternative(user, repo, branch, path, file_extensions)
                else:
                    raise e

        except requests.exceptions.RequestException as e:
            raise Exception(f"GitHub APIアクセスエラー: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("GitHub APIレスポンスの解析に失敗しました")
        except Exception as e:
            raise Exception(f"GitHubフォルダ処理エラー: {str(e)}")

    def _get_github_files_alternative(self, user, repo, branch, path, file_extensions):
        """GitHub APIが使えない場合の代替方法"""
        try:
            # Web scraping method (simplified)
            web_url = f"https://github.com/{user}/{repo}/tree/{branch}/{path}"
            # ここでは簡易的な実装のみ
            st.info("代替方法でファイル取得を試行中...")
            return []
        except Exception as e:
            raise Exception(f"GitHub代替取得エラー: {str(e)}")

    def _get_generic_web_folder_files(self, folder_url, file_extensions):
        """通常のWebフォルダからファイル一覧を取得"""
        # 通常のWebディレクトリリスティングからファイルを取得
        # 実装は省略（プロジェクトに応じて実装）
        return []

    def extract_data(self, gdf, oaza, chome, koaza, chiban, range_m):
        """データ抽出処理（丁目・小字対応）"""
        try:
            # 必要な列の存在確認
            required_columns = ['大字名', '地番']
            missing_columns = [col for col in required_columns if col not in gdf.columns]

            if missing_columns:
                return None, None, f"必要な列が見つかりません: {missing_columns}"

            # NULL値をチェック
            null_check = {}
            for col in required_columns:
                null_count = gdf[col].isnull().sum()
                if null_count > 0:
                    null_check[col] = null_count

            if null_check:
                warning_msg = "警告: NULL値が含まれています - " + ", ".join([f"{k}: {v}件" for k, v in null_check.items()])
                st.warning(warning_msg)

            # 検索条件を構築（丁目・小字の有無に応じて）
            search_condition = (
                (gdf['大字名'] == oaza) &
                (gdf['地番'] == chiban) &
                (gdf['大字名'].notna()) &
                (gdf['地番'].notna())
            )

            # 丁目が指定されている場合は条件に追加
            if chome is not None and chome != "選択なし" and '丁目名' in gdf.columns:
                search_condition = search_condition & (gdf['丁目名'] == chome) & (gdf['丁目名'].notna())

            # 小字が指定されている場合は条件に追加
            if koaza is not None and koaza != "選択なし" and '小字名' in gdf.columns:
                search_condition = search_condition & (gdf['小字名'] == koaza) & (gdf['小字名'].notna())

            df = gdf[search_condition]

            if df.empty:
                # デバッグ情報を提供
                debug_info = []
                oaza_matches = gdf[gdf['大字名'] == oaza]['大字名'].count()
                chiban_matches = gdf[gdf['地番'] == chiban]['地番'].count()

                debug_info.append(f"大字名'{oaza}'の該当件数: {oaza_matches}")
                debug_info.append(f"地番'{chiban}'の該当件数: {chiban_matches}")

                if chome and chome != "選択なし" and '丁目名' in gdf.columns:
                    chome_matches = gdf[gdf['丁目名'] == chome]['丁目名'].count()
                    debug_info.append(f"丁目名'{chome}'の該当件数: {chome_matches}")

                if koaza and koaza != "選択なし" and '小字名' in gdf.columns:
                    koaza_matches = gdf[gdf['小字名'] == koaza]['小字名'].count()
                    debug_info.append(f"小字名'{koaza}'の該当件数: {koaza_matches}")

                return None, None, f"該当する筆が見つかりませんでした。{' / '.join(debug_info)}"

            # 利用可能な列のみを選択
            available_columns = ["大字名", "地番", "geometry"]
            if "丁目名" in gdf.columns:
                available_columns.insert(1, "丁目名")
            if "小字名" in gdf.columns:
                insert_position = 2 if "丁目名" in available_columns else 1
                available_columns.insert(insert_position, "小字名")

            # 存在する列のみでデータフレームを作成
            existing_columns = [col for col in available_columns if col in df.columns]
            df_summary = df.reindex(columns=existing_columns)

            # geometryカラムが存在し、有効かチェック
            if 'geometry' not in df_summary.columns:
                return None, None, "geometry列が見つかりません"

            if df_summary['geometry'].isnull().any():
                return None, None, "geometry列にNULL値が含まれています"

            # 中心点計算と周辺筆抽出
            cen = df_summary.geometry.centroid
            cen_gdf = gpd.GeoDataFrame(geometry=cen)
            cen_gdf['x'] = cen_gdf.geometry.x
            cen_gdf['y'] = cen_gdf.geometry.y

            # 検索範囲の4角ポイント計算
            i1 = cen_gdf['x'] + range_m
            i2 = cen_gdf['x'] - range_m
            i3 = cen_gdf['y'] + range_m
            i4 = cen_gdf['y'] - range_m

            x1, y1 = i3.iloc[0], i1.iloc[0]
            x2, y2 = i4.iloc[0], i2.iloc[0]

            # 4つのポイントを定義
            top_right = [x1, y1]
            lower_left = [x2, y2]
            lower_right = [x1, y2]
            top_left = [x2, y1]

            points = pd.DataFrame([top_right, lower_left, lower_right, top_left],
                                index=["top_right", "lower_left", "lower_right", "top_left"],
                                columns=["lon", "lat"])

            # ジオメトリ作成
            geometry = [Point(xy) for xy in zip(points.lat, points.lon)]
            four_points_gdf = gpd.GeoDataFrame(points, geometry=geometry)

            # 検索範囲のポリゴン作成
            sq = four_points_gdf.dissolve().convex_hull

            # オーバーレイ処理（NULL値を除外したデータで）
            df1 = gpd.GeoDataFrame({'geometry': sq})
            df1 = df1.set_crs(gdf.crs)

            # 地番とgeometryが両方とも有効なデータのみを使用
            valid_data = gdf[(gdf['地番'].notna()) & (gdf['geometry'].notna())].copy()

            # 周辺筆抽出用のデータフレーム作成（利用可能な列のみ使用）
            overlay_columns = ['地番', 'geometry']
            if '大字名' in valid_data.columns:
                overlay_columns.insert(0, '大字名')
            if '丁目名' in valid_data.columns:
                overlay_columns.insert(-1, '丁目名')
            if '小字名' in valid_data.columns:
                overlay_columns.insert(-1, '小字名')

            existing_overlay_columns = [col for col in overlay_columns if col in valid_data.columns]
            df2 = gpd.GeoDataFrame(valid_data[existing_overlay_columns])

            overlay_gdf = df1.overlay(df2, how='intersection')

            return df_summary, overlay_gdf, f"対象筆: {len(df_summary)}件, 周辺筆: {len(overlay_gdf)}件"

        except Exception as e:
            return None, None, f"エラー: {str(e)}"

    def get_chome_options(self, gdf, selected_oaza):
        """指定された大字名に対応する丁目の選択肢を取得"""
        try:
            if '丁目名' not in gdf.columns:
                return None

            # 指定された大字名でフィルタリング
            filtered_gdf = gdf[
                (gdf['大字名'] == selected_oaza) &
                (gdf['大字名'].notna()) &
                (gdf['丁目名'].notna())
            ]

            if len(filtered_gdf) == 0:
                return None

            # 丁目名のユニークな値を取得してソート
            chome_list = sorted(filtered_gdf['丁目名'].unique())
            return chome_list

        except Exception as e:
            st.error(f"丁目名取得エラー: {str(e)}")
            return None

    def get_koaza_options(self, gdf, selected_oaza, selected_chome=None):
        """指定された大字名（及び丁目名）に対応する小字の選択肢を取得"""
        try:
            if '小字名' not in gdf.columns:
                return None

            # フィルタ条件を構築
            filter_condition = (
                (gdf['大字名'] == selected_oaza) &
                (gdf['大字名'].notna()) &
                (gdf['小字名'].notna())
            )

            # 丁目が指定されている場合は条件に追加
            if selected_chome and selected_chome != "選択なし" and '丁目名' in gdf.columns:
                filter_condition = filter_condition & (gdf['丁目名'] == selected_chome) & (gdf['丁目名'].notna())

            # 指定された条件でフィルタリング
            filtered_gdf = gdf[filter_condition]

            if len(filtered_gdf) == 0:
                return None

            # 小字名のユニークな値を取得してソート
            koaza_list = sorted(filtered_gdf['小字名'].unique())
            return koaza_list

        except Exception as e:
            st.error(f"小字名取得エラー: {str(e)}")
            return None
