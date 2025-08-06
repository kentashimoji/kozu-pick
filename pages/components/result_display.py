#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pages/components/result_display.py - 最終結果表示コンポーネント
4段階完了後の包括的な結果表示と出力機能
"""

import streamlit as st
import json
from datetime import datetime

try:
    from config.settings import APP_CONFIG, GIS_CONFIG
except ImportError:
    APP_CONFIG = {"version": "33.0"}
    GIS_CONFIG = {"default_gis_folder": ""}

class ResultDisplay:
    """最終結果表示コンポーネント"""
    
    def __init__(self):
        pass
    
    def render(self, address_info, target_shp_file):
        """最終結果を包括的に表示"""
        st.markdown("**4段階の住所特定が完了しました**")
        
        # メインの結果表示
        self._render_main_result(address_info, target_shp_file)
        
        # 操作パネル
        self._render_action_panel(address_info, target_shp_file)
        
        # 詳細情報タブ
        self._render_detail_tabs(address_info, target_shp_file)
    
    def _render_main_result(self, address_info, target_shp_file):
        """メインの結果表示"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._render_address_summary(address_info)
        
        with col2:
            self._render_file_summary(target_shp_file, address_info)
    
    def _render_address_summary(self, address_info):
        """住所サマリーを表示"""
        st.subheader("📍 完全な住所情報")
        
        # 完全住所の構築と表示
        complete_address = self._build_complete_address_string(address_info)
        st.success(f"**完全住所**: {complete_address}")
        
        # 階層構造での表示
        st.markdown("**住所構成:**")
        hierarchy_levels = [
            ("都道府県", "🏛️"),
            ("市区町村", "🏘️"), 
            ("大字", "🌄"),
            ("丁目", "🛣️"),
            ("地番", "🏠")
        ]
        
        for level, icon in hierarchy_levels:
            value = address_info.get(level, '')
            if value and value != "なし":
                st.write(f"{icon} **{level}**: {value}")
            elif level in ["都道府県", "市区町村", "大字", "地番"]:  # 必須項目
                st.write(f"{icon} **{level}**: *未設定*")
    
    def _render_file_summary(self, target_shp_file, address_info):
        """ファイルサマリーを表示"""
        st.subheader("📄 特定ファイル")
        
        if target_shp_file:
            st.success(f"**ファイル名**: `{target_shp_file}`")
            
            # ファイルパス推定
            estimated_path = self._estimate_file_path(target_shp_file)
            if estimated_path != "パス推定不可":
                st.write(f"**推定パス**: `{estimated_path}`")
            
            # ファイル分析
            file_analysis = self._analyze_filename(target_shp_file, address_info)
            if file_analysis:
                with st.expander("🔍 ファイル名分析"):
                    for key, value in file_analysis.items():
                        st.write(f"- **{key}**: {value}")
        else:
            st.warning("shpファイルが特定されていません")
        
        # 識別コード
        st.markdown("**識別コード:**")
        search_code = address_info.get('検索コード', '')
        team_code = address_info.get('団体コード', '')
        
        if search_code:
            st.write(f"🔍 **検索コード**: `{search_code}`")
        if team_code:
            st.write(f"🏛️ **団体コード**: `{team_code}`")
    
    def _render_action_panel(self, address_info, target_shp_file):
        """操作パネルを表示"""
        st.markdown("---")
        st.subheader("📋 結果の活用")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 テキスト表示", use_container_width=True):
                self._show_text_result(address_info, target_shp_file)
        
        with col2:
            if st.button("💾 JSON出力", use_container_width=True):
                self._download_json_result(address_info, target_shp_file)
        
        with col3:
            if st.button("📊 統計表示", use_container_width=True):
                self._show_processing_stats()
        
        with col4:
            if st.button("🔄 全リセット", use_container_width=True):
                self._reset_all_data()
    
    def _render_detail_tabs(self, address_info, target_shp_file):
        """詳細情報をタブで表示"""
        st.markdown("---")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 住所詳細", "📄 ファイル詳細", "📊 処理統計", "🔧 技術情報"])
        
        with tab1:
            self._render_address_details(address_info)
        
        with tab2:
            self._render_file_details(target_shp_file, address_info)
        
        with tab3:
            self._render_processing_statistics()
        
        with tab4:
            self._render_technical_info(address_info, target_shp_file)
    
    def _render_address_details(self, address_info):
        """住所詳細情報"""
        st.markdown("### 📍 住所構成詳細")
        
        # 住所検証
        validation_result = self._validate_address_completeness(address_info)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**入力情報:**")
            for key, value in address_info.items():
                if key not in ['団体コード', '検索コード']:
                    status = "✅" if value and value != "なし" else "❌"
                    display_value = value if value and value != "なし" else "*未入力*"
                    st.write(f"{status} **{key}**: {display_value}")
        
        with col2:
            st.markdown("**検証結果:**")
            completion_rate = validation_result['completion_rate']
            
            if completion_rate == 100:
                st.success(f"完全性: {completion_rate:.1f}% (完璧)")
            elif completion_rate >= 80:
                st.warning(f"完全性: {completion_rate:.1f}% (ほぼ完全)")
            else:
                st.error(f"完全性: {completion_rate:.1f}% (要改善)")
            
            if validation_result['missing_fields']:
                st.write("**不足項目:**")
                for field in validation_result['missing_fields']:
                    st.write(f"- {field}")
        
        # 住所の階層分析
        st.markdown("**階層分析:**")
        hierarchy = self._get_address_hierarchy(address_info)
        
        for i, level_info in enumerate(hierarchy):
            indent = "　" * i
            st.write(f"{indent}📍 **{level_info['level']}**: {level_info['name']}")
            if level_info.get('code'):
                st.write(f"{indent}　 コード: `{level_info['code']}`")
    
    def _render_file_details(self, target_shp_file, address_info):
        """ファイル詳細情報"""
        st.markdown("### 📄 特定ファイル詳細")
        
        if not target_shp_file:
            st.warning("ファイルが特定されていません")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**基本情報:**")
            st.write(f"**ファイル名**: {target_shp_file}")
            st.write(f"**拡張子**: {target_shp_file.split('.')[-1] if '.' in target_shp_file else 'なし'}")
            st.write(f"**文字数**: {len(target_shp_file)}")
            
            # 推定パス
            estimated_path = self._estimate_file_path(target_shp_file)
            st.write(f"**推定パス**: {estimated_path}")
        
        with col2:
            st.markdown("**分析結果:**")
            analysis = self._analyze_filename(target_shp_file, address_info)
            
            if analysis:
                for key, value in analysis.items():
                    st.write(f"**{key}**: {value}")
        
        # 関連ファイル推定
        if target_shp_file.endswith('.shp'):
            st.markdown("**推定関連ファイル:**")
            base_name = target_shp_file[:-4]
            related_files = [
                f"{base_name}.dbf (属性データ)",
                f"{base_name}.shx (インデックス)",
                f"{base_name}.prj (座標系情報)",
                f"{base_name}.cpg (文字コード)"
            ]
            
            for related_file in related_files:
                st.write(f"- {related_file}")
    
    def _render_processing_statistics(self):
        """処理統計情報"""
        st.markdown("### 📊 処理統計")
        
        # ステップ別統計
        step_stats = {}
        for step_key, completed in st.session_state.step_completed.items():
            step_num = step_key[-1]
            step_stats[f"Step{step_num}"] = "完了" if completed else "未完了"
        
        # 基本統計
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**ステップ完了状況:**")
            for step, status in step_stats.items():
                status_icon = "✅" if status == "完了" else "❌"
                st.write(f"{status_icon} **{step}**: {status}")
            
            completed_count = sum(st.session_state.step_completed.values())
            total_count = len(st.session_state.step_completed)
            st.write(f"**完了率**: {completed_count}/{total_count} ({completed_count/total_count*100:.1f}%)")
        
        with col2:
            st.markdown("**データ統計:**")
            
            # セッションデータ統計
            prefecture_data = st.session_state.get('prefecture_data', {})
            area_data = st.session_state.get('area_data', {})
            
            st.write(f"**都道府県数**: {len(prefecture_data)}")
            
            if prefecture_data:
                total_cities = sum(len(cities) for cities in prefecture_data.values())
                st.write(f"**総市区町村数**: {total_cities}")
            
            st.write(f"**読み込み大字数**: {len(area_data)}")
            
            if area_data:
                total_chome = sum(len(chome_list) for chome_list in area_data.values() 
                               if isinstance(chome_list, list))
                st.write(f"**読み込み丁目数**: {total_chome}")
        
        # 処理時間推定
        st.markdown("**処理情報:**")
        st.write(f"**完了日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        st.write(f"**アプリバージョン**: {APP_CONFIG.get('version', '不明')}")
    
    def _render_technical_info(self, address_info, target_shp_file):
        """技術情報"""
        st.markdown("### 🔧 技術情報")
        
        # セッション状態の概要
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**セッション情報:**")
            
            # セッションキーの統計
            session_keys = list(st.session_state.keys())
            st.write(f"**セッションキー数**: {len(session_keys)}")
            
            # データサイズ推定
            important_keys = ['prefecture_data', 'city_codes', 'area_data', 'step_completed']
            data_sizes = {}
            
            for key in important_keys:
                if key in st.session_state:
                    data_str = str(st.session_state[key])
                    data_sizes[key] = len(data_str)
            
            st.write("**データサイズ (文字数):**")
            for key, size in data_sizes.items():
                st.write(f"- {key}: {size:,}")
        
        with col2:
            st.markdown("**設定情報:**")
            
            # GIS設定
            gis_folder = GIS_CONFIG.get('default_gis_folder', 'なし')
            if len(gis_folder) > 50:
                gis_folder = gis_folder[:47] + "..."
            st.write(f"**GISフォルダ**: {gis_folder}")
            
            # 対応拡張子
            supported_ext = GIS_CONFIG.get('supported_extensions', [])
            if supported_ext:
                st.write(f"**対応拡張子**: {', '.join(supported_ext[:5])}")
                if len(supported_ext) > 5:
                    st.write(f"他{len(supported_ext)-5}個")
        
        # デバッグ情報
        with st.expander("🐛 デバッグ情報 (開発者向け)"):
            st.markdown("**重要なセッションキー:**")
            debug_keys = [
                'selected_prefecture', 'selected_city', 'selected_oaza', 
                'selected_chome', 'input_chiban', 'target_shp_file',
                'current_gis_code', 'gis_load_attempted'
            ]
            
            for key in debug_keys:
                value = st.session_state.get(key, 'なし')
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                st.write(f"- **{key}**: {value}")
    
    def _build_complete_address_string(self, address_info):
        """完全住所文字列を構築"""
        address_parts = []
        
        for key in ["都道府県", "市区町村", "大字", "丁目", "地番"]:
            value = address_info.get(key, '')
            if value and value != "なし":
                address_parts.append(value)
        
        return "".join(address_parts)
    
    def _estimate_file_path(self, target_shp_file):
        """ファイルパスを推定"""
        gis_folder = GIS_CONFIG.get('default_gis_folder', '')
        
        if gis_folder and target_shp_file:
            if gis_folder.endswith('/'):
                return f"{gis_folder}{target_shp_file}"
            else:
                return f"{gis_folder}/{target_shp_file}"
        
        return "パス推定不可"
    
    def _analyze_filename(self, filename, address_info):
        """ファイル名を分析"""
        if not filename:
            return {}
        
        analysis = {}
        
        # 基本情報
        analysis['文字数'] = len(filename)
        analysis['拡張子'] = filename.split('.')[-1] if '.' in filename else 'なし'
        
        # 構成要素分析
        if '_' in filename:
            parts = filename.replace('.shp', '').split('_')
            analysis['構成要素数'] = len(parts)
            analysis['命名パターン'] = '_'.join(['X'] * len(parts))
            
            # 要素の分類
            element_types = []
            for part in parts:
                if part.isdigit():
                    if len(part) == 5:
                        element_types.append("5桁コード")
                    elif len(part) == 2:
                        element_types.append("都道府県コード")
                    elif len(part) == 3:
                        element_types.append("市区町村コード")
                    else:
                        element_types.append("数値")
                elif any(keyword in part for keyword in ['地籍', '筆', 'cadastral', 'parcel']):
                    element_types.append("地籍キーワード")
                elif '丁目' in part:
                    element_types.append("丁目情報")
                elif part in ['公共座標15系', '公共座標16系']:
                    element_types.append("座標系情報")
                else:
                    element_types.append("地名・その他")
            
            analysis['要素タイプ'] = ', '.join(element_types)
        
        # 住所情報との一致度
        search_code = address_info.get('検索コード', '')
        oaza = address_info.get('大字', '')
        chiban = address_info.get('地番', '')
        
        matches = []
        if search_code and search_code in filename:
            matches.append("検索コード")
        if oaza and oaza in filename:
            matches.append("大字名")
        if chiban and chiban in filename:
            matches.append("地番")
        
        if matches:
            analysis['住所一致要素'] = ', '.join(matches)
        else:
            analysis['住所一致要素'] = 'なし'
        
        return analysis
    
    def _validate_address_completeness(self, address_info):
        """住所の完全性を検証"""
        required_fields = ["都道府県", "市区町村", "大字", "地番"]
        optional_fields = ["丁目"]
        
        missing_required = []
        missing_optional = []
        
        for field in required_fields:
            if not address_info.get(field):
                missing_required.append(field)
        
        for field in optional_fields:
            value = address_info.get(field, '')
            if not value or value == "なし":
                missing_optional.append(field)
        
        total_fields = len(required_fields) + len(optional_fields)
        completed_fields = total_fields - len(missing_required) - len(missing_optional)
        completion_rate = (completed_fields / total_fields) * 100
        
        return {
            'completion_rate': completion_rate,
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'missing_fields': missing_required + missing_optional,
            'is_complete': len(missing_required) == 0
        }
    
    def _get_address_hierarchy(self, address_info):
        """住所の階層構造を取得"""
        hierarchy = []
        
        levels = [
            ("都道府県", "prefecture_code"),
            ("市区町村", "city_code"),
            ("大字", ""),
            ("丁目", ""),
            ("地番", "")
        ]
        
        for level_name, code_key in levels:
            value = address_info.get(level_name, '')
            if value and value != "なし":
                level_info = {
                    'level': level_name,
                    'name': value
                }
                
                # コード情報があれば追加
                if code_key == "prefecture_code":
                    code = address_info.get('検索コード', '')[:2] if address_info.get('検索コード') else ''
                elif code_key == "city_code":
                    code = address_info.get('検索コード', '')[2:5] if len(address_info.get('検索コード', '')) >= 5 else ''
                else:
                    code = ''
                
                if code:
                    level_info['code'] = code
                
                hierarchy.append(level_info)
        
        return hierarchy
    
    def _show_text_result(self, address_info, target_shp_file):
        """テキスト形式で結果を表示"""
        result_lines = [
            "=" * 60,
            "🏛️ 都道府県・市区町村選択ツール",
            f"📍 住所特定結果 - {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            "=" * 60,
            ""
        ]
        
        # 住所情報
        result_lines.append("【完全住所】")
        complete_address = self._build_complete_address_string(address_info)
        result_lines.append(complete_address)
        result_lines.append("")
        
        result_lines.append("【詳細住所情報】")
        for key, value in address_info.items():
            if value and value != "なし":
                result_lines.append(f"{key}: {value}")
        result_lines.append("")
        
        # ファイル情報
        if target_shp_file:
            result_lines.append("【特定ファイル】")
            result_lines.append(f"shpファイル: {target_shp_file}")
            
            estimated_path = self._estimate_file_path(target_shp_file)
            if estimated_path != "パス推定不可":
                result_lines.append(f"推定パス: {estimated_path}")
            result_lines.append("")
        
        # 処理情報
        result_lines.append("【処理情報】")
        result_lines.append(f"アプリバージョン: {APP_CONFIG.get('version', '不明')}")
        
        completed_count = sum(st.session_state.step_completed.values())
        total_count = len(st.session_state.step_completed)
        result_lines.append(f"完了ステップ: {completed_count}/{total_count}")
        
        result_lines.append("")
        result_lines.append("=" * 60)
        
        result_text = "\n".join(result_lines)
        
        st.markdown("### 📋 テキスト形式結果")
        st.code(result_text, language="text")
        st.success("✅ 上記テキストをコピーしてご利用ください")
    
    def _download_json_result(self, address_info, target_shp_file):
        """JSON形式で結果をダウンロード"""
        # 処理統計を取得
        processing_stats = {
            "completed_steps": sum(st.session_state.step_completed.values()),
            "total_steps": len(st.session_state.step_completed),
            "step_details": st.session_state.step_completed,
            "completion_time": datetime.now().isoformat()
        }
        
        # 住所検証結果
        validation_result = self._validate_address_completeness(address_info)
        
        # 完全なJSONデータ
        result_data = {
            "result_summary": {
                "complete_address": self._build_complete_address_string(address_info),
                "target_shp_file": target_shp_file,
                "estimated_file_path": self._estimate_file_path(target_shp_file),
                "processing_completion_time": datetime.now().isoformat()
            },
            "address_info": address_info,
            "file_analysis": self._analyze_filename(target_shp_file, address_info) if target_shp_file else {},
            "address_validation": validation_result,
            "processing_statistics": processing_stats,
            "technical_info": {
                "app_version": APP_CONFIG.get('version', '不明'),
                "gis_folder": GIS_CONFIG.get('default_gis_folder', ''),
                "session_data_size": len(str(st.session_state))
            }
        }
        
        json_str = json.dumps(result_data, ensure_ascii=False, indent=2)
        
        # ファイル名生成
        search_code = address_info.get('検索コード', 'unknown')
        chiban = address_info.get('地番', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"address_result_{search_code}_{chiban}_{timestamp}.json"
        
        st.download_button(
            label="📥 JSON形式でダウンロード",
            data=json_str,
            file_name=filename,
            mime="application/json",
            use_container_width=True
        )
        
        st.info(f"💾 ファイル名: {filename}")
    
    def _show_processing_stats(self):
        """処理統計を詳細表示"""
        st.markdown("### 📊 詳細処理統計")
        
        # ステップ別詳細統計
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**ステップ完了状況:**")
            step_names = {
                'step1': '都道府県・市区町村選択',
                'step2': '大字・丁目選択',
                'step3': '地番入力',
                'step4': 'shpファイル特定'
            }
            
            for step_key, step_name in step_names.items():
                completed = st.session_state.step_completed[step_key]
                status_icon = "✅" if completed else "❌"
                st.write(f"{status_icon} **{step_name}**: {'完了' if completed else '未完了'}")
        
        with col2:
            st.markdown("**データ読み込み統計:**")
            
            # データ統計
            stats = {}
            
            prefecture_data = st.session_state.get('prefecture_data', {})
            stats['都道府県数'] = len(prefecture_data)
            
            if prefecture_data:
                total_cities = sum(len(cities) for cities in prefecture_data.values())
                stats['総市区町村数'] = total_cities
            
            area_data = st.session_state.get('area_data', {})
            stats['読み込み大字数'] = len(area_data)
            
            if area_data:
                total_chome = sum(len(chome_list) for chome_list in area_data.values() 
                               if isinstance(chome_list, list))
                stats['読み込み丁目数'] = total_chome
            
            for key, value in stats.items():
                st.write(f"**{key}**: {value:,}")
        
        # セッションデータサイズ分析
        st.markdown("**セッションデータ分析:**")
        
        important_keys = ['prefecture_data', 'city_codes', 'area_data', 'step_completed']
        data_info = []
        
        for key in important_keys:
            if key in st.session_state:
                data_str = str(st.session_state[key])
                data_info.append({
                    'キー': key,
                    'データサイズ (文字数)': f"{len(data_str):,}",
                    'データタイプ': type(st.session_state[key]).__name__
                })
        
        if data_info:
            import pandas as pd
            df = pd.DataFrame(data_info)
            st.dataframe(df, use_container_width=True)
    
    def _reset_all_data(self):
        """全データをリセット"""
        st.warning("⚠️ この操作により、全ての入力データと進捗が失われます")
        
        if st.button("⚠️ 確認: 全データを削除", type="secondary"):
            # セッション状態のリセット
            reset_keys = [
                'selected_prefecture', 'selected_city', 'selected_oaza', 
                'selected_chome', 'input_chiban', 'area_data', 'target_shp_file',
                'gis_load_attempted', 'current_gis_code', 'selected_file_path'
            ]
            
            for key in reset_keys:
                if key == 'area_data':
                    st.session_state[key] = {}
                elif key == 'gis_load_attempted':
                    st.session_state[key] = False
                else:
                    st.session_state[key] = ""
            
            # ステップ完了状態をリセット
            for step_key in st.session_state.step_completed:
                st.session_state.step_completed[step_key] = False
            
            st.success("✅ 全データをリセットしました")
            st.info("🔄 ページが自動でリロードされます...")
            st.rerun()