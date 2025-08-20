#!/usr/bin/env python3
"""
Gemini API 測試腳本 - 極簡版
快速測試 API Key 是否正常工作
"""

import os
import sys
import wave
from dotenv import load_dotenv
import google.generativeai as genai
from google import genai as new_genai
from google.genai import types


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


def test_tts():
    """測試 Gemini TTS 功能"""
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ 找不到 GEMINI_API_KEY")
        return False
    
    try:
        print("🎤 測試 TTS 功能...")
        
        # 初始化客戶端
        client = new_genai.Client(api_key=api_key)
        
        # 簡單的測試文本
        test_text = "Hello, this is a TTS test."
        
        # 生成音頻（使用單一說話者）
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=test_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Kore"
                        )
                    )
                )
            )
        )
        
        # 提取音頻數據
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        # 保存測試音頻
        with wave.open("test_tts.wav", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)
        
        print(f"✅ TTS 測試成功！")
        print(f"🎵 音頻已保存: test_tts.wav ({len(audio_data)/1024:.1f} KB)")
        return True
        
    except Exception as e:
        print(f"❌ TTS 測試失敗: {e}")
        if "MultiSpeakerVoiceConfig" in str(e):
            print("💡 提示: 請確認 google-genai >= 1.31.0")
        return False


if __name__ == "__main__":
    print("=" * 40)
    print("Gemini API & TTS 測試")
    print("=" * 40)
    
    # 測試基本 API
    api_success = test_api()
    
    if api_success:
        print("\n" + "=" * 40)
        # 測試 TTS
        tts_success = test_tts()
        print("=" * 40)
        
        if tts_success:
            print("🎉 所有測試通過！")
        else:
            print("⚠️ API 正常但 TTS 失敗")
            sys.exit(1)
    else:
        print("=" * 40)
        print("💥 基本 API 測試失敗！")
        sys.exit(1)