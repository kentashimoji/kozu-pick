#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pages/steps/step3_chiban.py - Step3: 地番入力
"""

import streamlit as st
import re

class Step3Chiban:
    def __init__(self, app):
        self.app = app
    
    def render(self):
        """Step3を描画"""
        st.markdown("---")
        st.header("3️⃣ 地番入力")
        st.markdown("**地番を入力してください**")
        
        # 現在の住所確認
        self._render_current_address()
        
        # 地番入力UI
        self._render_chiban_input()
        
        # 地番入力例・ヘルプ
        self._render_input_help()
        
        # Step3完了表示
        if st.session_state.step_completed['step3']:
            self._render_completion_status()
    
    def _render_current_address(self):
        """現在の住所を表示"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        selected_oaza = st.session_state.get('selected_oaza', '')
        selected_chome = st.session_state.get('selected_chome', '')
        
        current_address = f"{selected_prefecture}{selected_city}{selected_oaza}"
        if selected_chome and selected_chome not in ["丁目データなし", "データなし"]:
            current_address += selected_chome
        
        st.info(f"📍 現在の住所: **{current_address}**")
    
    def _render_chiban_input(self):
        """地番入力UIを描画"""
        current_chiban = st.session_state.get('input_chiban', '')
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            input_chiban = st.text_input(
                "地番を入力してください:",
                value=current_chiban,
                placeholder="例: 123-4, 45番地6, 78-9-10",
                help="地番は数字とハイフン、番地などの形式で入力してください",
                key="chiban_input"
            )
        
        with col2:
            st.write("")  # スペース調整
            if st.button("✅ 地番を確定", use_container_width=True):
                self._validate_and_set_chiban(input_chiban)
        
        # リアルタイム検証表示
        if input_chiban.strip():
            self._show_realtime_validation(input_chiban.strip())
    
    def _validate_and_set_chiban(self, input_chiban):
        """地番の検証と設定"""
        if not input_chiban.strip():
            st.error("❌ 地番を入力してください")
            return
        
        chiban = input_chiban.strip()
        
        # 地番の形式チェック
        validation_result = self._validate_chiban(chiban)
        
        if validation_result['valid']:
            st.session_state.input_chiban = chiban
            st.session_state.step_completed['step3'] = True
            st.success(f"✅ 地番確定: {chiban}")
            
            # 正規化された地番を表示
            if validation_result['normalized'] != chiban:
                st.info(f"💡 正規化された地番: {validation_result['normalized']}")
                st.session_state.input_chiban = validation_result['normalized']
            
            st.rerun()
        else:
            st.error(f"❌ {validation_result['error']}")
            
            # 修正提案があれば表示
            if validation_result.get('suggestion'):
                st.info(f"💡 修正提案: {validation_result['suggestion']}")
    
    def _show_realtime_validation(self, chiban):
        """リアルタイム検証結果を表示"""
        validation_result = self._validate_chiban(chiban)
        
        if validation_result['valid']:
            st.success("✅ 有効な地番形式です")
            
            # 地番の詳細分析を表示
            analysis = self._analyze_chiban(chiban)
            if analysis:
                with st.expander("🔍 地番分析"):
                    for key, value in analysis.items():
                        st.write(f"**{key}**: {value}")
        else:
            st.warning(f"⚠️ {validation_result['error']}")
    
    def _validate_chiban(self, chiban):
        """地番の形式をチェック"""
        if not chiban:
            return {'valid': False, 'error': '地番が入力されていません'}
        
        # 全角文字を半角に変換
        normalized_chiban = self._normalize_chiban(chiban)
        
        # 地番の一般的なパターンをチェック
        patterns = [
            (r'^\d+(-\d+)*$', '数字とハイフン形式'),  # 123-4-5形式
            (r'^\d+番地\d*$', '番地形式'),           # 123番地4形式
            (r'^\d+$', '単一番号形式'),              # 123形式
            (r'^\d+番地$', '番地のみ形式'),          # 123番地形式
            (r'^\d+の\d+$', '「の」区切り形式'),      # 123の4形式
        ]
        
        for pattern, description in patterns:
            if re.match(pattern, normalized_chiban):
                return {
                    'valid': True,
                    'normalized': normalized_chiban,
                    'pattern': description
                }
        
        # 修正可能なエラーのチェック
        suggestion = self._get_correction_suggestion(chiban)
        
        return {
            'valid': False,
            'error': '地番の形式が正しくありません',
            'suggestion': suggestion
        }
    
    def _normalize_chiban(self, chiban):
        """地番を正規化"""
        # 全角数字を半角に変換
        normalized = chiban
        for i in range(10):
            normalized = normalized.replace(chr(0xFF10 + i), str(i))
        
        # 全角ハイフンを半角に変換
        normalized = normalized.replace('－', '-').replace('ー', '-')
        
        # 不要な空白を削除
        normalized = normalized.strip()
        
        return normalized
    
    def _get_correction_suggestion(self, chiban):
        """修正提案を生成"""
        # よくある間違いパターンの修正提案
        suggestions = []
        
        # スペースが含まれている場合
        if ' ' in chiban or '　' in chiban:
            clean_chiban = chiban.replace(' ', '').replace('　', '')
            suggestions.append(f"スペースを除去: '{clean_chiban}'")
        
        # 「・」や「。」が含まれている場合
        if '・' in chiban or '。' in chiban:
            corrected = chiban.replace('・', '-').replace('。', '-')
            suggestions.append(f"区切り文字を修正: '{corrected}'")
        
        # 全角文字が含まれている場合
        normalized = self._normalize_chiban(chiban)
        if normalized != chiban:
            suggestions.append(f"半角に変換: '{normalized}'")
        
        return suggestions[0] if suggestions else None
    
    def _analyze_chiban(self, chiban):
        """地番を分析"""
        analysis = {}
        
        # 基本情報
        analysis['文字数'] = len(chiban)
        
        # パターン分析
        if '-' in chiban:
            parts = chiban.split('-')
            analysis['構成'] = f"{len(parts)}つの番号からなる地番"
            analysis['主番'] = parts[0]
            if len(parts) > 1:
                analysis['枝番'] = '-'.join(parts[1:])
        elif '番地' in chiban:
            if chiban.endswith('番地'):
                analysis['構成'] = "番地形式（枝番なし）"
                analysis['主番'] = chiban.replace('番地', '')
            else:
                parts = chiban.split('番地')
                analysis['構成'] = "番地形式（枝番あり）"
                analysis['主番'] = parts[0]
                analysis['枝番'] = parts[1]
        else:
            analysis['構成'] = "単一番号"
            analysis['主番'] = chiban
        
        # 数値範囲の妥当性チェック
        try:
            main_num = int(analysis['主番'])
            if main_num > 9999:
                analysis['注意'] = "主番が大きすぎる可能性があります"
            elif main_num <= 0:
                analysis['注意'] = "主番は正の数である必要があります"
        except ValueError:
            analysis['注意'] = "主番が数値ではありません"
        
        return analysis
    
    def _render_input_help(self):
        """地番入力例・ヘルプを表示"""
        with st.expander("📝 地番入力例とヘルプ"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**有効な地番形式:**")
                examples = [
                    ("123-4", "基本的な地番"),
                    ("45番地6", "番地形式"),
                    ("78-9-10", "枝番付き"),
                    ("100", "単一番号"),
                    ("5番地", "番地のみ"),
                    ("250の3", "「の」区切り")
                ]
                
                for example, description in examples:
                    st.write(f"- `{example}` ({description})")
            
            with col2:
                st.markdown("**注意事項:**")
                st.write("- 数字、ハイフン(-)、番地の文字を使用")
                st.write("- 全角・半角どちらでも自動変換されます")
                st.write("- スペースは自動的に除去されます")
                st.write("- 主番は1以上の数値である必要があります")
                
                st.markdown("**よくある間違い:**")
                st.write("- `123．4` → `123-4` に修正")
                st.write("- `45 番地 6` → `45番地6` に修正")
                st.write("- `７８-９` → `78-9` に修正")
    
    def _render_completion_status(self):
        """完了状況を表示"""
        input_chiban = st.session_state.get('input_chiban', '')
        
        # 現在の完全住所を構築
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        selected_oaza = st.session_state.get('selected_oaza', '')
        selected_chome = st.session_state.get('selected_chome', '')
        
        current_address = f"{selected_prefecture}{selected_city}{selected_oaza}"
        if selected_chome and selected_chome not in ["丁目データなし", "データなし"]:
            current_address += selected_chome
        
        complete_address = f"{current_address}{input_chiban}"
        st.success(f"✅ 完全住所: **{complete_address}**")
        
        # 詳細情報の表示
        with st.expander("📊 地番詳細情報"):
            st.write(f"**入力地番**: {input_chiban}")
            
            # 地番分析結果
            analysis = self._analyze_chiban(input_chiban)
            if analysis:
                st.markdown("**地番分析:**")
                for key, value in analysis.items():
                    if key == '注意':
                        st.warning(f"⚠️ **{key}**: {value}")
                    else:
                        st.write(f"- **{key}**: {value}")
            
            # 次のステップに向けた情報
            st.markdown("**次のステップ:**")
            st.write("- この住所情報を使ってshpファイルを特定します")
            st.write("- 複数の命名パターンで検索を行います")
            st.write("- 最適なファイルが自動選択されます")