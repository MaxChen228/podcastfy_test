#!/usr/bin/env python3
"""
Step 2: 使用 Gemini Multi-Speaker TTS 生成音頻
從已生成的腳本創建多說話者音頻
"""

import os
import sys
import json
import wave
import yaml
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check API key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ 請設置 GEMINI_API_KEY 環境變數")
    sys.exit(1)

def load_config(config_path: str = "./podcast_config.yaml"):
    """載入配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_wave_file(filename: str, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
    """保存 WAV 音頻檔案"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)

def generate_audio_from_script(script_dir: str):
    """從腳本生成音頻"""
    
    print("=" * 60)
    print("🎵 Step 2: Gemini Multi-Speaker TTS 音頻生成")
    print("=" * 60)
    
    script_dir = Path(script_dir)
    
    # 讀取腳本
    script_file = script_dir / "podcast_script.txt"
    if not script_file.exists():
        print(f"❌ 找不到腳本檔案: {script_file}")
        return None
    
    with open(script_file, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # 讀取元數據
    metadata_file = script_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print(f"📝 腳本資訊:")
        print(f"   - 字數: {metadata.get('actual_words', 'N/A')} 字")
        print(f"   - 目標時長: {metadata.get('target_minutes', 'N/A')} 分鐘")
        print(f"   - 英語等級: {metadata.get('english_level', 'N/A')}")
    
    # 載入配置文件取得所有設定
    config = load_config()
    
    # 基本設定
    style_instructions = config['basic'].get('style_instructions', 'conversational, engaging')
    
    # 聲線設定
    host_voice = config['voices'].get('host_voice', 'Kore')
    expert_voice = config['voices'].get('expert_voice', 'Puck')
    
    # TTS 模型設定
    tts_model = config['advanced'].get('tts_model', 'gemini-2.5-flash-preview-tts')
    
    print(f"🎤 聲線配置:")
    print(f"   - 主持人 (Person1): {host_voice}")
    print(f"   - 專家 (Person2): {expert_voice}")
    print(f"   - TTS 模型: {tts_model}")
    print(f"   - 風格: {style_instructions}")
    print("-" * 60)
    
    # 準備 TTS 提示
    tts_prompt = f"""Say this conversation between Host and Expert with {style_instructions} tone:

{script_content}"""
    
    print("🚀 開始生成音頻...")
    print("⏳ 這可能需要幾分鐘，請耐心等待...")
    
    try:
        # 初始化 Gemini 客戶端
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 使用多說話者配置生成音頻（模型名稱從配置讀取）
        response = client.models.generate_content(
            model=tts_model,
            contents=tts_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker="Person1",  # 主持人
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=host_voice
                                    )
                                )
                            ),
                            types.SpeakerVoiceConfig(
                                speaker="Person2",  # 專家
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=expert_voice
                                    )
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        # 提取音頻數據
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        # 保存音頻檔案
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"./output/audio/audio_{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        audio_file = output_dir / "podcast.wav"
        save_wave_file(str(audio_file), audio_data)
        
        # 複製腳本到音頻目錄
        script_copy = output_dir / "script.txt"
        script_copy.write_text(script_content, encoding='utf-8')
        
        # 更新元數據
        if metadata_file.exists():
            metadata['audio_generated'] = timestamp
            metadata['audio_file'] = str(audio_file)
            metadata['audio_size_kb'] = len(audio_data) / 1024
            metadata['voices'] = {
                'host': host_voice,
                'expert': expert_voice
            }
            
            audio_metadata_file = output_dir / "metadata.json"
            audio_metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        
        print("\n" + "=" * 60)
        print("✅ 音頻生成成功！")
        print(f"📁 輸出目錄: {output_dir}")
        print(f"🎵 音頻檔案: {audio_file.name}")
        print(f"📏 檔案大小: {len(audio_data)/1024:.1f} KB")
        print(f"🎤 聲線: {host_voice} (主持人) + {expert_voice} (專家)")
        print("=" * 60)
        print("\n🎧 現在可以播放音頻檔案來聆聽播客了！")
        
        return str(output_dir)
        
    except Exception as e:
        print(f"❌ 音頻生成失敗: {e}")
        
        # 如果是 API 錯誤，提供更多資訊
        if "MultiSpeakerVoiceConfig" in str(e):
            print("\n⚠️ 可能的問題：")
            print("1. google-genai 版本太舊（需要 >= 1.31.0）")
            print("   檢查版本: pip show google-genai | grep Version")
            print("   升級: pip install --upgrade google-genai")
        
        return None


def generate_audio_from_latest():
    """從最新的腳本生成音頻"""
    # 查找最新的腳本目錄
    scripts_dir = Path("./output/scripts")
    if not scripts_dir.exists():
        print("❌ 找不到 scripts 目錄")
        return None
    
    script_dirs = sorted([d for d in scripts_dir.iterdir() if d.is_dir()], 
                        key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not script_dirs:
        print("❌ 沒有找到任何腳本")
        return None
    
    latest_script_dir = script_dirs[0]
    print(f"📂 使用最新腳本: {latest_script_dir}")
    
    return generate_audio_from_script(str(latest_script_dir))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 如果提供了腳本目錄路徑
        script_dir = sys.argv[1]
        generate_audio_from_script(script_dir)
    else:
        # 使用最新的腳本
        generate_audio_from_latest()