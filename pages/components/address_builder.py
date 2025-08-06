#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
src/address_builder.py - 住所情報構築ユーティリティ
"""

import streamlit as st

class AddressBuilder:
    """住所情報の構築と管理を行うユーティリティクラス"""
    
    def __init__(self):
        pass
    
    def build_complete_address_info(self):
        """完全な住所情報を構築"""
        selected_chome = st.session_state.get('selected_chome', '')
        if selected_chome in ["丁目データなし", "データなし", ""]:
            selected_chome = "なし"
        
        return {
            "都道府県": st.session_state.get('selected_prefecture', ''),
            "市区町村": st.session_state.get('selected_city', ''),
            "大字": st.session_state.get('selected_oaza', ''),
            "丁目": selected_chome,
            "地番": st.session_state.get('input_chiban', ''),
            "団体コード": self.get_full_code(),
            "検索コード": self.get_search_code()
        }
    
    def get_complete_address_string(self):
        """完全住所文字列を取得"""
        address_info = self.build_complete_address_info()
        
        address_parts = []
        for key in ["都道府県", "市区町村", "大字", "丁目", "地番"]:
            value = address_info.get(key, '')
            if value and value != "なし":
                address_parts.append(value)
        
        return "".join(address_parts)
    
    def get_full_code(self):
        """完全な団体コードを取得"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        if not (selected_prefecture and selected_city):
            return ""
        
        city_codes = st.session_state.get('city_codes', {})
        city_key = f"{selected_prefecture}_{selected_city}"
        city_info = city_codes.get(city_key, {})
        
        return city_info.get('full_code', '')
    
    def get_search_code(self):
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
    
    def get_prefecture_code(self):
        """都道府県コードを取得"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        
        if not selected_prefecture:
            return ""
        
        prefecture_codes = st.session_state.get('prefecture_codes', {})
        return prefecture_codes.get(selected_prefecture, "")
    
    def get_city_code(self):
        """市区町村コードを取得"""
        selected_prefecture = st.session_state.get('selected_prefecture', '')
        selected_city = st.session_state.get('selected_city', '')
        
        if not (selected_prefecture and selected_city):
            return ""
        
        city_codes = st.session_state.get('city_codes', {})
        city_key = f"{selected_prefecture}_{selected_city}"
        city_info = city_codes.get(city_key, {})
        
        return city_info.get('city_code', '')
    
    def validate_address_completeness(self):
        """住所の完全性をチェック"""
        address_info = self.build_complete_address_info()
        
        required_fields = ["都道府県", "市区町村", "大字", "地番"]
        missing_fields = []
        
        for field in required_fields:
            if not address_info.get(field):
                missing_fields.append(field)
        
        return {
            "complete": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "completion_rate": (len(required_fields) - len(missing_fields)) / len(required_fields) * 100
        }
    
    def get_address_hierarchy(self):
        """住所の階層構造を取得"""
        address_info = self.build_complete_address_info()
        
        hierarchy = []
        
        # 都道府県レベル
        if address_info["都道府県"]:
            hierarchy.append({
                "level": "都道府県",
                "name": address_info["都道府県"],
                "code": self.get_prefecture_code()
            })
        
        # 市区町村レベル
        if address_info["市区町村"]:
            hierarchy.append({
                "level": "市区町村",
                "name": address_info["市区町村"],
                "code": self.get_city_code()
            })
        
        # 大字レベル
        if address_info["大字"]:
            hierarchy.append({
                "level": "大字",
                "name": address_info["大字"],
                "code": ""
            })
        
        # 丁目レベル
        if address_info["丁目"] and address_info["丁目"] != "なし":
            hierarchy.append({
                "level": "丁目",
                "name": address_info["丁目"],
                "code": ""
            })
        
        # 地番レベル
        if address_info["地番"]:
            hierarchy.append({
                "level": "地番",
                "name": address_info["地番"],
                "code": ""
            })
        
        return hierarchy