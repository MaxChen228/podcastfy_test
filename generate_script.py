#!/usr/bin/env python3
"""
Step 1: 使用 Podcastfy 生成播客腳本
只生成腳本，不做 TTS
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from podcastfy.client import generate_podcast
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config(config_path: str = "./podcast_config.yaml"):
    """載入配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_script_only(config_path: str = "./podcast_config.yaml"):
    """只生成腳本，不生成音頻"""
    
    print("=" * 60)
    print("📝 Step 1: Podcastfy 腳本生成")
    print("=" * 60)
    
    # 載入配置
    config = load_config(config_path)
    
    # 提取配置
    input_source = config['input']['source']
    input_type = config['input']['type']
    english_level = config['basic']['english_level']
    podcast_length = config['basic']['podcast_length']
    style_instructions = config['basic']['style_instructions']
    llm_model = config['advanced']['llm_model']
    
    print(f"📥 輸入來源: {input_source}")
    print(f"🎯 英語等級: {english_level}")
    print(f"📏 播客長度: {podcast_length}")
    print(f"🤖 LLM 模型: {llm_model}")
    print("-" * 60)
    
    # 檢查是否有手動覆蓋的長度控制參數
    if 'word_count' in config['advanced'] and config['advanced']['word_count']:
        # 使用手動配置的參數
        word_count = config['advanced']['word_count']
        max_num_chunks = config['advanced'].get('max_num_chunks', 6)
        min_chunk_size = config['advanced'].get('min_chunk_size', 600)
        print("📌 使用手動配置的長度控制參數")
    else:
        # 四種播客長度模式配置
        podcast_modes = {
            "short": {
                "word_count": 950,
                "max_num_chunks": 5,
                "min_chunk_size": 650,
                "time_range": "3-5 分鐘",
                "prompt_strategy": """CONCISE and FOCUSED approach:
                - Brief introduction (15-20 seconds)
                - Cover 3-4 key points with clear explanations
                - Use one vivid example or case study
                - Keep dialogue snappy and engaging
                - End with clear takeaways
                Think: "TED-Ed style" - educational, focused, memorable"""
            },
            "medium": {
                "word_count": 2000,
                "max_num_chunks": 8,
                "min_chunk_size": 700,
                "time_range": "6-10 分鐘",
                "prompt_strategy": """BALANCED and THOROUGH approach:
                - Proper introduction with context (30 seconds)
                - Develop 4-5 main points with supporting examples
                - Include 2-3 interesting anecdotes or case studies
                - Natural conversational flow with some depth
                - Address common questions or misconceptions
                - Conclude with actionable insights and summary
                Think: "Podcast episode" - comprehensive yet accessible"""
            },
            "long": {
                "word_count": 3300,
                "max_num_chunks": 12,
                "min_chunk_size": 800,
                "time_range": "11-15 分鐘",
                "prompt_strategy": """IN-DEPTH and ANALYTICAL approach:
                - Comprehensive introduction with full background
                - Explore topic from multiple perspectives
                - Include detailed examples, data, and evidence
                - Address counterarguments and edge cases
                - Build complex arguments with logical progression
                - Allow for nuanced discussion and reflection
                - Thorough conclusion with future implications
                Think: "Documentary deep-dive" - rigorous, multi-faceted, insightful"""
            },
            "extra-long": {
                "word_count": 7500,
                "max_num_chunks": 20,
                "min_chunk_size": 1000,
                "time_range": "16-45 分鐘",
                "prompt_strategy": """COMPREHENSIVE DOCUMENTARY approach:
                - Extended introduction with historical context
                - Systematic exploration of all major aspects
                - Multiple detailed case studies and real-world applications
                - Expert perspectives and diverse viewpoints
                - Deep analysis of implications and consequences
                - Address complexities, paradoxes, and open questions
                - Thoughtful pacing with natural topic transitions
                - Comprehensive wrap-up with call-to-action
                Think: "Full podcast episode" - exhaustive, authoritative, thought-provoking"""
            }
        }
        
        # 使用選擇的模式
        if podcast_length not in podcast_modes:
            print(f"⚠️ 未知的長度模式 '{podcast_length}'，使用預設 'medium'")
            podcast_length = "medium"
        
        mode = podcast_modes[podcast_length]
        word_count = mode["word_count"]
        max_num_chunks = mode["max_num_chunks"]
        min_chunk_size = mode["min_chunk_size"]
        prompt_strategy = mode["prompt_strategy"]
        
        print(f"📌 使用 '{podcast_length}' 模式（{mode['time_range']}）")
    
    # 從配置文件讀取進階設定
    conversation_style = config['advanced'].get('conversation_style', ["engaging", "educational"])
    language = config['advanced'].get('language', "English")
    dialogue_structure = config['advanced'].get('dialogue_structure', "two_speakers")
    
    # Podcastfy 配置（所有參數都從配置文件讀取）
    conversation_config = {
        "word_count": word_count,
        "max_num_chunks": max_num_chunks,
        "min_chunk_size": min_chunk_size,
        "conversation_style": conversation_style,
        "language": language,
        "dialogue_structure": dialogue_structure,
        "custom_instructions": f"""
        Create a podcast conversation for {english_level} English learners.
        Podcast length mode: {podcast_length} ({mode['time_range']})
        Style: {style_instructions}
        Use Person1 as Host and Person2 as Expert.
        
        CONTENT STRATEGY:
        {prompt_strategy}
        
        Remember to match the conversation length and depth to the '{podcast_length}' mode.
        """,
        "roles": ["Host", "Expert"],
        "output_folder": "./output"
    }
    
    print(f"🎯 Podcastfy 參數:")
    print(f"   - 目標字數: {word_count}")
    print(f"   - 最大輪次: {max_num_chunks}")
    print(f"   - 最小塊大小: {min_chunk_size}")
    print(f"   - 對話風格: {', '.join(conversation_style)}")
    
    print("🚀 開始生成腳本...")
    
    try:
        # 根據輸入類型調用 Podcastfy
        if input_type == "auto":
            # 自動檢測類型
            if input_source.startswith(('http://', 'https://')):
                if 'youtube.com' in input_source or 'youtu.be' in input_source:
                    input_type = 'youtube'
                else:
                    input_type = 'url'
            elif Path(input_source).exists():
                suffix = Path(input_source).suffix.lower()
                if suffix == '.pdf':
                    input_type = 'pdf'
                else:
                    input_type = 'text'
            else:
                input_type = 'text'
        
        print(f"📄 輸入類型: {input_type}")
        
        # 生成腳本（transcript_only=True 表示只生成腳本）
        if input_type == 'text':
            if Path(input_source).exists():
                with open(input_source, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = input_source
            
            result = generate_podcast(
                text=content,
                llm_model_name=llm_model,
                api_key_label="GEMINI_API_KEY",
                conversation_config=conversation_config,
                transcript_only=True  # 只生成腳本
            )
            
        elif input_type == 'url':
            result = generate_podcast(
                urls=[input_source],
                llm_model_name=llm_model,
                api_key_label="GEMINI_API_KEY",
                conversation_config=conversation_config,
                transcript_only=True
            )
            
        elif input_type == 'youtube':
            result = generate_podcast(
                youtube_urls=[input_source],
                llm_model_name=llm_model,
                api_key_label="GEMINI_API_KEY",
                conversation_config=conversation_config,
                transcript_only=True
            )
            
        elif input_type == 'pdf':
            result = generate_podcast(
                pdf_file_path=input_source,
                llm_model_name=llm_model,
                api_key_label="GEMINI_API_KEY",
                conversation_config=conversation_config,
                transcript_only=True
            )
        else:
            raise ValueError(f"不支援的輸入類型: {input_type}")
        
        # 查找生成的腳本檔案
        transcript_dir = Path("./output/transcripts/")
        transcript_files = sorted(transcript_dir.glob("transcript*.txt"), 
                                key=lambda x: x.stat().st_mtime, reverse=True)
        
        if transcript_files:
            latest_script = transcript_files[0]
            
            # 讀取腳本內容
            with open(latest_script, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 計算統計
            word_count_actual = len(script_content.split())
            
            # 保存到專案目錄
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f"./output/scripts/script_{timestamp}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存腳本
            script_file = output_dir / "podcast_script.txt"
            script_file.write_text(script_content, encoding='utf-8')
            
            # 保存元數據
            metadata = {
                "timestamp": timestamp,
                "input_source": input_source,
                "input_type": input_type,
                "english_level": english_level,
                "podcast_length": podcast_length,
                "time_range": mode['time_range'],
                "target_words": word_count,
                "actual_words": word_count_actual,
                "accuracy": f"{(word_count_actual/word_count*100):.1f}%",
                "script_file": str(script_file),
                "original_file": str(latest_script)
            }
            
            metadata_file = output_dir / "metadata.json"
            metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
            
            print("\n" + "=" * 60)
            print("✅ 腳本生成成功！")
            print(f"📁 輸出目錄: {output_dir}")
            print(f"📝 腳本檔案: {script_file.name}")
            print(f"📊 字數統計: {word_count_actual} 字（目標: {word_count} 字）")
            print(f"📈 準確度: {(word_count_actual/word_count*100):.1f}%")
            print("=" * 60)
            print(f"\n💡 下一步：執行 python step2_generate_audio.py {output_dir}")
            
            return str(output_dir)
            
        else:
            print("❌ 未找到生成的腳本檔案")
            return None
            
    except Exception as e:
        print(f"❌ 腳本生成失敗: {e}")
        return None


if __name__ == "__main__":
    # 如果提供了配置文件路徑，使用它；否則使用預設
    config_path = sys.argv[1] if len(sys.argv) > 1 else "./podcast_config.yaml"
    generate_script_only(config_path)