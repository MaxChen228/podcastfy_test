#!/usr/bin/env python3
"""
Integrated Podcast Generator
整合工作流：Podcastfy 生成腳本 + Gemini Multi-Speaker TTS 生成音頻
支援多模態輸入（文檔、PDF、網頁、YouTube）
"""

import os
import sys
import wave
import json
import yaml
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from urllib.parse import urlparse

# Google Gemini imports
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ 需要安裝 google-genai 套件")
    print("請執行: pip install google-genai")
    sys.exit(1)

# Podcastfy imports
try:
    from podcastfy.client import generate_podcast
except ImportError:
    print("❌ 需要安裝 podcastfy 套件")
    print("請執行: pip install podcastfy")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check API keys
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ 請設置 GEMINI_API_KEY 環境變數")
    sys.exit(1)


@dataclass
class IntegratedPodcastConfig:
    """整合播客配置"""
    input_source: str  # 文件路徑、URL、YouTube 連結等
    input_type: str = "auto"  # 'text', 'pdf', 'url', 'youtube', 'auto'
    english_level: str = "B2"
    target_minutes: int = 1
    host_voice: str = "Kore"  # Gemini TTS 主持人語音
    expert_voice: str = "Puck"  # Gemini TTS 專家語音
    style_instructions: str = "conversational, engaging, educational"
    output_dir: str = "./integrated_output"
    use_podcastfy_tts: bool = False  # 是否使用 Podcastfy 的 TTS（否則用 Gemini）


class IntegratedPodcastGenerator:
    """整合式播客生成器"""
    
    def __init__(self):
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        self.supported_input_types = ['text', 'pdf', 'url', 'youtube']
    
    @classmethod
    def from_config_file(cls, config_path: str = "./podcast_config.yaml"):
        """從配置文件創建播客生成器"""
        return cls(), cls.load_config(config_path)
    
    @staticmethod
    def load_config(config_path: str = "./podcast_config.yaml") -> IntegratedPodcastConfig:
        """載入配置文件"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return IntegratedPodcastConfig(
            input_source=config_data['input']['source'],
            input_type=config_data['input']['type'],
            english_level=config_data['basic']['english_level'],
            target_minutes=config_data['basic']['target_minutes'],
            host_voice=config_data['voices']['host_voice'],
            expert_voice=config_data['voices']['expert_voice'],
            style_instructions=config_data['basic']['style_instructions'],
            output_dir=config_data['advanced']['output_dir'],
            use_podcastfy_tts=config_data['advanced']['use_podcastfy_tts']
        )
        
    def detect_input_type(self, input_source: str) -> str:
        """自動檢測輸入類型"""
        # 檢查是否為 URL
        if input_source.startswith(('http://', 'https://')):
            if 'youtube.com' in input_source or 'youtu.be' in input_source:
                return 'youtube'
            return 'url'
        
        # 檢查是否為檔案
        if Path(input_source).exists():
            suffix = Path(input_source).suffix.lower()
            if suffix == '.pdf':
                return 'pdf'
            elif suffix in ['.txt', '.md']:
                return 'text'
        
        # 預設為文本內容
        return 'text'
    
    def save_wave_file(self, filename: str, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
        """保存 WAV 音頻檔案"""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)
    
    def generate_script_with_podcastfy(self, config: IntegratedPodcastConfig) -> Dict[str, Any]:
        """使用 Podcastfy 生成對話腳本"""
        logger.info("📝 使用 Podcastfy 生成對話腳本...")
        
        # 自動檢測輸入類型
        if config.input_type == "auto":
            config.input_type = self.detect_input_type(config.input_source)
            logger.info(f"檢測到輸入類型: {config.input_type}")
        
        # 根據時長計算字數
        word_count = config.target_minutes * 150  # 約 150 字/分鐘
        
        # 準備 Podcastfy 配置
        conversation_config = {
            "word_count": word_count,
            "conversation_style": ["engaging", "educational"],
            "language": "English",
            "dialogue_structure": "two_speakers",
            "custom_instructions": f"""
                Create a podcast conversation for {config.english_level} English learners.
                Requirements:
                - Use appropriate vocabulary for {config.english_level} level
                - Length: approximately {word_count} words
                - Style: {config.style_instructions}
                - Format: Natural conversation between Host and Expert
                - Host asks questions and guides the conversation
                - Expert provides insights and explanations
            """,
            "roles": ["Host", "Expert"],
            "output_folder": config.output_dir
        }
        
        # 創建臨時輸出目錄
        temp_dir = Path(config.output_dir) / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        conversation_config["output_folder"] = str(temp_dir)
        
        try:
            # 根據輸入類型調用 Podcastfy
            if config.input_type == 'text':
                # 如果是檔案路徑，讀取內容
                if Path(config.input_source).exists():
                    with open(config.input_source, 'r', encoding='utf-8') as f:
                        content = f.read()
                else:
                    content = config.input_source
                
                result = generate_podcast(
                    text=content,
                    llm_model_name="gemini-2.5-flash",
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    transcript_only=not config.use_podcastfy_tts  # True = 只生成腳本，給 Gemini TTS 使用
                )
                
            elif config.input_type == 'pdf':
                result = generate_podcast(
                    pdf_file_path=config.input_source,
                    llm_model_name="gemini-2.5-pro",
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    tts_model="gemini" if not config.use_podcastfy_tts else "openai"
                )
                
            elif config.input_type == 'url':
                result = generate_podcast(
                    urls=[config.input_source],
                    llm_model_name="gemini-2.5-pro",
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    tts_model="gemini" if not config.use_podcastfy_tts else "openai"
                )
                
            elif config.input_type == 'youtube':
                result = generate_podcast(
                    youtube_urls=[config.input_source],
                    llm_model_name="gemini-2.5-pro",
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    tts_model="gemini" if not config.use_podcastfy_tts else "openai"
                )
            else:
                raise ValueError(f"不支援的輸入類型: {config.input_type}")
            
            # 尋找生成的腳本檔案（Podcastfy 保存在 ./data/transcripts/）
            data_transcript_dir = Path("./data/transcripts/")
            transcript_files = list(data_transcript_dir.glob("transcript*.txt"))
            if not transcript_files:
                # 備用：搜尋臨時目錄
                transcript_files = list(temp_dir.glob("**/transcript*.txt"))
                if not transcript_files:
                    transcript_files = list(temp_dir.glob("**/*.txt"))
            
            if transcript_files:
                transcript_file = transcript_files[0]
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    script = f.read()
                
                logger.info(f"✅ 腳本生成完成（{len(script.split())} words）")
                
                # 如果使用 Podcastfy 的 TTS，查找音頻檔案
                if config.use_podcastfy_tts:
                    data_audio_dir = Path("./data/audio/")
                    audio_files = list(data_audio_dir.glob("podcast*.mp3"))
                    if not audio_files:
                        audio_files = list(temp_dir.glob("**/*.mp3"))
                    
                    if audio_files:
                        return {
                            "status": "success",
                            "script": script,
                            "script_file": str(transcript_file),
                            "audio_file": str(audio_files[0]),
                            "used_podcastfy_tts": True
                        }
                
                return {
                    "status": "success",
                    "script": script,
                    "script_file": str(transcript_file)
                }
            else:
                raise Exception("未找到生成的腳本檔案")
                
        except Exception as e:
            logger.error(f"❌ 腳本生成失敗: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def generate_audio_from_script(self, script: str, config: IntegratedPodcastConfig) -> bytes:
        """使用 Gemini Multi-Speaker TTS 生成音頻"""
        logger.info("🎵 使用 Gemini Multi-Speaker TTS 生成音頻...")
        
        # 準備 TTS 提示
        tts_prompt = f"""Say this conversation between Host and Expert with {config.style_instructions} tone:

