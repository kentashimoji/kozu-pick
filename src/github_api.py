# -*- coding: utf-8 -*-

"""
GitHub API処理
"""
import sys
from pathlib import Path


# プロジェクトルート
project_root = Path(__file__).resolve().parent.parent  # 2階層上
sys.path.insert(0, str(project_root))


import requests
import streamlit as st
from config.settings import GITHUB_CONFIG


class GitHubAPI:
    def __init__(self):
        self.headers = {'User-Agent': GITHUB_CONFIG["user_agent"]}
        self.timeout = GITHUB_CONFIG["timeout"]

    def download_file(self, url):
        """ファイルをダウンロード"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            st.error(f"ネットワークエラー: {str(e)}")
            return None

    def get_folder_contents(self, folder_url):
        """フォルダの内容を取得"""
        try:
            # GitHub URLをAPI URLに変換
            api_url = self._convert_to_api_url(folder_url)

            response = requests.get(api_url, headers=self.headers, timeout=self.timeout)

            if response.status_code == 403:
                st.warning("⚠️ GitHub APIのレート制限に達しました。")
                return []

            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"GitHub APIアクセスエラー: {str(e)}")
            return []

    def _convert_folder_url_to_api(self, folder_url):
        """GitHub URLをAPI URLに変換"""
        try:
            if "raw.githubusercontent.com" in folder_url:
                # raw.githubusercontent.com URLをAPI URLに変換
                # https://raw.githubusercontent.com/user/repo/branch/path
                # -> https://api.github.com/repos/user/repo/contents/path?ref=branch
                
                parts = folder_url.replace('https://raw.githubusercontent.com/', '').split('/')
                username = parts[0]
                repo = parts[1]
                branch = parts[2]
                folder_path = '/'.join(parts[3:]) if len(parts) > 3 else ''
                
                api_url = f"https://api.github.com/repos/{username}/{repo}/contents/{folder_path}"
                if branch != 'main':
                    api_url += f"?ref={branch}"
                
                return api_url
                
            elif "github.com" in folder_url:
                # github.com URLをAPI URLに変換
                # https://github.com/user/repo/tree/branch/path
                # -> https://api.github.com/repos/user/repo/contents/path?ref=branch
                
                parts = folder_url.replace('https://github.com/', '').split('/')
                if len(parts) < 2:
                    raise ValueError("無効なGitHub URLです")
                
                username = parts[0]
                repo = parts[1]
                
                if len(parts) > 3 and parts[2] == 'tree':
                    branch = parts[3]
                    folder_path = '/'.join(parts[4:]) if len(parts) > 4 else ''
                else:
                    branch = 'main'
                    folder_path = '/'.join(parts[2:]) if len(parts) > 2 else ''
                
                api_url = f"https://api.github.com/repos/{username}/{repo}/contents/{folder_path}"
                if branch != 'main':
                    api_url += f"?ref={branch}"
                
                return api_url
            else:
                raise ValueError("GitHubのURLではありません")
                
        except Exception as e:
            raise ValueError(f"URL変換エラー: {str(e)}")
    
    def search_files_by_code(self, folder_url, search_code, file_extensions=None):
        """フォルダ内から指定コードを含むファイルを検索"""
        if file_extensions is None:
            file_extensions = ['.zip', '.shp', '.csv', '.xlsx', '.xls', '.kml']
        
        try:
            # フォルダ内容を取得
            files_data = self.get_folder_contents(folder_url)
            
            if not files_data:
                return []
            
            found_files = []
            
            for item in files_data:
                if item['type'] == 'file':
                    file_name = item['name']
                    file_ext = '.' + file_name.lower().split('.')[-1] if '.' in file_name else ''
                    
                    # ファイル名に検索コードが含まれ、対応する拡張子かチェック
                    if search_code in file_name and file_ext in file_extensions:
                        found_files.append({
                            'name': file_name,
                            'download_url': item['download_url'],
                            'size': item.get('size', 0),
                            'extension': file_ext,
                            'description': f"GISファイル ({item.get('size', 0)} bytes)"
                        })
            
            # ファイルを優先度順にソート（ZIP > CSV/Excel > SHP > KML）
            priority_order = {'.zip': 1, '.csv': 2, '.xlsx': 2, '.xls': 2, '.shp': 3, '.kml': 4}
            found_files.sort(key=lambda x: priority_order.get(x['extension'], 99))
            
            return found_files
            
        except Exception as e:
            st.error(f"ファイル検索エラー: {str(e)}")
            return []
    
    def get_file_info(self, file_url):
        """ファイル情報を取得"""
        try:
            # HEADリクエストでファイル情報のみ取得
            response = requests.head(file_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            return {
                'size': int(response.headers.get('content-length', 0)),
                'content_type': response.headers.get('content-type', ''),
                'last_modified': response.headers.get('last-modified', '')
            }
        except Exception as e:
            return None
    
    def validate_github_url(self, url):
        """GitHub URLの妥当性をチェック"""
        if not url:
            return False, "URLが入力されていません"
        
        if "github.com" not in url and "raw.githubusercontent.com" not in url:
            return False, "GitHubのURLではありません"
        
        try:
            response = requests.head(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return True, "有効なURLです"
            elif response.status_code == 404:
                return False, "ファイルまたはフォルダが見つかりません"
            elif response.status_code == 403:
                return False, "アクセス権限がありません"
            else:
                return False, f"アクセスエラー (HTTP {response.status_code})"
        except requests.RequestException as e:
            return False, f"接続エラー: {str(e)}"
    
    def get_repository_info(self, repo_url):
        """リポジトリ情報を取得"""
        try:
            # リポジトリURLからAPI URLを生成
            if "github.com" in repo_url:
                parts = repo_url.replace('https://github.com/', '').split('/')
                if len(parts) >= 2:
                    username = parts[0]
                    repo = parts[1]
                    
                    api_url = f"https://api.github.com/repos/{username}/{repo}"
                    
                    response = requests.get(api_url, headers=self.headers, timeout=self.timeout)
                    response.raise_for_status()
                    
                    repo_data = response.json()
                    return {
                        'name': repo_data.get('name'),
                        'full_name': repo_data.get('full_name'),
                        'description': repo_data.get('description'),
                        'default_branch': repo_data.get('default_branch'),
                        'size': repo_data.get('size'),
                        'language': repo_data.get('language'),
                        'updated_at': repo_data.get('updated_at')
                    }
            
            return None
        except Exception as e:
            return None