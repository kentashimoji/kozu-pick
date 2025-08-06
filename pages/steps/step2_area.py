#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pages/steps/step2_area.py - Step2: 大字・丁目選択
シンプル化版：まず基本的な選択機能を動作させる
"""

import streamlit as st

class Step2Area:
    def __init__(self, app):
        self.app = app
    
    def render(self):
        """Step2を描画"""
        st.markdown("---")
        st.header("2️⃣ 大字・丁目選択")
        st.markdown("**5桁コードで特定されたファイルから大字・丁目を表示**")
        
        # セッション状態の確認
        area_data = st.session_state.get('area_data', {})
        
        # デバッグ情報を表示
        self._render_debug_info(area_data)
        
        # データがない場合の処理
        if not area_data:
            self._render_no_data_state()
            return
        
        # 大字・丁目選択UI（シンプル版）
        self._render_simple_area_selection(area_data)
        
        # Step2完了表示
        if st.session_state.get('step_completed', {}).get('step2', False):
            self._render_completion_status()
    
    def _render_debug_info(self, area_data):
        """デバッグ情報を表示"""
        with st.expander("🔍 デバッグ情報（詳細）"):
            st.write("**セッション状態:**")
            st.write(f"- area_data存在: {'✅' if area_data else '❌'}")
            st.write(f"- area_data件数: {len(area_data) if area_data else 0}")
            st.write(f"- area_dataタイプ: {type(area_data)}")
            st.write(f"- selected_oaza: '{st.session_state.get('selected_oaza', '')}'")
            st.write(f"- selected_chome: '{st.session_state.get('selected_chome', '')}'")
            st.write(f"- step2_completed: {st.session_state.get('step_completed', {}).get('step2', False)}")
            
            if area_data:
                st.write(f"**area_data内容（最初の5件）:**")
                for i, (oaza, chome_list) in enumerate(list(area_data.items())[:5]):
                    st.write(f"  {i+1}. キー: '{oaza}' (タイプ: {type(oaza)})")
                    st.write(f"       値: {chome_list} (タイプ: {type(chome_list)})")
                    if i == 0:  # 最初の項目の詳細
                        st.write(f"       値の長さ: {len(chome_list) if chome_list else 0}")
                        if chome_list and len(chome_list) > 0:
                            st.write(f"       最初の丁目: '{chome_list[0]}' (タイプ: {type(chome_list[0])})")
            
            # セッション状態の全体確認
            st.write("**全セッション状態キー:**")
            session_keys = list(st.session_state.keys())
            st.write(f"キー数: {len(session_keys)}")
            for key in session_keys[:10]:  # 最初の10個のキーのみ表示
                value = st.session_state.get(key, 'なし')
                st.write(f"  - {key}: {type(value)} = {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
    
    def _render_no_data_state(self):
        """データなし状態の表示"""
        st.warning("⚠️ 大字・丁目データが読み込まれていません")
        
        # テストデータボタン
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧪 テストデータ1（数字形式）", use_container_width=True):
                test_data = {
                    "001": ["001丁目", "002丁目", "003丁目"],
                    "002": ["001丁目", "002丁目"],  
                    "003": ["001丁目"]
                }
                st.session_state.area_data = test_data
                st.rerun()
        
        with col2:
            if st.button("🧪 テストデータ2（文字形式）", use_container_width=True):
                test_data = {
                    "那覇": ["1丁目", "2丁目", "3丁目"],
                    "首里": ["1丁目", "2丁目", "3丁目", "4丁目"],
                    "真嘉比": ["1丁目", "2丁目"]
                }
                st.session_state.area_data = test_data
                st.rerun()
        
        with col3:
            if st.button("🧪 テストデータ3（混合）", use_container_width=True):
                test_data = {
                    "001": ["001丁目", "002丁目"],
                    "那覇": ["1丁目", "2丁目"],
                    "002": ["1", "2"],
                    "首里": ["データなし"]
                }
                st.session_state.area_data = test_data
                st.rerun()
        
        # 手動データ入力
        st.write("### 📝 手動データ入力（テスト用）")
        with st.form("manual_data_form"):
            oaza_input = st.text_input("大字名を入力", value="テスト大字")
            chome_input = st.text_area("丁目名を入力（改行区切り）", value="1丁目\n2丁目\n3丁目")
            
            if st.form_submit_button("📥 手動データを設定"):
                if oaza_input:
                    chome_list = [line.strip() for line in chome_input.split('\n') if line.strip()]
                    if not chome_list:
                        chome_list = ["データなし"]
                    
                    manual_data = {oaza_input: chome_list}
                    st.session_state.area_data = manual_data
                    st.success(f"✅ 手動データを設定しました: {oaza_input}")
                    st.rerun()
    
    def _render_simple_area_selection(self, area_data):
        """シンプルな大字・丁目選択UI"""
        st.write("### 📍 エリア選択")
        
        # area_dataが正常かチェック
        if not isinstance(area_data, dict):
            st.error(f"❌ area_dataが辞書形式ではありません: {type(area_data)}")
            return
        
        if len(area_data) == 0:
            st.warning("⚠️ area_dataが空です")
            return
        
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_simple_oaza_selection(area_data)
        
        with col2:
            self._render_simple_chome_selection(area_data)
    
    def _render_simple_oaza_selection(self, area_data):
        """シンプルな大字選択"""
        st.write("#### 🏞️ 大字選択")
        
        try:
            # 大字リストを取得
            oaza_list = list(area_data.keys())
            st.write(f"利用可能大字: {len(oaza_list)}個")
            st.write(f"大字一覧: {oaza_list[:5]}{'...' if len(oaza_list) > 5 else ''}")
            
            if not oaza_list:
                st.error("❌ 大字リストが空です")
                return
            
            # 現在の選択状況
            current_oaza = st.session_state.get('selected_oaza', '')
            st.write(f"現在選択中: '{current_oaza}'")
            
            # selectboxの作成（キーを指定して重複を避ける）
            selected_oaza = st.selectbox(
                "大字を選択してください:",
                options=["選択してください"] + oaza_list,
                key="simple_oaza_select"  # 固定キー
            )
            
            st.write(f"選択された値: '{selected_oaza}'")
            
            # 選択処理
            if selected_oaza != "選択してください":
                if st.session_state.get('selected_oaza') != selected_oaza:
                    st.write(f"🔄 大字を更新: '{current_oaza}' → '{selected_oaza}'")
                    st.session_state.selected_oaza = selected_oaza
                    st.session_state.selected_chome = ""  # 丁目をリセット
                    st.success(f"✅ 大字選択: {selected_oaza}")
                    st.rerun()
                else:
                    st.info(f"ℹ️ 既に選択済み: {selected_oaza}")
            else:
                st.info("まず大字を選択してください")
        
        except Exception as e:
            st.error(f"❌ 大字選択エラー: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    def _render_simple_chome_selection(self, area_data):
        """シンプルな丁目選択"""
        st.write("#### 🏘️ 丁目選択")
        
        selected_oaza = st.session_state.get('selected_oaza', '')
        
        if not selected_oaza:
            st.selectbox(
                "丁目を選択してください:",
                ["まず大字を選択してください"],
                disabled=True,
                key="simple_chome_disabled"
            )
            return
        
        st.write(f"選択された大字: '{selected_oaza}'")
        
        try:
            # 選択された大字の丁目リストを取得
            chome_list = area_data.get(selected_oaza, [])
            st.write(f"利用可能丁目: {chome_list}")
            
            if not chome_list or chome_list == ["丁目データなし"] or chome_list == ["データなし"]:
                st.info("この大字には丁目データがありません")
                st.selectbox(
                    "丁目を選択してください:",
                    ["丁目データなし"],
                    disabled=True,
                    key="simple_chome_no_data"
                )
                # 大字のみでStep2完了
                if not st.session_state.get('step_completed', {}).get('step2', False):
                    # step_completedを初期化
                    if 'step_completed' not in st.session_state:
                        st.session_state.step_completed = {}
                    st.session_state.step_completed['step2'] = True
                    st.success("✅ 大字選択完了（丁目データなし）")
                    st.rerun()
            else:
                # 丁目選択UI
                current_chome = st.session_state.get('selected_chome', '')
                
                selected_chome = st.selectbox(
                    "丁目を選択してください:",
                    options=["選択してください"] + chome_list,
                    key="simple_chome_select"
                )
                
                st.write(f"選択された丁目: '{selected_chome}'")
                
                if selected_chome != "選択してください":
                    if st.session_state.get('selected_chome') != selected_chome:
                        st.session_state.selected_chome = selected_chome
                        
                        # step_completedを初期化
                        if 'step_completed' not in st.session_state:
                            st.session_state.step_completed = {}
                        st.session_state.step_completed['step2'] = True
                        
                        st.success(f"✅ 選択完了: {selected_oaza} {selected_chome}")
                        st.rerun()
                    else:
                        st.info(f"ℹ️ 既に選択済み: {selected_chome}")
        
        except Exception as e:
            st.error(f"❌ 丁目選択エラー: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    def _render_completion_status(self):
        """完了状況を表示"""
        selected_oaza = st.session_state.get('selected_oaza', '')
        selected_chome = st.session_state.get('selected_chome', '')
        
        address_parts = [selected_oaza]
        if selected_chome and selected_chome not in ["丁目データなし", "データなし"]:
            address_parts.append(selected_chome)
        
        st.success(f"✅ Step2完了: {' '.join(address_parts)}")
        
        # 詳細情報
        with st.expander("📊 選択結果詳細"):
            st.write(f"**大字**: {selected_oaza}")
            st.write(f"**丁目**: {selected_chome or '指定なし'}")
            
            # リセットボタン
            if st.button("🔄 Step2をリセット"):
                st.session_state.selected_oaza = ""
                st.session_state.selected_chome = ""
                if 'step_completed' not in st.session_state:
                    st.session_state.step_completed = {}
                st.session_state.step_completed['step2'] = False
                st.rerun()