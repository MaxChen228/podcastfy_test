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
    target_minutes = config['basic']['target_minutes']
    style_instructions = config['basic']['style_instructions']
    llm_model = config['advanced']['llm_model']
    
    print(f"📥 輸入來源: {input_source}")
    print(f"🎯 英語等級: {english_level}")
    print(f"⏱️ 目標長度: {target_minutes} 分鐘")
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
        # 根據目標時長自動計算參數（基於社區最佳實踐）
        community_best_practices = {
            0.5: {"word_count": 200, "max_num_chunks": 3, "min_chunk_size": 600},
            1: {"word_count": 300, "max_num_chunks": 4, "min_chunk_size": 600},
            2: {"word_count": 600, "max_num_chunks": 5, "min_chunk_size": 600},
            3: {"word_count": 800, "max_num_chunks": 6, "min_chunk_size": 600},
            5: {"word_count": 1200, "max_num_chunks": 8, "min_chunk_size": 700},
            10: {"word_count": 2000, "max_num_chunks": 12, "min_chunk_size": 800},
        }
        
        # 找到最接近的配置
        closest_time = min(community_best_practices.keys(), 
                          key=lambda x: abs(x - target_minutes))
        params = community_best_practices[closest_time]
        
        word_count = params["word_count"]
        max_num_chunks = params["max_num_chunks"]
        min_chunk_size = params["min_chunk_size"]
        print(f"📌 使用自動計算的長度控制參數（基於 {closest_time} 分鐘配置）")
    
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
        Target duration: {target_minutes} minute(s)
        Style: {style_instructions}
        Use Person1 as Host and Person2 as Expert.
        """,
        "roles": ["Host", "Expert"],
        "output_folder": "./data"
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
        transcript_dir = Path("./data/transcripts/")
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
            output_dir = Path(f"./scripts/script_{timestamp}")
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
                "target_minutes": target_minutes,
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