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
    print("📝 Step 1: Podcastfy 腳本生成")
    print("=" * 60)
    
    # 載入配置
    config = load_config(config_path)
    
    # 解析輸入來源
    sources, input_type = parse_input_sources(config)
    english_level = config['basic']['english_level']
    podcast_length = config['basic']['podcast_length']
    style_instructions = config['basic']['style_instructions']
    llm_model = config['advanced']['llm_model']
    
    print(f"📥 輸入模式: {input_type}")
    if input_type == 'multi':
        print(f"📂 資料來源數量: {len(sources)}")
        for i, source in enumerate(sources, 1):
            source_preview = str(source)[:60] + "..." if len(str(source)) > 60 else str(source)
            print(f"   {i}. {source_preview}")
    else:
        print(f"📥 輸入來源: {sources[0]}")
    
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
    
    # 英語等級特定的教學策略
    level_strategies = {
        "A1": {
            "vocabulary": "Use only basic, high-frequency words (top 1000 most common)",
            "grammar": "Simple present/past tense, basic sentence structures (S+V+O)",
            "techniques": """
            - Define EVERY new concept immediately after introducing it
            - Repeat key information 3-4 times using different words
            - Use analogies with everyday objects (like 'computer is like a brain')
            - Break complex ideas into 3-4 simple steps
            - Person1 asks clarifying questions like 'What does that mean?'
            - Person2 explains with examples from daily life
            - Include pauses for comprehension (use phrases like 'Let's think about this...')
            - Knowledge density: 1 new concept per 2-3 minutes""",
            "creativity": 0.3
        },
        "A2": {
            "vocabulary": "Common words plus some topic-specific terms (top 2000 words)",
            "grammar": "Present continuous, simple future, basic conjunctions",
            "techniques": """
            - Explain new concepts with 'In other words...' or 'This means that...'
            - Repeat important points 2-3 times with variations
            - Use concrete examples before abstract concepts
            - Person1 summarizes what Person2 said to confirm understanding
            - Include phrases like 'Let me explain this differently...'
            - Compare new ideas to familiar concepts
            - Knowledge density: 1 new concept per 1-2 minutes""",
            "creativity": 0.4
        },
        "B1": {
            "vocabulary": "Wider range including some abstract terms (top 3500 words)",
            "grammar": "All basic tenses, conditional sentences, relative clauses",
            "techniques": """
            - Explain complex concepts once, then provide one example
            - Repeat only the most critical points
            - Mix concrete and abstract explanations
            - Person1 and Person2 build on each other's ideas
            - Include some technical vocabulary with brief explanations
            - Knowledge density: 1-2 new concepts per minute""",
            "creativity": 0.5
        },
        "B2": {
            "vocabulary": "Rich vocabulary including idiomatic expressions",
            "grammar": "Complex structures, passive voice, reported speech",
            "techniques": """
            - Introduce concepts with minimal repetition
            - Use professional terminology with context clues
            - Discuss implications and connections between ideas
            - Natural conversational flow with interruptions and elaborations
            - Knowledge density: 2-3 new concepts per minute""",
            "creativity": 0.6
        },
        "C1": {
            "vocabulary": "Sophisticated vocabulary, technical terms, nuanced expressions",
            "grammar": "Full range of complex structures, subjunctive mood",
            "techniques": """
            - Rapid introduction of complex concepts
            - Assume background knowledge, minimal explanations
            - Discuss abstract theories and hypotheticals
            - Use academic discourse markers
            - Knowledge density: 3-4 new concepts per minute""",
            "creativity": 0.7
        },
        "C2": {
            "vocabulary": "Native-level vocabulary, specialized jargon, cultural references",
            "grammar": "Native-like flexibility and complexity",
            "techniques": """
            - Dense information delivery
            - Implicit connections between concepts
            - Sophisticated humor and wordplay
            - Multiple layers of meaning
            - Knowledge density: 4+ new concepts per minute""",
            "creativity": 0.8
        }
    }
    
    # 獲取對應等級的策略
    level_strategy = level_strategies.get(english_level, level_strategies["B1"])
    
    # 從配置讀取 Podcastfy 進階設定（如果存在）
    podcastfy_config = config.get('podcastfy', {})
    
    # Podcastfy 完整配置（整合所有進階功能）
    conversation_config = {
        # 基本參數
        "word_count": word_count,
        "max_num_chunks": max_num_chunks,
        "min_chunk_size": min_chunk_size,
        "language": language,
        "output_folder": "./output",
        
        # 品牌化設定
        "podcast_name": podcastfy_config.get('podcast_name', 'AI Learning Podcast'),
        "podcast_tagline": podcastfy_config.get('podcast_tagline', 'Your Personal Learning Companion'),
        "output_language": podcastfy_config.get('output_language', 'English'),
        
        # 對話風格（支援陣列格式）
        "conversation_style": podcastfy_config.get('conversation_style', conversation_style),
        
        # 說話者角色（更具體的角色定義）
        "roles_person1": podcastfy_config.get('roles_person1', f"{english_level} Learning Host"),
        "roles_person2": podcastfy_config.get('roles_person2', "Subject Matter Expert"),
        
        # 對話結構（自定義播客流程）
        "dialogue_structure": podcastfy_config.get('dialogue_structure', [
            "Welcome & Topic Introduction",
            "Key Concepts Overview", 
            "Detailed Explanation",
            "Real-World Examples",
            "Learning Summary"
        ]),
        
        # 參與技巧（提升吸引力）
        "engagement_techniques": podcastfy_config.get('engagement_techniques', [
            "rhetorical questions",
            "analogies", 
            "real-world examples",
            "step-by-step explanations"
        ]),
        
        # 創造力控制（根據等級調整）
        "creativity": podcastfy_config.get('creativity', level_strategy["creativity"]),
        
        # 自定義指令（整合等級策略和用戶指令）
        "custom_instructions": f"""
        {podcastfy_config.get('user_instructions', '')}
        
        Create an educational podcast for {english_level} English learners.
        
        LANGUAGE REQUIREMENTS:
        - Vocabulary: {level_strategy['vocabulary']}
        - Grammar: {level_strategy['grammar']}
        
        PEDAGOGICAL TECHNIQUES:
        {level_strategy['techniques']}
        
        PODCAST SPECIFICATIONS:
        - Length: {podcast_length} ({mode['time_range']})
        - Style: {style_instructions}
        - Host Role: {podcastfy_config.get('roles_person1', f'{english_level} Learning Host')}
        - Expert Role: {podcastfy_config.get('roles_person2', 'Subject Matter Expert')}
        
        CONTENT STRATEGY:
        {prompt_strategy}
        
        IMPORTANT: Adapt your language complexity, explanation depth, and repetition frequency strictly according to the {english_level} level requirements above.""",
        
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