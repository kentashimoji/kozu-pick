#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
都道府県・市区町村選択ツール v4.0
GitHub ExcelファイルからデータをダウンロードしてGUIアプリケーションを作成

必要なライブラリ:
pip install pandas openpyxl requests tkinter pillow

作成者: AI Assistant
バージョン: 4.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import pandas as pd
import requests
from io import BytesIO
import json
import webbrowser
from datetime import datetime
import os
import sys

class PrefectureCitySelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏛️ 都道府県・市区町村選択ツール v4.0")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        
        # アプリケーションアイコンを設定（可能な場合）
        try:
            self.root.iconbitmap('favicon.ico')
        except:
            pass
        
        self.prefecture_data = {}
        self.current_url = ""
        self.data_loaded = False
        
        # スタイル設定
        self.setup_styles()
        self.setup_ui()
        
        # 初期URL設定
        default_url = "https://raw.githubusercontent.com/USERNAME/REPOSITORY/main/000925835.xlsx"
        self.url_var.set(default_url)
        
    def setup_styles(self):
        """UIスタイルを設定"""
        style = ttk.Style()
        
        # テーマを設定
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        # カスタムスタイル
        style.configure('Title.TLabel', font=('', 16, 'bold'))
        style.configure('Header.TLabel', font=('', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green', font=('', 10, 'bold'))
        style.configure('Error.TLabel', foreground='red', font=('', 10, 'bold'))
        style.configure('Info.TLabel', foreground='blue', font=('', 10))
        
    def setup_ui(self):
        """UIを構築"""
        # メインフレームを作成
        self.setup_main_frame()
        
        # ノートブック（タブ）を作成
        self.setup_notebook()
        
        # 各タブを設定
        self.setup_main_tab()
        self.setup_data_tab()
        self.setup_about_tab()
        
        # ステータスバー
        self.setup_status_bar()
        
        # ウィンドウリサイズ対応
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def setup_main_frame(self):
        """メインフレームを設定"""
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
    def setup_notebook(self):
        """ノートブック（タブ）を設定"""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # タブフレームを作成
        self.main_tab = ttk.Frame(self.notebook, padding="15")
        self.data_tab = ttk.Frame(self.notebook, padding="15")
        self.about_tab = ttk.Frame(self.notebook, padding="15")
        
        # タブを追加
        self.notebook.add(self.main_tab, text="🏛️ メイン")
        self.notebook.add(self.data_tab, text="📊 データ管理")
        self.notebook.add(self.about_tab, text="ℹ️ 情報")
        
    def setup_main_tab(self):
        """メインタブを設定"""
        # タイトル
        title_label = ttk.Label(self.main_tab, text="都道府県・市区町村選択ツール", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # バージョン表示
        version_label = ttk.Label(self.main_tab, text="Version 4.0", 
                                 style='Info.TLabel')
        version_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # GitHub URL入力セクション
        url_frame = ttk.LabelFrame(self.main_tab, text="📡 データソース設定", padding="10")
        url_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        url_frame.columnconfigure(0, weight=1)
        
        ttk.Label(url_frame, text="GitHub ExcelファイルURL:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Consolas', 9))
        self.url_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        button_frame = ttk.Frame(url_frame)
        button_frame.grid(row=2, column=0, sticky=tk.W)
        
        self.load_button = ttk.Button(button_frame, text="🔄 データを読み込み", 
                                     command=self.load_data)
        self.load_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="🗑️ クリア", 
                                      command=self.clear_data)
        self.clear_button.pack(side=tk.LEFT)
        
        # 選択セクション
        selection_frame = ttk.LabelFrame(self.main_tab, text="🎯 地域選択", padding="10")
        selection_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        selection_frame.columnconfigure(0, weight=1)
        
        # 都道府県選択
        ttk.Label(selection_frame, text="都道府県:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.prefecture_var = tk.StringVar()
        self.prefecture_combo = ttk.Combobox(selection_frame, textvariable=self.prefecture_var, 
                                           state="disabled", width=50)
        self.prefecture_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.prefecture_combo.bind("<<ComboboxSelected>>", self.on_prefecture_selected)
        
        # 市区町村選択
        ttk.Label(selection_frame, text="市区町村:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(selection_frame, textvariable=self.city_var, 
                                     state="disabled", width=50)
        self.city_combo.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.city_combo.bind("<<ComboboxSelected>>", self.on_city_selected)
        
        # 結果表示
        result_frame = ttk.LabelFrame(self.main_tab, text="📍 選択結果", padding="10")
        result_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        result_frame.columnconfigure(0, weight=1)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=6, width=60, 
                                                   wrap=tk.WORD, state=tk.DISABLED)
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ボタンセクション
        action_frame = ttk.Frame(self.main_tab)
        action_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(action_frame, text="📋 結果をコピー", 
                  command=self.copy_result).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="🔄 リセット", 
                  command=self.reset_selection).pack(side=tk.LEFT)
        
        # グリッド設定
        self.main_tab.columnconfigure(0, weight=1)
        
    def setup_data_tab(self):
        """データ管理タブを設定"""
        # データ情報表示
        info_frame = ttk.LabelFrame(self.data_tab, text="📊 データ情報", padding="10")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        info_frame.columnconfigure(1, weight=1)
        
        self.data_info_text = scrolledtext.ScrolledText(info_frame, height=10, width=70, 
                                                       wrap=tk.WORD, state=tk.DISABLED)
        self.data_info_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # データ操作ボタン
        button_frame = ttk.Frame(self.data_tab)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="💾 JSONで保存", 
                  command=self.save_json).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="📄 CSVで保存", 
                  command=self.save_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="📋 データをコピー", 
                  command=self.copy_data_info).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🔄 情報を更新", 
                  command=self.update_data_info).pack(side=tk.LEFT)
        
        # グリッド設定
        self.data_tab.columnconfigure(0, weight=1)
        self.data_tab.rowconfigure(0, weight=1)
        
    def setup_about_tab(self):
        """情報タブを設定"""
        about_text = """
🏛️ 都道府県・市区町村選択ツール v4.0

【概要】
GitHubにアップロードされたExcelファイルから日本の都道府県・市区町村データを
読み込み、階層的な選択を可能にするGUIアプリケーションです。

【主な機能】
✅ GitHub上のExcelファイルの直接読み込み
✅ 都道府県選択による市区町村の絞り込み
✅ データのJSON/CSV形式での保存
✅ 選択結果のクリップボードコピー
✅ データ統計情報の表示
✅ 使いやすいタブインターフェース

【必要なライブラリ】
• pandas
• openpyxl  
• requests
• tkinter (標準ライブラリ)

【インストール方法】
pip install pandas openpyxl requests

【使用方法】
1. GitHubのExcelファイルのRaw URLを入力
2. 「データを読み込み」ボタンをクリック
3. 都道府県を選択
4. 市区町村を選択
5. 必要に応じてデータを保存

【対応ファイル形式】
• Excel (.xlsx, .xls)
• CSVファイル (UTF-8)

【GitHub Raw URLの取得方法】
1. GitHubでファイルを開く
2. 「Raw」ボタンをクリック
3. ブラウザのアドレスバーからURLをコピー

【注意事項】
• インターネット接続が必要です
• プライベートリポジトリの場合は適切なアクセス権限が必要です
• ファイルサイズが大きい場合は読み込みに時間がかかります

【更新履歴】
v4.0: タブインターフェース、データ管理機能、統計情報表示を追加
v3.0: GitHub対応、エラーハンドリング強化
v2.0: GUI改善、保存機能追加
v1.0: 初期バージョン

作成: AI Assistant
ライセンス: MIT
        """
        
        about_scrolled = scrolledtext.ScrolledText(self.about_tab, wrap=tk.WORD, 
                                                  state=tk.DISABLED, font=('', 10))
        about_scrolled.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # テキストを挿入
        about_scrolled.config(state=tk.NORMAL)
        about_scrolled.insert(tk.END, about_text)
        about_scrolled.config(state=tk.DISABLED)
        
        # ボタンフレーム
        about_button_frame = ttk.Frame(self.about_tab)
        about_button_frame.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(about_button_frame, text="🌐 GitHub", 
                  command=lambda: webbrowser.open("https://github.com")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(about_button_frame, text="📧 フィードバック", 
                  command=self.show_feedback_dialog).pack(side=tk.LEFT)
        
        # グリッド設定
        self.about_tab.columnconfigure(0, weight=1)
        self.about_tab.rowconfigure(0, weight=1)
        
    def setup_status_bar(self):
        """ステータスバーを設定"""
        self.status_bar = ttk.Frame(self.main_frame)
        self.status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.status_label = ttk.Label(self.status_bar, text="準備完了", 
                                     style='Info.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        # 右側に現在時刻を表示
        self.time_label = ttk.Label(self.status_bar, text="", 
                                   style='Info.TLabel')
        self.time_label.pack(side=tk.RIGHT)
        
        # 時刻更新
        self.update_time()
        
    def update_time(self):
        """現在時刻を更新"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)  # 1秒後に再実行
        
    def update_status(self, message, is_error=False):
        """ステータスメッセージを更新"""
        if is_error:
            self.status_label.config(text=f"❌ {message}", style='Error.TLabel')
        else:
            self.status_label.config(text=f"✅ {message}", style='Success.TLabel')
        
        # 3秒後に元に戻す
        self.root.after(3000, lambda: self.status_label.config(text="待機中", style='Info.TLabel'))
        
    def load_data(self):
        """データを読み込み"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("エラー", "URLを入力してください")
            return
            
        if "raw.githubusercontent.com" not in url:
            response = messagebox.askyesno("確認", 
                "GitHub Raw URLではないようです。続行しますか？\n"
                "正しいURLは 'raw.githubusercontent.com' を含んでいます。")
            if not response:
                return
                
        try:
            self.load_button.config(text="読み込み中...", state="disabled")
            self.update_status("データを読み込んでいます...")
            self.root.update()
            
            # GitHubからファイルをダウンロード
            headers = {'User-Agent': 'PrefectureCitySelector/4.0'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # ファイル形式を判定
            if url.lower().endswith('.csv'):
                # CSVファイルの場合
                df = pd.read_csv(BytesIO(response.content), encoding='utf-8-sig')
            else:
                # Excelファイルの場合
                excel_data = BytesIO(response.content)
                df = pd.read_excel(excel_data)
            
            # データを整理
            self.prefecture_data = {}
            prefecture_cols = [col for col in df.columns if '都道府県' in col and '漢字' in col]
            city_cols = [col for col in df.columns if '市区町村' in col and '漢字' in col]
            
            if not prefecture_cols or not city_cols:
                # 列名が見つからない場合の代替処理
                available_cols = list(df.columns)
                messagebox.showinfo("列情報", f"利用可能な列: {available_cols}")
                return
            
            prefecture_col = prefecture_cols[0]
            city_col = city_cols[0]
            
            for _, row in df.iterrows():
                prefecture = row.get(prefecture_col)
                city = row.get(city_col)
                
                if pd.notna(prefecture):
                    if prefecture not in self.prefecture_data:
                        self.prefecture_data[prefecture] = set()
                    
                    if pd.notna(city):
                        self.prefecture_data[prefecture].add(city)
            
            # SetをListに変換してソート
            for prefecture in self.prefecture_data:
                self.prefecture_data[prefecture] = sorted(list(self.prefecture_data[prefecture]))
            
            # プルダウンを更新
            self.update_prefecture_combo()
            self.update_data_info()
            
            self.current_url = url
            self.data_loaded = True
            
            self.load_button.config(text="🔄 データを読み込み", state="normal")
            
            total_prefectures = len(self.prefecture_data)
            total_cities = sum(len(cities) for cities in self.prefecture_data.values())
            
            messagebox.showinfo("成功", 
                f"データの読み込みが完了しました！\n\n"
                f"📊 統計情報:\n"
                f"• 都道府県数: {total_prefectures}\n"
                f"• 総市区町村数: {total_cities}\n"
                f"• データソース: {url[:50]}...")
            
            self.update_status(f"データ読み込み完了 ({total_prefectures}都道府県, {total_cities}市区町村)")
            
        except requests.RequestException as e:
            self.load_button.config(text="🔄 データを読み込み", state="normal")
            error_msg = f"ネットワークエラー: {str(e)}"
            messagebox.showerror("エラー", error_msg)
            self.update_status("読み込み失敗", is_error=True)
            
        except Exception as e:
            self.load_button.config(text="🔄 データを読み込み", state="normal")
            error_msg = f"データの読み込みに失敗しました: {str(e)}"
            messagebox.showerror("エラー", error_msg)
            self.update_status("読み込み失敗", is_error=True)
    
    def clear_data(self):
        """データをクリア"""
        if messagebox.askyesno("確認", "読み込まれたデータをクリアしますか？"):
            self.prefecture_data = {}
            self.data_loaded = False
            self.prefecture_combo['values'] = []
            self.prefecture_combo['state'] = 'disabled'
            self.city_combo['values'] = []
            self.city_combo['state'] = 'disabled'
            self.prefecture_var.set('')
            self.city_var.set('')
            
            # 結果テキストをクリア
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.config(state=tk.DISABLED)
            
            # データ情報をクリア
            self.data_info_text.config(state=tk.NORMAL)
            self.data_info_text.delete(1.0, tk.END)
            self.data_info_text.config(state=tk.DISABLED)
            
            self.update_status("データをクリアしました")
    
    def update_prefecture_combo(self):
        """都道府県コンボボックスを更新"""
        if not self.prefecture_data:
            return
            
        prefectures = sorted(self.prefecture_data.keys())
        prefecture_list = [f"{p} ({len(self.prefecture_data[p])}市区町村)" for p in prefectures]
        self.prefecture_combo['values'] = prefecture_list
        self.prefecture_combo['state'] = 'readonly'
        
    def on_prefecture_selected(self, event):
        """都道府県選択時の処理"""
        selected = self.prefecture_var.get()
        if not selected:
            return
            
        # 都道府県名を抽出
        prefecture_name = selected.split(' (')[0]
        
        # 市区町村プルダウンを更新
        cities = self.prefecture_data.get(prefecture_name, [])
        self.city_combo['values'] = cities
        self.city_combo['state'] = 'readonly'
        self.city_var.set('')  # 選択をリセット
        
        # 結果をクリア
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        self.update_status(f"{prefecture_name}を選択 ({len(cities)}市区町村)")
        
    def on_city_selected(self, event):
        """市区町村選択時の処理"""
        prefecture = self.prefecture_var.get().split(' (')[0] if self.prefecture_var.get() else ''
        city = self.city_var.get()
        
        if prefecture and city:
            result_text = f"📍 選択された地域情報\n\n"
            result_text += f"都道府県: {prefecture}\n"
            result_text += f"市区町村: {city}\n"
            result_text += f"完全な住所: {prefecture}{city}\n\n"
            result_text += f"選択日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n"
            result_text += f"データソース: {self.current_url[:60]}...\n" if self.current_url else ""
            
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)
            self.result_text.config(state=tk.DISABLED)
            
            self.update_status(f"選択完了: {prefecture}{city}")
    
    def copy_result(self):
        """結果をクリップボードにコピー"""
        content = self.result_text.get(1.0, tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.update_status("結果をコピーしました")
        else:
            messagebox.showwarning("警告", "コピーする結果がありません")
    
    def reset_selection(self):
        """選択をリセット"""
        self.prefecture_var.set('')
        self.city_var.set('')
        self.city_combo['values'] = []
        self.city_combo['state'] = 'disabled'
        
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        self.update_status("選択をリセットしました")
    
    def update_data_info(self):
        """データ情報を更新"""
        if not self.prefecture_data:
            info_text = "データが読み込まれていません。\n\n"
            info_text += "メインタブでGitHubのExcelファイルURLを入力し、\n"
            info_text += "「データを読み込み」ボタンをクリックしてください。"
        else:
            info_text = "📊 データ統計情報\n"
            info_text += "=" * 50 + "\n\n"
            
            total_cities = sum(len(cities) for cities in self.prefecture_data.values())
            info_text += f"総都道府県数: {len(self.prefecture_data)}\n"
            info_text += f"総市区町村数: {total_cities}\n"
            info_text += f"平均市区町村数/都道府県: {total_cities/len(self.prefecture_data):.1f}\n\n"
            
            info_text += "都道府県別市区町村数:\n"
            info_text += "-" * 30 + "\n"
            
            # 市区町村数でソート
            sorted_prefectures = sorted(self.prefecture_data.items(), 
                                      key=lambda x: len(x[1]), reverse=True)
            
            for i, (prefecture, cities) in enumerate(sorted_prefectures, 1):
                info_text += f"{i:2d}. {prefecture:<8} : {len(cities):3d}市区町村\n"
            
            info_text += f"\n最新更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            info_text += f"データソース: {self.current_url}\n" if self.current_url else ""
        
        self.data_info_text.config(state=tk.NORMAL)
        self.data_info_text.delete(1.0, tk.END)
        self.data_info_text.insert(tk.END, info_text)
        self.data_info_text.config(state=tk.DISABLED)
    
    def copy_data_info(self):
        """データ情報をコピー"""
        content = self.data_info_text.get(1.0, tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.update_status("データ情報をコピーしました")
        else:
            messagebox.showwarning("警告", "コピーするデータがありません")
    
    def save_json(self):
        """JSONファイルとして保存"""
        if not self.prefecture_data:
            messagebox.showwarning("警告", "保存するデータがありません")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="JSONファイルとして保存",
            initialname=f"prefecture_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            try:
                # メタデータを追加
                save_data = {
                    "metadata": {
                        "version": "4.0",
                        "created_at": datetime.now().isoformat(),
                        "source_url": self.current_url,
                        "total_prefectures": len(self.prefecture_data),
                        "total_cities": sum(len(cities) for cities in self.prefecture_data.values())
                    },
                    "data": self.prefecture_data
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"JSONファイルを保存しました:\n{filename}")
                self.update_status("JSONファイル保存完了")
                
            except Exception as e:
                messagebox.showerror("エラー", f"保存に失敗しました: {str(e)}")
                self.update_status("保存失敗", is_error=True)
    
    def save_csv(self):
        """CSVファイルとして保存"""
        if not self.prefecture_data:
            messagebox.showwarning("警告", "保存するデータがありません")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="CSVファイルとして保存",
            initialname=f"prefecture_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            try:
                rows = []
                for prefecture, cities in self.prefecture_data.items():
                    for city in cities:
                        rows.append([prefecture, city, f"{prefecture}{city}"])
                
                df = pd.DataFrame(rows, columns=['都道府県', '市区町村', '完全住所'])
                
                # メタデータをコメントとして追加
                with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                    f.write(f"# 都道府県・市区町村データ v4.0\n")
                    f.write(f"# 作成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# データソース: {self.current_url}\n")
                    f.write(f"# 都道府県数: {len(self.prefecture_data)}\n")
                    f.write(f"# 市区町村数: {len(rows)}\n")
                    f.write("#\n")
                    
                    # CSVデータを書き込み
                    df.to_csv(f, index=False, lineterminator='\n')
                
                messagebox.showinfo("成功", f"CSVファイルを保存しました:\n{filename}")
                self.update_status("CSVファイル保存完了")
                
            except Exception as e:
                messagebox.showerror("エラー", f"保存に失敗しました: {str(e)}")
                self.update_status("保存失敗", is_error=True)
    
    def show_feedback_dialog(self):
        """フィードバックダイアログを表示"""
        feedback_window = tk.Toplevel(self.root)
        feedback_window.title("📧 フィードバック")
        feedback_window.geometry("500x400")
        feedback_window.resizable(False, False)
        
        # ウィンドウを中央に配置
        feedback_window.transient(self.root)
        feedback_window.grab_set()
        
        main_frame = ttk.Frame(feedback_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="フィードバック・要望", 
                 font=('', 12, 'bold')).pack(pady=(0, 10))
        
        feedback_text = """
このアプリケーションについてのご意見・ご要望をお聞かせください。

【改善提案の例】
• 新機能の追加要望
• UIの改善案  
• バグ報告
• データ形式の対応要望
• その他の改善提案

【連絡先】
• GitHub Issues
• メール
• その他のフィードバック方法

皆様からのフィードバックは、今後の開発に大変参考になります。
ありがとうございます！
        """
        
        text_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        text_widget.insert(tk.END, feedback_text)
        text_widget.config(state=tk.DISABLED)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="GitHub Issues", 
                  command=lambda: webbrowser.open("https://github.com")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="閉じる", 
                  command=feedback_window.destroy).pack(side=tk.RIGHT)
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        if messagebox.askokcancel("終了確認", "アプリケーションを終了しますか？"):
            try:
                # 設定を保存（オプション）
                if self.current_url:
                    config = {
                        "last_url": self.current_url,
                        "window_geometry": self.root.geometry(),
                        "last_used": datetime.now().isoformat()
                    }
                    
                    config_file = "prefecture_selector_config.json"
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)
                        
            except Exception as e:
                print(f"設定保存エラー: {e}")
                
            self.root.destroy()
    
    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            config_file = "prefecture_selector_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 前回のURLを復元
                if 'last_url' in config:
                    self.url_var.set(config['last_url'])
                    
                # ウィンドウサイズを復元
                if 'window_geometry' in config:
                    self.root.geometry(config['window_geometry'])
                    
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
    
    def run(self):
        """アプリケーションを実行"""
        # 設定を読み込み
        self.load_config()
        
        # 終了時の処理を設定
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # キーボードショートカットを設定
        self.root.bind('<Control-l>', lambda e: self.load_data())
        self.root.bind('<Control-s>', lambda e: self.save_json())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F5>', lambda e: self.load_data())
        
        # ウィンドウを中央に配置
        self.center_window()
        
        # メインループを開始
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nアプリケーションが中断されました")
        except Exception as e:
            print(f"予期しないエラー: {e}")
            messagebox.showerror("エラー", f"予期しないエラーが発生しました: {str(e)}")
    
    def center_window(self):
        """ウィンドウを画面中央に配置"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

def main():
    """メイン関数"""
    print("🏛️ 都道府県・市区町村選択ツール v4.0")
    print("=" * 50)
    print("アプリケーションを起動しています...")
    
    try:
        # 必要なライブラリの確認
        required_modules = ['pandas', 'requests', 'openpyxl']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"\n❌ 不足しているライブラリ: {', '.join(missing_modules)}")
            print("以下のコマンドでインストールしてください:")
            print(f"pip install {' '.join(missing_modules)}")
            return
        
        # アプリケーションを作成・実行
        app = PrefectureCitySelector()
        print("✅ アプリケーションが正常に起動しました")
        print("\n【キーボードショートカット】")
        print("Ctrl+L: データ読み込み")
        print("Ctrl+S: JSONで保存")
        print("Ctrl+Q: 終了")
        print("F5: データ再読み込み")
        print("\nGUIウィンドウをご確認ください...")
        
        app.run()
        
    except ImportError as e:
        print(f"❌ モジュールのインポートエラー: {e}")
        print("必要なライブラリをインストールしてください:")
        print("pip install pandas openpyxl requests")
    
    except Exception as e:
        print(f"❌ アプリケーション起動エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nアプリケーションを終了しました。")
        print("ご利用ありがとうございました！")

if __name__ == "__main__":
    main()