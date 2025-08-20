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

def parse_input_sources(config):
    """解析輸入來源配置，支援單一/多資料來源"""
    input_config = config['input']
    input_type = input_config.get('type', 'auto')
    
    if input_type == 'multi':
        # 多資料來源模式
        sources = input_config.get('sources', [])
        if not sources:
            raise ValueError("多資料來源模式但未提供 sources 陣列")
        return sources, 'multi'
    else:
        # 單一來源模式（向後相容）
        source = input_config.get('source')
        if not source:
            raise ValueError("單一來源模式但未提供 source")
        return [source], input_type

def categorize_sources(sources):
    """將多個來源按類型分類"""
    urls = []
    youtube_urls = []
    pdf_files = []
    text_files = []
    direct_texts = []
    
    for source in sources:
        source_str = str(source).strip()
        
        if source_str.startswith(('http://', 'https://')):
            if 'youtube.com' in source_str or 'youtu.be' in source_str:
                youtube_urls.append(source_str)
            else:
                urls.append(source_str)
        elif Path(source_str).exists():
            if source_str.lower().endswith('.pdf'):
                pdf_files.append(source_str)
            else:
                text_files.append(source_str)
        else:
            # 直接文字內容
            direct_texts.append(source_str)
    
    return {
        'urls': urls,
        'youtube_urls': youtube_urls, 
        'pdf_files': pdf_files,
        'text_files': text_files,
        'direct_texts': direct_texts
    }

