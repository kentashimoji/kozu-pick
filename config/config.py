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
}
