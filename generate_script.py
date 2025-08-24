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

def load_character_profiles(profiles_path: str = "./character_profiles.yaml"):
    """載入角色設定檔案"""
    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"⚠️ 角色設定檔案未找到: {profiles_path}")
        return {"character_profiles": {}, "voice_pairings": {}}

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
    character_data = load_character_profiles()
    
    # 解析輸入來源
    sources, input_type = parse_input_sources(config)
    english_level = config['basic']['english_level']
    podcast_length = config['basic']['podcast_length']
    llm_model = config['advanced']['llm_model']
    
    # 獲取等級和長度配置
    level_config = config['level_configs'][english_level]
    length_config = config['length_configs'][podcast_length]
    
    # 載入角色設定
    character_profiles = character_data.get('character_profiles', {})
    voice_pairings = character_data.get('voice_pairings', {})
    
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
    
    # 獲取聲線配置
    host_voice = level_config.get('voices', {}).get('host_voice', 'Unknown')
    expert_voice = level_config.get('voices', {}).get('expert_voice', 'Unknown')
    
    # 顯示角色資訊
    print(f"🎙️ 主持人聲線: {host_voice}")
    if host_voice in character_profiles:
        host_char = character_profiles[host_voice]
        print(f"   └── {host_char.get('name', 'Unknown')} ({host_char.get('profession', 'Unknown')})")
    
    print(f"🎙️ 專家聲線: {expert_voice}")
    if expert_voice in character_profiles:
        expert_char = character_profiles[expert_voice]
        print(f"   └── {expert_char.get('name', 'Unknown')} ({expert_char.get('profession', 'Unknown')})")
    
    # 顯示配對動態
    pairing_key = f"{host_voice}_{expert_voice}"
    if pairing_key in voice_pairings:
        pairing_info = voice_pairings[pairing_key]
        print(f"🤝 配對動態: {pairing_info.get('dynamic', 'Standard Professional')}")
        print(f"   └── {pairing_info.get('specialty', 'General discussion')}")
    
    # 新增結構化配置顯示
    print(f"🏗️ 結構深度: {level_config.get('structural_depth', 'balanced')}")
    print(f"⏱️ 內容節奏: {level_config.get('content_pacing', level_config['pace'])}")
    print(f"🧩 參與要素: {', '.join(level_config.get('engagement_factors', level_config['techniques'])[:3])}...")
    print(f"📋 對話結構: {len(level_config['dialogue_structure'])} 個段落")
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
        
        # 說話者角色（來自等級配置的主客分工）
        "roles_person1": level_config.get('roles_person1', 'Host - Discussion Leader'),
        "roles_person2": level_config.get('roles_person2', 'Expert - Content Specialist'),
        
        # 對話結構（來自等級配置）
        "dialogue_structure": level_config['dialogue_structure'],
        
        # 參與技巧（來自等級配置）
        "engagement_techniques": level_config['techniques'],
        
        # 創造力控制（來自等級配置）
        "creativity": level_config['creativity'],
        
        # 結構化對話指令（專業版本4.0）
        "user_instructions": "",
        
        # 保持向後相容
        "roles": ["Host", "Expert"]
    }
    
    # 獲取角色個性資訊
    host_char = character_profiles.get(host_voice, {})
    expert_char = character_profiles.get(expert_voice, {})
    pairing_key = f"{host_voice}_{expert_voice}"
    pairing_info = voice_pairings.get(pairing_key, {})
    
    # 構建詳細的 custom_instructions
    base_instructions = f"""
    Create a natural, structured conversation between two people with clearly defined roles exploring this topic.
    
    === CONVERSATION PROFILE ===
    LEVEL: {english_level} ({level_config['style_name']})
    KNOWLEDGE DENSITY: {level_config['knowledge_density']}
    PACE: {level_config['pace']}
    INTERACTION: {level_config['interaction_level']} interaction
    STRUCTURAL DEPTH: {level_config.get('structural_depth', 'balanced')}
    
    === CHARACTER PROFILES ==="""
    
    # 添加主持人角色資訊
    if host_char:
        host_traits = ', '.join(host_char.get('personality_traits', {}).get('core', []))
        host_phrases = host_char.get('signature_phrases', {}).get('openings', [])[:3]
        base_instructions += f"""
    
    Person1 (HOST) - {host_char.get('name', host_voice)}:
    ROLE: {level_config.get('roles_person1', 'Host - Discussion Leader')}
    BACKGROUND: {host_char.get('background', 'Professional host')}
    PERSONALITY: {host_traits}
    SPEAKING STYLE: {host_char.get('speaking_characteristics', {}).get('tone', 'Professional and clear')}
    SIGNATURE PHRASES: {', '.join(f'"{phrase}"' for phrase in host_phrases)}
    EXPERTISE: {', '.join(host_char.get('expertise_areas', [])[:4])}"""
    else:
        base_instructions += f"""
    
    Person1 (HOST): {level_config.get('roles_person1', 'Host - Discussion Leader')}"""
    
    # 添加專家角色資訊
    if expert_char:
        expert_traits = ', '.join(expert_char.get('personality_traits', {}).get('core', []))
        expert_phrases = expert_char.get('signature_phrases', {}).get('analysis', expert_char.get('signature_phrases', {}).get('observations', []))[:3]
        base_instructions += f"""
    
    Person2 (EXPERT) - {expert_char.get('name', expert_voice)}:
    ROLE: {level_config.get('roles_person2', 'Expert - Content Specialist')}
    BACKGROUND: {expert_char.get('background', 'Subject matter expert')}
    PERSONALITY: {expert_traits}
    SPEAKING STYLE: {expert_char.get('speaking_characteristics', {}).get('tone', 'Knowledgeable and engaging')}
    SIGNATURE PHRASES: {', '.join(f'"{phrase}"' for phrase in expert_phrases)}
    EXPERTISE: {', '.join(expert_char.get('expertise_areas', [])[:4])}"""
    else:
        base_instructions += f"""
    
    Person2 (EXPERT): {level_config.get('roles_person2', 'Expert - Content Specialist')}"""
    
    # 添加配對動態資訊
    if pairing_info:
        base_instructions += f"""
    
    === PAIRING DYNAMIC ===
    CHEMISTRY: {pairing_info.get('dynamic', 'Professional collaboration')}
    INTERACTION PATTERN: {pairing_info.get('interaction_pattern', 'Balanced discussion')}
    SPECIALTY: {pairing_info.get('specialty', 'General expertise sharing')}
    """
    
    base_instructions += f"""
    
    === CORE RESPONSIBILITIES ===
    HOST RESPONSIBILITIES:
    - Opening the show and setting the agenda
    - Breaking down complex concepts into understandable parts
    - Asking clarifying questions to help audience understanding
    - Language teaching (intensity varies by level: A1=heavy, B1=moderate, C1=minimal)
    - Maintaining conversation flow and pacing
    - Embodying their character's personality and speaking style
    
    EXPERT RESPONSIBILITIES:  
    - Providing detailed content knowledge and explanations
    - Answering Host's questions with appropriate depth
    - Sharing insights and professional perspectives
    - Supporting Host's concept-breaking with examples and elaboration
    - Focusing primarily on content accuracy and completeness
    - Demonstrating their character's expertise and communication style
    
    === DIALOGUE STRUCTURE ===
    Follow this {len(level_config['dialogue_structure'])}-part structure naturally:
    {chr(10).join(f'{i+1}. {section}' for i, section in enumerate(level_config['dialogue_structure']))}
    
    === ENGAGEMENT FACTORS ===
    Integrate these elements throughout: {', '.join(level_config.get('engagement_factors', level_config['techniques']))}
    
    === LANGUAGE TEACHING ELEMENTS ===
    Teaching Style: {level_config.get('language_teaching_elements', {}).get('teaching_style', 'none')}
    Focus Areas: {', '.join(level_config.get('language_teaching_elements', {}).get('focus_areas', []))}
    Teaching Markers: {chr(10).join('- "' + marker + '"' for marker in level_config.get('language_teaching_elements', {}).get('teaching_markers', []))}
    Error Correction: {level_config.get('language_teaching_elements', {}).get('error_correction', 'none')}
    Learning Repetition: {level_config.get('language_teaching_elements', {}).get('repetition_for_learning', 'none')}
    
    TEACHING INTEGRATION RULES:
    - {config.get('language_teaching', {}).get('teaching_spectrum', {}).get(english_level, 'content_focused')}
    - For A1: Include explicit vocabulary explanations using teaching markers
    - For A1-A2: Actively teach useful phrases and expressions
    - For B1: Naturally weave in alternative expressions and language tips
    - For B2+: Minimal language focus, content-driven discussion
    
    === NATURAL CONVERSATION MARKERS ===
    Weave these naturally throughout:
    {chr(10).join('- "' + marker + '"' for marker in level_config['conversation_markers'])}
    """
    
    # 添加等級專用的 AVOID/EMBRACE 指導，整合角色個性
    level_specific = ""
    if english_level == 'A1':
        host_name = host_char.get('name', host_voice)
        expert_name = expert_char.get('name', expert_voice)
        level_specific = f"""
        
        === A1 HOST-EXPERT DYNAMIC ===
        HOST ({host_name} - English Teacher): 
        - LEAD the conversation with heavy language teaching focus (80%)
        - Break down every complex word and concept immediately using your {host_char.get('speaking_characteristics', {}).get('tone', 'warm and patient')} approach
        - Ask EXPERT to pause for vocabulary/grammar explanations
        - Use your signature teaching style: {host_char.get('signature_phrases', {}).get('clarifications', ['Let me break this down...'])[0] if host_char.get('signature_phrases', {}).get('clarifications') else 'Let me explain this clearly...'}
        - Constantly check understanding with encouraging phrases like: "{host_char.get('signature_phrases', {}).get('encouragement', ['You are doing great!'])[0] if host_char.get('signature_phrases', {}).get('encouragement') else 'Do you understand?'}"
        - Embody your background as {host_char.get('profession', 'an experienced teacher')}
        
        EXPERT ({expert_name} - Patient Content Provider):
        - WAIT for HOST's language teaching moments with your {expert_char.get('speaking_characteristics', {}).get('tone', 'enthusiastic')} personality
        - Provide simple, clear content explanations when asked, showing your {', '.join(expert_char.get('personality_traits', {}).get('core', ['helpful'])[:2])} nature
        - Support HOST's teaching with examples from your expertise in {', '.join(expert_char.get('expertise_areas', ['general topics'])[:2])}
        - Use basic vocabulary, speak with your characteristic {expert_char.get('speaking_characteristics', {}).get('pace', 'measured pace')}
        - Let HOST dominate the conversation rhythm while contributing your natural curiosity
        
        INTERACTION FLOW: {host_name} asks → {expert_name} explains simply → {host_name} teaches language → {host_name} asks next question
        CHARACTER CHEMISTRY: {pairing_info.get('chemistry', 'Teacher and eager learner working together')}
        """
    elif english_level == 'A2':  
        host_name = host_char.get('name', host_voice)
        expert_name = expert_char.get('name', expert_voice)
        level_specific = f"""
        
        === A2 HOST-EXPERT DYNAMIC ===
        HOST ({host_name} - Friendly Language Guide):
        - GUIDE the conversation with natural language teaching (60%) using your {host_char.get('speaking_characteristics', {}).get('tone', 'warm')} personality
        - Introduce useful phrases and expressions contextually, drawing from your expertise in {', '.join(host_char.get('expertise_areas', ['language teaching'])[:2])}
        - Ask EXPERT to demonstrate natural language usage with your characteristic curiosity
        - Use your signature guidance style: "{host_char.get('signature_phrases', {}).get('transitions', ['Let me show you another way...'])[0] if host_char.get('signature_phrases', {}).get('transitions') else 'Here is how native speakers say it...'}"
        - Encourage EXPERT with your naturally {', '.join(host_char.get('personality_traits', {}).get('core', ['supportive']))} approach
        
        EXPERT ({expert_name} - Patient Teacher):
        - COLLABORATE with HOST on language demonstrations using your {expert_char.get('speaking_characteristics', {}).get('tone', 'knowledgeable')} style
        - Provide content knowledge with clear, natural expressions, showing your background in {expert_char.get('profession', 'content expertise')}
        - Offer alternative ways to say things when prompted by HOST, using your {', '.join(expert_char.get('personality_traits', {}).get('core', ['helpful']))} nature
        - Use slightly more complex vocabulary with HOST's guidance, maintaining your characteristic {expert_char.get('speaking_characteristics', {}).get('pace', 'thoughtful pace')}
        - Support HOST's teaching with examples from your expertise
        
        INTERACTION FLOW: {host_name} introduces topic → {expert_name} explains → {host_name} guides language → Both explore together
        CHARACTER CHEMISTRY: {pairing_info.get('chemistry', 'Collaborative language exploration')}
        """
    elif english_level == 'B1':
        host_name = host_char.get('name', host_voice)
        expert_name = expert_char.get('name', expert_voice)
        level_specific = f"""
        
        === B1 HOST-EXPERT DYNAMIC ===
        HOST ({host_name} - Conversational Language Coach):
        - MODERATE the conversation with integrated language coaching (40%) using your {host_char.get('speaking_characteristics', {}).get('tone', 'balanced')} style
        - Weave in language tips during natural conversation flow, showing your {', '.join(host_char.get('personality_traits', {}).get('core', ['thoughtful']))} personality
        - Appreciate EXPERT's language use with phrases like: "{host_char.get('signature_phrases', {}).get('appreciation', host_char.get('signature_phrases', {}).get('observations', ['That is fascinating...']))[0] if host_char.get('signature_phrases', {}).get('appreciation') or host_char.get('signature_phrases', {}).get('observations') else 'That is a great way to put it...'}"
        - Offer alternatives naturally, drawing from your expertise in {', '.join(host_char.get('expertise_areas', ['communication'])[:2])}
        - Balance content exploration with language guidance using your professional background
        
        EXPERT ({expert_name} - Knowledgeable Discussant):
        - ENGAGE in substantial content discussion with HOST using your {expert_char.get('speaking_characteristics', {}).get('tone', 'engaging')} communication style
        - Use varied vocabulary and expressions naturally, reflecting your {', '.join(expert_char.get('personality_traits', {}).get('core', ['knowledgeable']))} nature
        - Welcome HOST's language coaching and build on it with your characteristic {expert_char.get('speaking_characteristics', {}).get('emphasis', 'thoughtful emphasis')}
        - Provide detailed explanations from your expertise in {', '.join(expert_char.get('expertise_areas', ['subject matter'])[:3])}
        - Share the conversation space more equally, showing your {', '.join(expert_char.get('personality_traits', {}).get('communication', ['articulate']))} traits
        
        INTERACTION FLOW: {host_name} moderates → {expert_name} discusses deeply → {host_name} coaches language → Both explore implications
        CHARACTER CHEMISTRY: {pairing_info.get('chemistry', 'Balanced professional dialogue')}
        """
    else:  # B2, C1, C2
        host_name = host_char.get('name', host_voice)
        expert_name = expert_char.get('name', expert_voice)
        level_specific = f"""
        
        === {english_level} HOST-EXPERT DYNAMIC ===
        HOST ({host_name} - Professional Moderator):
        - FACILITATE sophisticated content exploration using your {host_char.get('speaking_characteristics', {}).get('tone', 'authoritative')} presence
        - Break down complex concepts for audience understanding, leveraging your background in {host_char.get('profession', 'professional moderation')}
        - Ask probing questions to deepen analysis with your signature style: "{host_char.get('signature_phrases', {}).get('inquiry', host_char.get('signature_phrases', {}).get('observations', ['What strikes me is...']))[0] if host_char.get('signature_phrases', {}).get('inquiry') or host_char.get('signature_phrases', {}).get('observations') else 'The real question here is...'}"
        - Minimal language focus - only when truly beneficial, showing your {', '.join(host_char.get('personality_traits', {}).get('core', ['strategic']))} nature
        - Guide conversation toward key insights using your expertise in {', '.join(host_char.get('expertise_areas', ['analysis'])[:2])}
        
        EXPERT ({expert_name} - Domain Authority):
        - PROVIDE in-depth knowledge and professional insights using your {expert_char.get('speaking_characteristics', {}).get('tone', 'authoritative')} communication style
        - Engage in sophisticated analysis and discussion, drawing from your extensive background: {expert_char.get('background', 'Professional expertise')}
        - Share specialized perspectives from your expertise in {', '.join(expert_char.get('expertise_areas', ['specialized knowledge'])[:3])}
        - Use technical language appropriately, reflecting your {', '.join(expert_char.get('personality_traits', {}).get('core', ['expert']))} credentials
        - Take substantial conversation space for detailed explanations with your characteristic {expert_char.get('speaking_characteristics', {}).get('emphasis', 'confident delivery')}
        
        INTERACTION FLOW: {host_name} facilitates → {expert_name} analyzes deeply → {host_name} synthesizes → {expert_name} provides implications
        CHARACTER CHEMISTRY: {pairing_info.get('chemistry', 'Professional expertise sharing')}
        FOCUS: Content-driven discussion with sophisticated concept exploration
        """
    
    # 組合完整指令，添加明確的長度控制
    conversation_config["user_instructions"] = base_instructions + level_specific + f"""
    
    === CONVERSATION GUIDELINES ===
    - HOST always opens and sets agenda
    - EXPERT provides knowledge when asked
    - Both maintain their distinct roles throughout
    - Language teaching varies by level (A1=heavy, B1=moderate, C1=minimal)
    - Concept breaking is always HOST's primary job
    - Content expertise is always EXPERT's primary job
    
    === LENGTH REQUIREMENTS ===
    TARGET LENGTH: {word_count} words ({length_config['time_range']})
    APPROACH: {length_config['approach']}
    IMPORTANT: Generate EXACTLY {word_count} words, no more, no less.
    Stop the conversation naturally when approaching {word_count} words.
    Conclude with a proper ending rather than cutting off mid-sentence.
    """
    
    # 輸出指令長度用於調試
    instruction_length = len(conversation_config["user_instructions"])
    print(f"🔍 Instructions length: {instruction_length} characters (~{instruction_length//4} tokens)")
    
    # 根據長度設定決定是否啟用 longform 模式
    use_longform = (podcast_length == "extra-long")
    
    print(f"🎯 Podcastfy 參數:")
    print(f"   - 目標字數: {word_count}")
    print(f"   - 最大輪次: {max_num_chunks}")
    print(f"   - 最小塊大小: {min_chunk_size}")
    print(f"   - 對話風格: {', '.join(conversation_style)}")
    print(f"   - 長篇模式: {'啟用' if use_longform else '關閉'}")
    
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
                    transcript_only=True,
                    longform=use_longform
                )
            elif all_urls:
                # 純 URL 模式
                result = generate_podcast(
                    urls=all_urls,
                    llm_model_name=llm_model,
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    transcript_only=True,
                    longform=use_longform
                )
            elif combined_text:
                # 純文字模式
                result = generate_podcast(
                    text=combined_text,
                    llm_model_name=llm_model,
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    transcript_only=True,
                    longform=use_longform
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
                    transcript_only=True,  # 只生成腳本
                    longform=use_longform
                )
            
            elif input_type == 'url':
                result = generate_podcast(
                    urls=[input_source],
                    llm_model_name=llm_model,
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    transcript_only=True,
                    longform=use_longform
                )
                
            elif input_type == 'youtube':
                result = generate_podcast(
                    youtube_urls=[input_source],
                    llm_model_name=llm_model,
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    transcript_only=True,
                    longform=use_longform
                )
                
            elif input_type == 'pdf':
                result = generate_podcast(
                    pdf_file_path=input_source,
                    llm_model_name=llm_model,
                    api_key_label="GEMINI_API_KEY",
                    conversation_config=conversation_config,
                    transcript_only=True,
                    longform=use_longform
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