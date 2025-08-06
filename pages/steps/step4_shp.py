#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pages/steps/step4_shp.py - Step4: shpファイル特定
"""

import streamlit as st
from datetime import datetime

try:
    from config.settings import GIS_CONFIG
    from src.address_builder import AddressBuilder
except ImportError:
    GIS_CONFIG = {"default_gis_folder": ""}
    AddressBuilder = None

class Step4Shp:
    def __init__(self, app):
        self.app = app
        self.address_builder = AddressBuilder() if AddressBuilder else None
    
    def render(self):
        """Step4を描画"""
        st.markdown("---")
        st.header("4️⃣ shpファイル特定")
        st.markdown("**特定された住所情報から対象shpファイルを特定**")
        
        # 完全な住所情報を構築
        complete_address_info = self._build_complete_address_info()
        
        # 特定条件と実行UI
        self._render_identification_ui(complete_address_info)
        
        # shpファイル特定結果の表示
        target_shp = st.session_state.get('target_shp_file', '')
        if target_shp:
            self._render_identification_result(target_shp, complete_address_info)
    
    def _build_complete_address_info(self):
        """完全な住所情報を構築"""
        if self.address_builder:
            return self.address_builder.build_complete_address_info()
        
        # フォールバック：基本的な住所情報構築
        selected_chome = st.session_state.get('selected_chome', '')
        if selected_chome in ["丁目データなし", "データなし", ""]:
            selected_chome = "なし"
        
        return {
            "都道府県": st.session_state.get('selected_prefecture', ''),
            "市区町村": st.session_state.get('selected_city', ''),
            "大字": st.session_state.get('selected_oaza', ''),
            "丁目": selected_chome,
            "地番": st.session_state.get('input_chiban', ''),
            "団体コード": self._get_full_code(),
            "検索コード": self._get_search_code()
        }
    
    def _render_identification_ui(self, complete_address_info):
        """特定条件と実行UIを描画"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📍 特定条件")
            
            # 住所情報の表示
            for key, value in complete_address_info.items():
                if value and value != "なし":
                    if key == "検索コード":
                        st.write(f"**{key}**: `{value}`")
                    else:
                        st.write(f"**{key}**: {value}")
            
            # 検索パターンのプレビュー
            with st.expander("🔍 検索パターンプレビュー"):
                patterns = self._generate_shp_patterns(complete_address_info)
                st.write("**生成される検索パターン:**")
                for i, pattern in enumerate(patterns[:5], 1):  # 最初の5個まで表示
                    st.write(f"{i}. `{pattern}`")
                if len(patterns) > 5:
                    st.write(f"... 他{len(patterns)-5}個のパターン")
        
        with col2:
            st.subheader("🔧 実行")
            
            # 自動特定ボタン
            if st.button("🔍 shpファイルを特定", 
                        type="primary", 
                        use_container_width=True):
                self._identify_target_shp(complete_address_info)
            
            # 手動入力オプション
            st.markdown("**手動指定:**")
            manual_shp = st.text_input(
                "ファイル名:",
                placeholder="例: 47201_那覇_1174.shp",
                help="手動でshpファイル名を指定できます"
            )
            
            if st.button("📝 手動設定", use_container_width=True) and manual_shp:
                st.session_state.target_shp_file = manual_shp.strip()
                st.session_state.step_completed['step4'] = True
                st.success(f"✅ 手動設定完了: {manual_shp}")
                st.rerun()
    
    def _render_identification_result(self, target_shp, complete_address_info):
        """特定結果を表示"""
        st.success(f"✅ 特定されたshpファイル: **{target_shp}**")
        
        if not st.session_state.step_completed['step4']:
            st.session_state.step_completed['step4'] = True
            st.rerun()
        
        # ファイル詳細情報
        with st.expander("📄 ファイル詳細情報"):
            st.write(f"**ファイル名**: {target_shp}")
            st.write(f"**特定日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
            
            # ファイルパスの推定
            estimated_path = self._estimate_shp_file_path(target_shp)
            if estimated_path != "パス推定不可":
                st.write(f"**推定パス**: `{estimated_path}`")
            
            # ファイルサイズ推定（もし情報があれば）
            file_info = self._get_file_info(target_shp)
            if file_info:
                for key, value in file_info.items():
                    st.write(f"**{key}**: {value}")
        
        # 特定方法の詳細
        with st.expander("🔧 特定処理詳細"):
            self._show_identification_details(complete_address_info, target_shp)
    
    def _identify_target_shp(self, address_info):
        """対象shpファイルを特定"""
        try:
            with st.spinner("🔍 shpファイルを検索中..."):
                # 実際のファイル検索を試行（アプリ連携）
                if hasattr(self.app, 'search_shp_files_by_address'):
                    found_files = self.app.search_shp_files_by_address(address_info)
                    
                    if found_files:
                        # 最も適切なファイルを選択
                        target_shp = found_files[0].get('name', '')
                        st.session_state.target_shp_file = target_shp
                        st.success(f"🎯 shpファイルを特定しました: {target_shp}")
                        
                        # 複数ファイルが見つかった場合の表示
                        if len(found_files) > 1:
                            st.info(f"📄 他に{len(found_files)-1}個の候補ファイルが見つかりました")
                            with st.expander(f"🔍 他の候補ファイル ({len(found_files)-1}個)"):
                                for i, file_info in enumerate(found_files[1:], 1):
                                    file_name = file_info.get('name', 'Unknown')
                                    file_size = file_info.get('size', 'Unknown')
                                    st.write(f"{i}. **{file_name}** ({file_size} bytes)")
                        return
                
                # フォールバック：パターンベースの特定
                st.info("💡 パターンベースでファイルを特定します...")
                shp_patterns = self._generate_shp_patterns(address_info)
                target_shp = self._select_best_shp_pattern(shp_patterns)
                
                if target_shp:
                    st.session_state.target_shp_file = target_shp
                    st.success(f"🎯 shpファイルを特定しました（パターンベース）: {target_shp}")
                else:
                    st.warning("⚠️ 条件に一致するshpファイルが特定できませんでした")
                    self._handle_identification_failure(address_info)
                    
        except Exception as e:
            st.error(f"❌ shpファイル特定エラー: {str(e)}")
            
            # エラー時のフォールバック
            fallback_shp = self._create_fallback_shp_name(address_info)
            st.session_state.target_shp_file = fallback_shp
            st.info(f"💡 フォールバックファイル名: {fallback_shp}")
    
    def _handle_identification_failure(self, address_info):
        """特定失敗時の処理"""
        st.markdown("**🔧 トラブルシューティング:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # デバッグ情報の表示
            with st.expander("🔧 デバッグ情報"):
                patterns = self._generate_shp_patterns(address_info)
                st.write("**生成されたパターン:**")
                for i, pattern in enumerate(patterns, 1):
                    st.write(f"{i}. {pattern}")
        
        with col2:
            # 代替案の提示
            st.markdown("**💡 代替案:**")
            
            # より一般的なパターンで再試行
            if st.button("🔄 一般的なパターンで再試行"):
                general_patterns = self._generate_general_patterns(address_info)
                if general_patterns:
                    st.session_state.target_shp_file = general_patterns[0]
                    st.success(f"✅ 一般パターンで設定: {general_patterns[0]}")
                    st.rerun()
            
            # 自動生成
            if st.button("🤖 自動生成"):
                auto_shp = self._create_fallback_shp_name(address_info)
                st.session_state.target_shp_file = auto_shp
                st.success(f"✅ 自動生成: {auto_shp}")
                st.rerun()
    
    def _generate_shp_patterns(self, address_info):
        """shpファイル名のパターンを生成"""
        patterns = []
        
        # 基本情報
        search_code = address_info.get('検索コード', '')
        prefecture = address_info.get('都道府県', '')
        city = address_info.get('市区町村', '')
        oaza = address_info.get('大字', '')
        chome = address_info.get('丁目', '')
        chiban = address_info.get('地番', '')
        
        # パターン1: 最も詳細な住所ベース
        if all([search_code, oaza, chiban]):
            detailed_name = f"{search_code}_{oaza}"
            if chome and chome != "なし":
                detailed_name += f"_{chome}"
            detailed_name += f"_{chiban}.shp"
            patterns.append(detailed_name)
        
        # パターン2: 大字・丁目ベース
        if search_code and oaza:
            area_name = f"{search_code}_{oaza}"
            if chome and chome != "なし":
                area_name += f"_{chome}"
            area_name += ".shp"
            patterns.append(area_name)
        
        # パターン3: 市区町村名込み
        if search_code and city:
            city_clean = city.replace('市', '').replace('区', '').replace('町', '').replace('村', '')
            city_name = f"{search_code}_{city_clean}"
            if oaza:
                city_name += f"_{oaza}"
            city_name += ".shp"
            patterns.append(city_name)
        
        # パターン4: 地籍関連の命名パターン
        if search_code:
            patterns.extend([
                f"{search_code}_地籍.shp",
                f"{search_code}_筆.shp",
                f"{search_code}_公共座標15系_筆R_2025.shp",  # 沖縄県特有
                f"{search_code}_公共座標16系_筆R_2025.shp",  # 石垣市特有
                f"{search_code}.shp",
                f"cadastral_{search_code}.shp",
                f"parcel_{search_code}.shp"
            ])
        
        # パターン5: 都道府県コードベース
        if search_code and len(search_code) >= 2:
            prefecture_code = search_code[:2]
            prefecture_clean = prefecture.replace('県', '').replace('府', '').replace('都', '')
            patterns.extend([
                f"{prefecture_code}_{prefecture_clean}.shp",
                f"{prefecture_code}_all.shp",
                f"{prefecture_code}.shp"
            ])
        
        return patterns
    
    def _generate_general_patterns(self, address_info):
        """より一般的なパターンを生成"""
        search_code = address_info.get('検索コード', '')
        city = address_info.get('市区町村', '')
        
        general_patterns = []
        
        if search_code:
            general_patterns.extend([
                f"{search_code}.shp",
                f"{search_code}_all.shp",
                f"{search_code}_general.shp"
            ])
        
        if city:
            city_clean = city.replace('市', '').replace('区', '').replace('町', '').replace('村', '')
            general_patterns.extend([
                f"{city_clean}.shp",
                f"{city_clean}_cadastral.shp"
            ])
        
        return general_patterns
    
    def _select_best_shp_pattern(self, patterns):
        """最適なshpファイルパターンを選択"""
        # 実際の実装では、ここでファイルシステムやAPIを使って
        # 存在するファイルをチェックする
        
        # 優先度順に返す（最も詳細なパターンを優先）
        if patterns:
            return patterns[0]
        
        return None
    
    def _create_fallback_shp_name(self, address_info):
        """フォールバック用のshpファイル名を作成"""
        search_code = address_info.get('検索コード', '99999')
        city = address_info.get('市区町村', 'Unknown')
        chiban = address_info.get('地番', '1')
        
        # 基本的なフォールバック名
        city_clean = city.replace('市', '').replace('区', '').replace('町', '').replace('村', '')
        fallback_name = f"{search_code}_{city_clean}_{chiban}.shp"
        return fallback_name
    
    def _estimate_shp_file_path(self, target_shp):
        """shpファイルパスを推定"""
        gis_folder = GIS_CONFIG.get('default_gis_folder', '') if 'GIS_CONFIG' in globals() else ''
        
        if gis_folder and target_shp:
            # GitHub Raw URLの場合
            if 'github' in gis_folder.lower():
                if gis_folder.endswith('/'):
                    return f"{gis_folder}{target_shp}"
                else:
                    return f"{gis_folder}/{target_shp}"
            else:
                return f"{gis_folder}/{target_shp}"
        
        return "パス推定不可"
    
    def _get_file_info(self, target_shp):
        """ファイル情報を取得（可能であれば）"""
        # 実際の実装では、ここでファイルシステムやAPIを使って
        # ファイル情報を取得する
        
        # 現在はダミー情報を返す
        if target_shp:
            return {
                "推定ファイルタイプ": "Shapefile",
                "関連ファイル": f"{target_shp[:-4]}.dbf, {target_shp[:-4]}.shx, {target_shp[:-4]}.prj"
            }
        
        return {}
    
    def _show_identification_details(self, address_info, target_shp):
        """特定処理の詳細を表示"""
        st.markdown("**処理手順:**")
        st.write("1. 住所情報から検索パターンを生成")
        st.write("2. 優先度順でファイル検索を実行")
        st.write("3. 最適なファイルを選択・特定")
        
        # 使用された検索条件
        st.markdown("**使用された条件:**")
        for key, value in address_info.items():
            if value and value != "なし":
                st.write(f"- **{key}**: {value}")
        
        # 特定結果の分析
        st.markdown("**特定結果分析:**")
        if target_shp:
            # ファイル名からパターンを推定
            if '_' in target_shp:
                parts = target_shp.replace('.shp', '').split('_')
                st.write(f"- **構成要素数**: {len(parts)}")
                st.write(f"- **命名パターン**: {'_'.join(['X'] * len(parts))}")
                
                # 特徴的な要素の識別
                features = []
                for part in parts:
                    if part.isdigit() and len(part) == 5:
                        features.append("5桁コード")
                    elif part.isdigit():
                        features.append("数値")
                    elif '丁目' in part:
                        features.append("丁目情報")
                    elif any(keyword in part for keyword in ['地籍', '筆', 'cadastral', 'parcel']):
                        features.append("地籍キーワード")
                    else:
                        features.append("地名・その他")
                
                if features:
                    st.write(f"- **含まれる要素**: {', '.join(features)}")
    
    def _get_full_code(self):
        """完全な団体コードを取得"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        if not (selected_prefecture and selected_city):
            return ""
        
        city_codes = st.session_state.get('city_codes', {})
        city_key = f"{selected_prefecture}_{selected_city}"
        city_info = city_codes.get(city_key, {})
        
        return city_info.get('full_code', '')
    
    def _get_search_code(self):
        """検索用5桁コードを取得"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        if not (selected_prefecture and selected_city):
            return ""
        
        prefecture_codes = st.session_state.get('prefecture_codes', {})
        city_codes = st.session_state.get('city_codes', {})
        
        prefecture_code = prefecture_codes.get(selected_prefecture, "")
        city_key = f"{selected_prefecture}_{selected_city}"
        city_info = city_codes.get(city_key, {})
        city_code = city_info.get('city_code', "")
        
        return f"{prefecture_code}{city_code}"