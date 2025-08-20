#!/usr/bin/env python3
"""
Gemini API 測試腳本 - 極簡版
快速測試 API Key 是否正常工作
"""

import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai


def test_api():
    """測試 Gemini API 連線"""
    # 載入環境變數
    load_dotenv()
    
    # 檢查 API Key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ 找不到 GEMINI_API_KEY")
        print("請檢查 .env 檔案")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    try:
        # 設定 API
        genai.configure(api_key=api_key)
        
        # 使用最穩定的模型測試
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 簡單測試
        print("🧪 測試 API 連線...")
        response = model.generate_content("回覆 OK")
        
        if response.text:
            print(f"✅ API 測試成功！")
            print(f"📝 回應: {response.text.strip()}")
            return True
        else:
            print("❌ API 回應為空")
            return False
            
    except Exception as e:
        print(f"❌ API 測試失敗: {e}")
        return False


if __name__ == "__main__":
    print("=" * 40)
    print("Gemini API 連線測試")
    print("=" * 40)
    
    success = test_api()
    
    print("=" * 40)
    if success:
        print("🎉 測試通過！API Key 正常運作")
    else:
        print("💥 測試失敗！請檢查 API Key")
        sys.exit(1)