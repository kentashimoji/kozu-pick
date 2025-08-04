# -*- coding: utf-8 -*-

"""
GitHub API処理
"""

import requests
import streamlit as st
from config.settings import GITHUB_CONFIG
import sys
from pathlib import Path


# プロジェクトルート
project_root = Path(__file__).resolve().parent.parent  # 2階層上
sys.path.insert(0, str(project_root))


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

    def _convert_to_api_url(self, folder_url):
        """GitHub URLをAPI URLに変換"""
        if "raw.githubusercontent.com" in folder_url:
            parts = folder_url.replace('https://raw.githubusercontent.com/', '').split('/')
            username = parts[0]
            repo = parts[1]
            branch = parts[2]
            folder_path = '/'.join(parts[3:])

            return f"https://api.github.com/repos/{username}/{repo}/contents/{folder_path}"

        raise ValueError("無効なGitHub URLです")
