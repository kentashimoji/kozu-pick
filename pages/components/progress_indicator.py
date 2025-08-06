#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pages/components/progress_indicator.py - 進捗表示コンポーネント
4段階プロセスの進捗状況を視覚的に表示
"""
import streamlit as st
from datetime import datetime

class ProgressIndicator:
    """進捗表示コンポーネント"""
    
    def __init__(self):
        self.steps_config = [
            {
                "key": "step1",
                "icon": "1️⃣",
                "title": "都道府県・市区町村",
                "description": "Excelデータから選択",
                "color": "blue"
            },
            {
                "key": "step2", 
                "icon": "2️⃣",
                "title": "大字・丁目",
                "description": "GISデータから選択",
                "color": "green"
            },
            {
                "key": "step3",
                "icon": "3️⃣", 
                "title": "地番入力",
                "description": "地番を入力・検証",
                "color": "orange"
            },
            {
                "key": "step4",
                "icon": "4️⃣",
                "title": "shpファイル特定",
                "description": "対象ファイルを特定",
                "color": "purple"
            }
        ]
    
    def render(self, style="horizontal"):
        """進捗インジケーターを描画"""
        st.markdown("### 📊 進捗状況")
        
        if style == "horizontal":
            self._render_horizontal()
        elif style == "vertical":
            self._render_vertical()
        elif style == "detailed":
            self._render_detailed()
        elif style == "compact":
            self._render_compact()
        else:
            self._render_horizontal()  # デフォルト
        
        st.markdown("---")
    
    def _render_horizontal(self):
        """水平レイアウトで描画"""
        cols = st.columns(4)
        
        for i, step_config in enumerate(self.steps_config):
            with cols[i]:
                self._render_step_card(step_config, "horizontal")
    
    def _render_vertical(self):
        """垂直レイアウトで描画"""
        for step_config in self.steps_config:
            self._render_step_card(step_config, "vertical")
            if step_config["key"] != "step4":  # 最後以外に区切り線
                st.markdown("↓")
    
    def _render_detailed(self):
        """詳細表示で描画"""
        # 全体の進捗率
        completed_count = sum(st.session_state.step_completed.values())
        total_count = len(self.steps_config)
        progress_rate = completed_count / total_count
        
        st.progress(progress_rate)
        st.write(f"**進捗率**: {progress_rate*100:.1f}% ({completed_count}/{total_count})")
        
        # 各ステップの詳細
        for step_config in self.steps_config:
            with st.expander(f"{step_config['icon']} {step_config['title']}", 
                           expanded=self._is_current_step(step_config)):
                self._render_step_details(step_config)
    
    def _render_compact(self):
        """コンパクト表示で描画"""
        completed_count = sum(st.session_state.step_completed.values())
        total_count = len(self.steps_config)
        
        # 進捗バーのみ
        progress_rate = completed_count / total_count
        st.progress(progress_rate)
        
        # ステップアイコンを一列で表示
        icon_cols = st.columns(4)
        for i, step_config in enumerate(self.steps_config):
            with icon_cols[i]:
                completed = st.session_state.step_completed[step_config["key"]]
                if completed:
                    st.success(f"{step_config['icon']}")
                else:
                    st.info(f"{step_config['icon']}")
    
    def _render_step_card(self, step_config, layout="horizontal"):
        """個別ステップカードを描画"""
        step_key = step_config["key"]
        completed = st.session_state.step_completed[step_key]
        is_current = self._is_current_step(step_config)
        
        # ステップの状態を判定
        if completed:
            status = "完了"
            status_color = "success"
            status_icon = "✅"
        elif is_current:
            status = "進行中"
            status_color = "info"
            status_icon = "🔄"
        else:
            status = "未実行"
            status_color = "secondary"
            status_icon = "⏳"
        
        # カードの描画
        if layout == "horizontal":
            if completed:
                st.success(f"{step_config['icon']} {step_config['title']} ✅")
            elif is_current:
                st.info(f"{step_config['icon']} {step_config['title']} 🔄")
            else:
                st.info(f"{step_config['icon']} {step_config['title']}")
            
            # 簡単な説明
            st.caption(step_config['description'])
        
        else:  # vertical
            # より詳細な垂直表示
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if completed:
                    st.success(step_config['icon'])
                elif is_current:
                    st.info(step_config['icon'])
                else:
                    st.info(step_config['icon'])
            
            with col2:
                st.write(f"**{step_config['title']}**")
                st.caption(step_config['description'])
                st.caption(f"状態: {status_icon} {status}")
    
    def _render_step_details(self, step_config):
        """ステップの詳細情報を描画"""
        step_key = step_config["key"]
        completed = st.session_state.step_completed[step_key]
        
        # 基本情報
        st.write(f"**説明**: {step_config['description']}")
        st.write(f"**状態**: {'完了' if completed else '未完了'}")
        
        # ステップ固有の詳細情報
        if step_key == "step1" and completed:
            self._render_step1_details()
        elif step_key == "step2" and completed:
            self._render_step2_details()
        elif step_key == "step3" and completed:
            self._render_step3_details()
        elif step_key == "step4" and completed:
            self._render_step4_details()
    
    def _render_step1_details(self):
        """Step1の詳細情報"""
        prefecture = st.session_state.get('selected_prefecture', '')
        city = st.session_state.get('selected_city', '')
        search_code = self._get_search_code()
        
        if prefecture and city:
            st.write(f"**選択済み**: {prefecture} {city}")
            if search_code:
                st.write(f"**検索コード**: {search_code}")
    
    def _render_step2_details(self):
        """Step2の詳細情報"""
        oaza = st.session_state.get('selected_oaza', '')
        chome = st.session_state.get('selected_chome', '')
        area_data = st.session_state.get('area_data', {})
        
        if oaza:
            st.write(f"**選択大字**: {oaza}")
            if chome and chome not in ["丁目データなし", "データなし"]:
                st.write(f"**選択丁目**: {chome}")
        
        if area_data:
            st.write(f"**読み込み済み大字数**: {len(area_data)}")
    
    def _render_step3_details(self):
        """Step3の詳細情報"""
        chiban = st.session_state.get('input_chiban', '')
        
        if chiban:
            st.write(f"**入力地番**: {chiban}")
            
            # 完全住所を構築
            complete_address = self._build_complete_address()
            if complete_address:
                st.write(f"**完全住所**: {complete_address}")
    
    def _render_step4_details(self):
        """Step4の詳細情報"""
        target_shp = st.session_state.get('target_shp_file', '')
        
        if target_shp:
            st.write(f"**特定ファイル**: {target_shp}")
            
            # 特定日時（推定）
            st.write(f"**特定日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    
    def _is_current_step(self, step_config):
        """現在のステップかどうかを判定"""
        step_key = step_config["key"]
        
        # 完了していないステップの中で最初のもの
        for config in self.steps_config:
            if not st.session_state.step_completed[config["key"]]:
                return config["key"] == step_key
        
        # 全て完了している場合は最後のステップ
        return step_key == "step4"
    
    def _get_search_code(self):
        """検索コードを取得"""
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
    
    def _build_complete_address(self):
        """完全住所を構築"""
        parts = []
        
        prefecture = st.session_state.get('selected_prefecture', '')
        city = st.session_state.get('selected_city', '')
        oaza = st.session_state.get('selected_oaza', '')
        chome = st.session_state.get('selected_chome', '')
        chiban = st.session_state.get('input_chiban', '')
        
        if prefecture:
            parts.append(prefecture)
        if city:
            parts.append(city)
        if oaza:
            parts.append(oaza)
        if chome and chome not in ["丁目データなし", "データなし"]:
            parts.append(chome)
        if chiban:
            parts.append(chiban)
        
        return "".join(parts) if parts else ""
    
    def get_completion_summary(self):
        """完了状況のサマリーを取得"""
        completed_steps = []
        pending_steps = []
        
        for step_config in self.steps_config:
            step_key = step_config["key"]
            if st.session_state.step_completed[step_key]:
                completed_steps.append(step_config["title"])
            else:
                pending_steps.append(step_config["title"])
        
        completed_count = len(completed_steps)
        total_count = len(self.steps_config)
        progress_rate = (completed_count / total_count) * 100
        
        return {
            "completed_count": completed_count,
            "total_count": total_count,
            "progress_rate": progress_rate,
            "completed_steps": completed_steps,
            "pending_steps": pending_steps,
            "next_step": pending_steps[0] if pending_steps else None,
            "is_complete": completed_count == total_count
        }
    
    def render_mini_progress(self):
        """ミニ進捗表示（サイドバー用など）"""
        summary = self.get_completion_summary()
        
        # 進捗バー
        st.progress(summary["progress_rate"] / 100)
        st.write(f"**進捗**: {summary['progress_rate']:.0f}%")
        
        # 現在のステップ
        if summary["next_step"]:
            st.info(f"**次のステップ**: {summary['next_step']}")
        else:
            st.success("**🎉 全ステップ完了！**")
    
    def render_step_navigation(self):
        """ステップナビゲーション（ジャンプ機能付き）"""
        st.markdown("### 🧭 ステップナビゲーション")
        
        nav_cols = st.columns(4)
        
        for i, step_config in enumerate(self.steps_config):
            with nav_cols[i]:
                step_key = step_config["key"]
                completed = st.session_state.step_completed[step_key]
                is_current = self._is_current_step(step_config)
                
                # ジャンプボタン（完了済みステップのみ）
                if completed:
                    if st.button(f"{step_config['icon']} {step_config['title']}", 
                               key=f"nav_{step_key}",
                               help=f"{step_config['title']}にジャンプ"):
                        # ジャンプ処理（実装は呼び出し側で行う）
                        st.session_state.nav_jump_target = step_key
                        st.rerun()
                else:
                    # 未完了ステップは無効化
                    st.button(f"{step_config['icon']} {step_config['title']}", 
                            disabled=True,
                            key=f"nav_disabled_{step_key}")
        
        # ジャンプ処理の説明
        st.caption("💡 完了済みのステップをクリックすると該当箇所にジャンプできます")