def generate_script_only(config_path: str = "./podcast_config.yaml"):
    """只生成腳本，不生成音頻"""
    
    print("=" * 60)
    print("📝 自然對話播客腳本生成")
    print("=" * 60)
    
    # 載入配置
    config = load_config(config_path)
    
    # 解析輸入來源
    sources, input_type = parse_input_sources(config)
    english_level = config['basic']['english_level']
    podcast_length = config['basic']['podcast_length']
    llm_model = config['advanced']['llm_model']
    
    # 獲取等級和長度配置
    level_config = config['level_configs'][english_level]
    length_config = config['length_configs'][podcast_length]
    
    print(f"📥 輸入模式: {input_type}")
    if input_type == 'multi':
        print(f"📂 資料來源數量: {len(sources)}")
        for i, source in enumerate(sources, 1):
            source_preview = str(source)[:60] + "..." if len(str(source)) > 60 else str(source)
            print(f"   {i}. {source_preview}")
    else:
        print(f"📥 輸入來源: {sources[0]}")
    
    print(f"🎯 對話等級: {english_level} ({level_config['style_name']})")
    print(f"📏 播客長度: {podcast_length} ({length_config['time_range']})")
    print(f"🤖 LLM 模型: {llm_model}")
    print(f"🎭 對話風格: {', '.join(level_config['conversation_style'])}")
    print("-" * 60)
    
    # 使用統一配置的長度和等級設定
    word_count = length_config['word_count']
    max_num_chunks = length_config['max_num_chunks']
    min_chunk_size = length_config['min_chunk_size']
    
    print(f"📌 {length_config['approach']}（{length_config['time_range']}）")
    
    # 從等級配置讀取對話設定
    conversation_style = level_config['conversation_style']
    language = config['advanced'].get('language', "English")
    dialogue_structure = config['advanced'].get('dialogue_structure', "two_speakers")
    
    # 檢查等級配置是否存在
    if english_level not in config['level_configs']:
        print(f"⚠️ 未知的等級 '{english_level}'，使用預設 'B1'")
        english_level = "B1"
        level_config = config['level_configs']['B1']
    
    print(f"🎯 對話模式: {level_config['style_name']} - {level_config['knowledge_density']} 知識密度")
    
    # Podcastfy 配置（使用統一的等級和長度設定）
    conversation_config = {
        # 基本參數
        "word_count": word_count,
        "max_num_chunks": max_num_chunks,
        "min_chunk_size": min_chunk_size,
        "language": language,
        "output_folder": "./output",
        
        # 品牌化（根據等級動態生成）
        "podcast_name": f"Natural Conversations - {level_config['style_name']}",
        "podcast_tagline": "Where curiosity meets understanding through natural dialogue",
        "output_language": "English",
        
        # 對話風格（來自等級配置）
        "conversation_style": conversation_style,
        
        # 說話者角色（去除教學色彩）
        "roles_person1": "Curious Discussant",
        "roles_person2": "Thoughtful Contributor",
        
        # 對話結構（來自等級配置）
        "dialogue_structure": level_config['dialogue_structure'],
        
        # 參與技巧（來自等級配置）
        "engagement_techniques": level_config['techniques'],
        
        # 創造力控制（來自等級配置）
        "creativity": level_config['creativity'],
        
        # 自然對話指令（根據等級自動生成）
        "custom_instructions": f"""
        Create a natural conversation between two genuinely curious people exploring this topic.
        
        CONVERSATION LEVEL: {english_level} ({level_config['style_name']})
        KNOWLEDGE DENSITY: {level_config['knowledge_density']}
        PACE: {level_config['pace']}
        INTERACTION: {level_config['interaction_level']} interaction
        
        NATURAL CONVERSATION MARKERS:
        {chr(10).join('- "' + marker + '"' for marker in level_config['conversation_markers'])}
        
        CONVERSATION PRINCIPLES:
        1. Both speakers are genuinely curious and engaged
        2. Knowledge emerges through natural discussion, not teaching
        3. Use authentic reactions and organic idea building
        4. Maintain {level_config['pace']} pace with {level_config['interaction_level']} interaction
        5. Apply {level_config['knowledge_density']} knowledge density naturally
        
        ENGAGEMENT TECHNIQUES:
        {', '.join(level_config['techniques'])}
        
        AVOID: Teaching language, structured lessons, "let me explain" phrases
        EMBRACE: Genuine curiosity, collaborative exploration, natural discovery
        
        TARGET: {length_config['time_range']} of natural, engaging conversation
        APPROACH: {length_config['approach']}
        """,
        
        # 保持向後相容
        "roles": ["Host", "Expert"]
    }
    
    print(f"🎯 Podcastfy 參數:")
    print(f"   - 目標字數: {word_count}")
    print(f"   - 最大輪次: {max_num_chunks}")
    print(f"   - 最小塊大小: {min_chunk_size}")
    print(f"   - 對話風格: {', '.join(conversation_style)}")
    
    print("🚀 開始生成腳本...")
    
    try:
        # 處理多資料來源或單一來源
        if input_type == 'multi':
            # 多資料來源處理
            categorized = categorize_sources(sources)
            
            print("📊 來源分析:")
            if categorized['urls']: print(f"   🌐 網頁: {len(categorized['urls'])} 個")
            if categorized['youtube_urls']: print(f"   📹 YouTube: {len(categorized['youtube_urls'])} 個")
            if categorized['pdf_files']: print(f"   📄 PDF: {len(categorized['pdf_files'])} 個")
            if categorized['text_files']: print(f"   📝 文字檔案: {len(categorized['text_files'])} 個")
            if categorized['direct_texts']: print(f"   💭 直接文字: {len(categorized['direct_texts'])} 段")
            
            # 使用 Podcastfy 的多來源支援
            all_urls = categorized['urls'] + categorized['youtube_urls']
            
            # 讀取本地文件內容
            combined_text = ""
            for text_file in categorized['text_files']:
                with open(text_file, 'r', encoding='utf-8') as f:
                    combined_text += f"\n\n=== 來源: {text_file} ===\n" + f.read()
            
            # 加入直接文字
            for i, direct_text in enumerate(categorized['direct_texts'], 1):
                combined_text += f"\n\n=== 直接輸入 {i} ===\n" + direct_text
            
            # 處理 PDF 檔案（暫時加到文字中，之後可優化）
            for pdf_file in categorized['pdf_files']:
                combined_text += f"\n\n=== PDF 檔案: {pdf_file} ===\n[需要 PDF 內容解析]"            
            
            # 調用 Podcastfy
            print("🚀 開始處理多資料來源...")
            if all_urls and combined_text:
                # URL + 文字混合模式
                result = generate_podcast(
                    urls=all_urls,
                    text=combined_text,
                    llm_model_name=llm_model,
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    transcript_only=True
                )
            elif all_urls:
                # 純 URL 模式
                result = generate_podcast(
                    urls=all_urls,
                    llm_model_name=llm_model,
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    transcript_only=True
                )
            elif combined_text:
                # 純文字模式
                result = generate_podcast(
                    text=combined_text,
                    llm_model_name=llm_model,
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    transcript_only=True
                )
            else:
                raise ValueError("多資料來源模式但未找到有效來源")
        
        else:
            # 單一來源處理（原有邏輯）
            input_source = sources[0]
            
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
        
        # 查找生成的腳本檔案（修正路徑）
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
            output_dir = Path(f"./output/scripts/script_{timestamp}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存腳本
            script_file = output_dir / "podcast_script.txt"
            script_file.write_text(script_content, encoding='utf-8')
            
            # 保存元數據
            metadata = {
                "timestamp": timestamp,
                "input_type": input_type,
                "english_level": english_level,
                "podcast_length": podcast_length,
                "time_range": length_config['time_range'],
                "target_words": word_count,
                "actual_words": word_count_actual,
                "accuracy": f"{(word_count_actual/word_count*100):.1f}%",
                "script_file": str(script_file),
                "original_file": str(latest_script)
            }
            
            # 根據輸入模式添加來源資訊
            if input_type == 'multi':
                metadata["input_sources"] = sources
                metadata["source_count"] = len(sources)
                if 'categorized' in locals():
                    metadata["source_breakdown"] = {
                        "urls": len(categorized['urls']),
                        "youtube_urls": len(categorized['youtube_urls']),
                        "pdf_files": len(categorized['pdf_files']),
                        "text_files": len(categorized['text_files']),
                        "direct_texts": len(categorized['direct_texts'])
                    }
            else:
                metadata["input_source"] = sources[0]
            
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