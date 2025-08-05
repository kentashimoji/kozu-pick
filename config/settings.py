"""
config/settings.py - 4段階構成対応の設定ファイル
"""

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
    # 実際のExcelファイルのURLに変更してください
    "default_url": "https://raw.githubusercontent.com/kentashimoji/kozu-pick/main/000925835.xlsx"
}

GIS_CONFIG = {
    "supported_extensions": ['.zip', '.shp', '.shx', '.prj', '.dbf', '.cpg', '.kml', '.csv', '.xlsx', '.xls'],
    "shapefile_required": ['.shp', '.shx', '.dbf','.prj','cpg'],
    # GISファイル検索用のデフォルトフォルダ（実際のフォルダURLに変更してください）
    "default_gis_folder": "https://api.github.com/repos/kentashimoji/kozu-pick/contents/47okinawa",
    # shpファイル特定用の設定
    "shp_search_patterns": [
        "{search_code}_{oaza}_{chome}_{chiban}.shp",  # 詳細パターン
        "{search_code}_{oaza}_{chome}.shp",           # 大字・丁目パターン
        "{search_code}_{oaza}.shp",                   # 大字パターン
        "{search_code}_地籍.shp",                     # 市区町村パターン
        "{search_code}.shp"                           # 基本パターン
    ]
}

# 4段階プロセス設定
PROCESS_CONFIG = {
    "step1": {
        "title": "都道府県・市区町村選択",
        "description": "指定されたExcelファイルからプルダウンを構成",
        "data_source": "excel_file",
        "required_fields": ["prefecture", "city"]
    },
    "step2": {
        "title": "大字・丁目選択", 
        "description": "5桁コードで特定されたファイルから大字・丁目を表示",
        "data_source": "gis_folder",
        "required_fields": ["oaza"],
        "optional_fields": ["chome"]
    },
    "step3": {
        "title": "地番入力",
        "description": "地番を入力する窓",
        "data_source": "user_input",
        "required_fields": ["chiban"],
        "validation_patterns": [
            r'^\d+(-\d+)*$',     # 123-4-5形式
            r'^\d+番地\d*',      # 123番地4形式  
            r'^\d+',            # 123形式
            r'^\d+番地'         # 123番地形式
        ]
    },
    "step4": {
        "title": "shpファイル特定",
        "description": "特定された住所情報から対象shpを特定",
        "data_source": "file_system",
        "required_fields": ["target_shp_file"]
    }
}

# 自動読み込み設定
AUTO_LOAD_CONFIG = {
    "enabled": True,
    "show_progress": True,
    "retry_count": 3,
    "retry_delay": 1.0,
    "step2_auto_trigger": True,  # Step1完了時にStep2データを自動読み込み
    "step4_auto_trigger": True   # Step3完了時にStep4処理を自動実行
}

# UI設定
UI_CONFIG = {
    "show_data_source_section": False,
    "show_debug_info": False,
    "show_progress_indicator": True,
    "prefecture_priority": "沖縄県",
    "default_help_messages": True,
    "step_navigation": {
        "show_step_numbers": True,
        "show_completion_status": True,
        "allow_step_skip": False,
        "show_reset_buttons": True
    }
}

# メッセージ設定
MESSAGES = {
    "loading": "📡 データを読み込んでいます...",
    "loading_complete": "✅ データの読み込みが完了しました",
    "loading_failed": "❌ データの読み込みに失敗しました",
    "no_data": "データが読み込まれていません",
    "select_prefecture": "都道府県を選択してください",
    "select_city": "市区町村を選択してください",
    "select_oaza": "大字を選択してください",
    "select_chome": "丁目を選択してください",
    "input_chiban": "地番を入力してください",
    "no_prefecture_selected": "まず都道府県を選択してください",
    "no_city_selected": "まず市区町村を選択してください",
    "no_oaza_selected": "まず大字を選択してください",
    "step_completed": "✅ ステップ完了",
    "step_pending": "⏳ 前のステップを完了してください",
    "validation_error": "❌ 入力内容を確認してください",
    "shp_identification_success": "🎯 shpファイルを特定しました",
    "shp_identification_failed": "⚠️ 条件に一致するshpファイルが特定できませんでした"
}

# ファイル命名規則
FILE_NAMING_CONFIG = {
    "shp_patterns": {
        "detailed": "{search_code}_{oaza}_{chome}_{chiban}",
        "area_specific": "{search_code}_{oaza}_{chome}",
        "oaza_only": "{search_code}_{oaza}",
        "city_general": "{search_code}_地籍",
        "basic": "{search_code}"
    },
    "extensions": {
        "shapefile": ".shp",
        "shapefile_index": ".shx", 
        "database": ".dbf",
        "projection": ".prj",
        "codepage": ".cpg"
    },
    "folder_structure": {
        "root": "{prefecture_code}{city_code}",
        "oaza_subfolder": "{oaza}",
        "chome_subfolder": "{chome}"
    }
}

# バリデーション設定
VALIDATION_CONFIG = {
    "prefecture_code": {
        "min_length": 2,
        "max_length": 2,
        "pattern": r'^[0-4][0-9]',
        "range": (1, 47)
    },
    "city_code": {
        "min_length": 3,
        "max_length": 3,
        "pattern": r'^[0-9]{3}'
    },
    "chiban": {
        "max_length": 50,
        "allowed_chars": r'[0-9\-番地]',
        "required": True
    },
    "oaza": {
        "max_length": 100,
        "required": True
    },
    "chome": {
        "max_length": 20,
        "required": False
    }
}

# エラーハンドリング設定
ERROR_CONFIG = {
    "show_traceback": False,  # 本番環境ではFalse
    "log_errors": True,
    "retry_on_network_error": True,
    "fallback_behavior": {
        "step1_failure": "show_manual_input",
        "step2_failure": "show_retry_button", 
        "step3_failure": "highlight_validation_error",
        "step4_failure": "show_manual_shp_selection"
    }
}

# パフォーマンス設定
PERFORMANCE_CONFIG = {
    "cache_enabled": True,
    "cache_ttl": 3600,  # 1時間
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "timeout_seconds": 30,
    "batch_processing": False,
    "lazy_loading": True
}