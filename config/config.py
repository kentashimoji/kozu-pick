# -*- coding: utf-8 -*-

import sys
from pathlib import Path

# プロジェクトルート追加
project_root = Path(__file__).resolve().parent.parent  # 2階層上
sys.path.insert(0, str(project_root))


APP_CONFIG = {
    "title": "都道府県・市区町村選択ツール v33.0",
    "icon": "🏛️",
    "layout": "wide",
    "sidebar_state": "expanded",
    "version": "33.0"
}

GITHUB_CONFIG = {
    "user_agent": "PrefectureCitySelector/33.0",
    "timeout": 30,
    "default_url": "https://raw.githubusercontent.com/USERNAME/REPOSITORY/main/000925835.xlsx"
}

GIS_CONFIG = {
    "supported_extensions": ['.zip', '.shp', '.shx', '.prj', '.dbf', '.cpg', '.kml'],
    "shapefile_required": ['.shp', '.shx', '.dbf']
    "default_search_range": 100,  # デフォルト検索範囲（メートル）
    "max_search_range": 1000,     # 最大検索範囲（メートル）
    "min_search_range": 10        # 最小検索範囲（メートル）
}

# 小字抽出用設定
KOZU_CONFIG = {
    "required_columns": ['大字名', '地番'],
    "optional_columns": ['丁目名', '小字名'],
    "geometry_column": 'geometry',
    "cache_enabled": True,
    "max_cache_size": 100  # キャッシュする最大ファイル数
}