{script}"""
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=tts_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=config.host_voice,
                            )
                        )
                    )
                )
            )
            
            # 提取音頻數據
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            logger.info(f"✅ 音頻生成完成（{len(audio_data)/1024:.1f} KB）")
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ 音頻生成失敗: {e}")
            raise
    
    def generate(self, config: IntegratedPodcastConfig) -> Dict[str, Any]:
        """完整的整合生成流程"""
        print("\n" + "=" * 60)
        print("🚀 整合式播客生成")
        print(f"📥 輸入來源: {config.input_source}")
        print(f"🎯 英語等級: {config.english_level}")
        print(f"⏱️ 目標長度: {config.target_minutes} 分鐘")
        print("=" * 60)
        
        # 創建輸出目錄
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = output_dir / f"podcast_{config.english_level}_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: 使用 Podcastfy 生成腳本
            print("\n📝 Step 1: 生成對話腳本...")
            script_result = self.generate_script_with_podcastfy(config)
            
            if script_result["status"] != "success":
                raise Exception(f"腳本生成失敗: {script_result.get('error', 'Unknown error')}")
            
            script = script_result["script"]
            
            # 保存腳本
            script_file = session_dir / "script.txt"
            script_file.write_text(script, encoding='utf-8')
            print(f"💾 腳本已保存: {script_file}")
            
            # 如果已經使用 Podcastfy TTS，直接返回
            if script_result.get("used_podcastfy_tts"):
                print("✅ 使用 Podcastfy TTS 完成")
                return {
                    "status": "success",
                    "output_dir": str(session_dir),
                    "script_file": str(script_file),
                    "audio_file": script_result["audio_file"],
                    "tts_provider": "podcastfy"
                }
            
            # Step 2: 使用 Gemini TTS 生成音頻
            print("\n🎵 Step 2: 生成音頻...")
            audio_data = self.generate_audio_from_script(script, config)
            
            # 保存音頻
            audio_file = session_dir / "podcast.wav"
            self.save_wave_file(str(audio_file), audio_data)
            print(f"💾 音頻已保存: {audio_file}")
            
            # 保存元數據
            metadata = {
                "timestamp": timestamp,
                "input_source": config.input_source,
                "input_type": config.input_type,
                "english_level": config.english_level,
                "target_minutes": config.target_minutes,
                "host_voice": config.host_voice,
                "expert_voice": config.expert_voice,
                "script_words": len(script.split()),
                "audio_size_kb": len(audio_data) / 1024,
                "tts_provider": "gemini",
                "files": {
                    "script": str(script_file),
                    "audio": str(audio_file)
                }
            }
            
            metadata_file = session_dir / "metadata.json"
            metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
            
            print("\n" + "=" * 60)
            print("✅ 播客生成成功！")
            print(f"📁 輸出目錄: {session_dir}")
            print(f"🎵 音頻檔案: {audio_file.name} ({len(audio_data)/1024:.1f} KB)")
            print(f"📝 腳本檔案: {script_file.name} ({len(script.split())} words)")
            print("=" * 60)
            
            return {
                "status": "success",
                "output_dir": str(session_dir),
                "audio_file": str(audio_file),
                "script_file": str(script_file),
                "metadata": metadata
            }
            
        except Exception as e:
            print(f"\n❌ 播客生成失敗: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


def generate_from_config(config_path: str = "./podcast_config.yaml"):
    """從配置文件生成播客"""
    try:
        generator, config = IntegratedPodcastGenerator.from_config_file(config_path)
        return generator.generate(config)
    except Exception as e:
        print(f"❌ 配置載入失敗: {e}")
        return {"status": "error", "error": str(e)}


def test_multimodal_inputs():
    """測試不同類型的輸入"""
    generator = IntegratedPodcastGenerator()
    
    # 測試案例
    test_cases = [
        {
            "name": "從配置文件生成播客",
            "use_config": True
        },
        {
            "name": "文本檔案測試（Podcastfy 腳本 + Gemini Multi-Speaker TTS）",
            "config": IntegratedPodcastConfig(
                input_source="./sample_article.txt",
                english_level="B2",
                target_minutes=1,
                style_instructions="educational and clear",
                use_podcastfy_tts=False  # Podcastfy 只做腳本，Gemini Multi-Speaker TTS 做音頻
            )
        },
        # 可以加入更多測試案例：
        # PDF: input_source="./document.pdf"
        # 網頁: input_source="https://example.com/article"
        # YouTube: input_source="https://youtube.com/watch?v=..."
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 {test_case['name']}")
        print("-" * 40)
        
        if test_case.get('use_config'):
            # 使用配置文件
            result = generate_from_config()
        else:
            # 檢查輸入檔案是否存在
            if test_case['config'].input_source.startswith('./'):
                if not Path(test_case['config'].input_source).exists():
                    # 創建測試檔案
                    test_content = """
                    The Impact of Artificial Intelligence on Education
                    
                    Artificial Intelligence is revolutionizing education in unprecedented ways. 
                    From personalized learning paths to intelligent tutoring systems, AI helps 
                    students learn at their own pace. Teachers can use AI tools to identify 
                    learning gaps and provide targeted support. The technology also enables 
                    accessible education for students with disabilities, breaking down 
                    traditional barriers to learning.
                    
                    AI-powered adaptive learning platforms adjust difficulty levels based on 
                    student performance, ensuring optimal challenge and engagement. Virtual 
                    teaching assistants can answer questions 24/7, providing instant support. 
                    Automated grading systems free up teachers' time for more meaningful 
                    interactions with students.
                    """
                    
                    Path(test_case['config'].input_source).write_text(test_content)
                    print(f"創建測試檔案: {test_case['config'].input_source}")
            
            result = generator.generate(test_case['config'])
        
        if result["status"] == "success":
            print(f"✅ 測試成功")
        else:
            print(f"❌ 測試失敗: {result.get('error')}")
    
    return True


if __name__ == "__main__":
    print("🎯 整合式播客生成器")
    print("支援輸入格式：文本檔案、PDF、網頁、YouTube")
    print("=" * 60)
    
    # 執行測試
    success = test_multimodal_inputs()
    
    if success:
        print("\n🎉 測試完成！")
        print("\n使用方式：")
        print("1. 準備任何格式的內容（文本、PDF、網頁、YouTube）")
        print("2. 設定英語難度等級（A1-C2）")
        print("3. Podcastfy 自動生成對話腳本")
        print("4. Gemini Multi-Speaker TTS 生成高品質音頻")
    
    sys.exit(0 if success else 1)