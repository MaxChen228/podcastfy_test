#!/usr/bin/env python3
"""
Step 2: LLM 智能標籤嵌入引擎
分析腳本內容，根據英語等級配置智能嵌入 SSML 和情感標籤
"""

import os
import sys
import json
import yaml
import google.generativeai as genai
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TagEmbeddingEngine:
    """LLM 驅動的標籤嵌入引擎"""
    
    def __init__(self, config: Dict[Any, Any], english_level: str):
        """
        初始化標籤嵌入引擎
        
        Args:
            config: 播客配置字典
            english_level: 英語等級 (A1-C2)
        """
        self.config = config
        self.english_level = english_level
        self.level_config = config['level_configs'][english_level]
        self.tag_config = self.level_config.get('tag_embedding', {})
        
        # Get model configurations
        self.tag_embedding_config = config.get('tag_embedding', {})
        models_config = self.tag_embedding_config.get('models', {})
        
        # Fallback for backward compatibility
        fallback_model = self.tag_embedding_config.get('llm_model', 'gemini-1.5-flash-latest')
        
        self.analysis_model_name = models_config.get('analysis_model', fallback_model)
        self.tagging_model_name = models_config.get('tagging_model', fallback_model)
        
        # Get model parameters
        self.model_params = self.tag_embedding_config.get('model_parameters', {})
        self.content_processing = self.tag_embedding_config.get('content_processing', {})
        self.tag_validation = self.tag_embedding_config.get('tag_validation', {})
        
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        # Initialize two separate models
        self.analysis_model = genai.GenerativeModel(self.analysis_model_name)
        self.tagging_model = genai.GenerativeModel(self.tagging_model_name)
        
        self.generation_config = genai.types.GenerationConfig(
            temperature=self.model_params.get('temperature', 0.3),
            top_p=self.model_params.get('top_p', 0.8),
            top_k=self.model_params.get('top_k', 40),
            max_output_tokens=self.model_params.get('max_output_tokens', 8192)
        )
    
    def analyze_dialogue_context(self, script_content: str) -> Dict[str, Any]:
        """分析對話內容，識別情境和情緒"""
        
        analysis_prompt = f"""
        Please analyze the content and context of the following podcast dialogue script:

        {script_content}

        Please answer the following:
        1. The primary mood of the dialogue (e.g., positive, neutral, serious).
        2. The pace of the dialogue (e.g., slow, moderate, fast).
        3. The complexity of the main topic (e.g., basic, intermediate, advanced).
        4. Suggested primary emotion tags (3-5 tags).
        5. Suggested types of pauses (e.g., long pauses between paragraphs, short pauses between sentences).

        Please respond in JSON format:
        {{
            "mood": "positive/neutral/serious",
            "pace": "slow/moderate/fast", 
            "complexity": "basic/intermediate/advanced",
            "suggested_emotions": ["emotion1", "emotion2", "emotion3"],
            "pause_strategy": "A description of the pause strategy"
        }}
        """
        
        try:
            response = self.analysis_model.generate_content(
                analysis_prompt,
                generation_config=self.generation_config
            )
            analysis_text = response.text.strip()
            
            # 嘗試解析 JSON
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
            elif analysis_text.startswith('```'):
                analysis_text = analysis_text.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(analysis_text)
            return analysis
            
        except Exception as e:
            print(f"⚠️ 內容分析失敗，使用預設設定: {e}")
            return {
                "mood": "中性",
                "pace": "中等",
                "complexity": "中等",
                "suggested_emotions": ["conversational", "thoughtful", "engaged"],
                "pause_strategy": "段落間適度停頓"
            }
    
    def generate_tag_embedding_prompt(self, script_content: str, analysis: Dict[str, Any]) -> str:
        """Generates the LLM prompt for tag embedding based on configuration and analysis."""
        
        # Get level-specific tag strategy
        density = self.tag_config.get('density', 'moderate')
        emotion_range = self.tag_config.get('emotion_range', ['conversational', 'thoughtful'])
        
        # Construct the prompt template in English
        prompt = f"""
As an expert Audio Director, your task is to creatively embed TTS tags into the following script to bring the dialogue to life, making it sound natural and expressive.

=== CRITICAL DIRECTIVE: DO NOT MODIFY THE ORIGINAL TEXT ===
This is the most important rule. The text content of the script (the dialogue itself) MUST remain IDENTICAL after you add the tags.
- DO NOT translate any words.
- DO NOT add or remove any words.
- DO NOT change the order of the dialogue.
Your only job is to INSERT tags like [happy] or [PAUSE=1s]. Any modification to the source text will result in failure.

=== Creative Principles & Guidelines ===
Instead of rigid rules, consider these principles for a more artistic result:
1.  **Natural Flow:** Strive for a natural density of tags. They should enhance the conversation, not distract from it.
2.  **Emotional Nuance:** Embed tags at points of emotional transition, even mid-sentence, to capture the speaker's changing feelings.
3.  **Keyword Emphasis:** Consider using tags to add weight or emotion to key words and concepts.
4.  **Rhythmic Pauses:** Use a variety of pauses (e.g., [PAUSE=500ms], [brief pause]) to create a realistic and thoughtful conversational rhythm.

=== Available Tag Palette ===
Here is a rich palette of tags you can use. Prioritize from this list, but feel free to use other common emotional tags if they fit the context perfectly.

**1. Core Emotions:**
- Positive: [happy], [excited], [joyful], [satisfied], [delighted], [proud], [grateful], [relaxed], [confident], [amused]
- Negative: [sad], [angry], [frustrated], [disappointed], [worried], [nervous], [scared], [upset]
- Complex/Neutral: [serious], [curious], [interested], [confused], [surprised], [empathetic], [sincere], [hesitating]

**2. Vocal Effects & Human Sounds:**
- Laughter: [laughing], [chuckling], [giggles]
- Breathing/Sounds: [sighing], [panting], [gasping], [breathing], [yawning], [coughing], [sniffing], [groaning]

**3. Speaking Style & Tone:**
- Style: [conversational], [professional], [storytelling], [narrator], [childlike]
- Tone: [sarcastic], [comforting], [disapproving], [astonished]

**4. Intensity & Volume:**
- Volume: [whisper], [soft], [loud], [shout]
- Intensity: [gentle], [dramatic], [emphasized], [intense], [calm]

**5. Pacing & Pauses:**
- Timed Pauses: [PAUSE=500ms], [PAUSE=1s], [PAUSE=2s], [PAUSE=3s]
- Descriptive Pauses: [brief pause], [long pause], [dramatic pause]
- Pace: [slow], [fast], [rushed], [relaxed pace]

=== Level-Specific Styling ===
"""

        # Provide specific guidance based on the level
        if self.english_level in ['A1', 'A2']:
            prompt += """
- **Goal:** Create a gentle, supportive, and easy-to-follow listening experience.
- **Guidance:** Prioritize basic, positive emotions like [gentle], [curious], [supportive], [happy]. Use ample pauses ([PAUSE=1s], [PAUSE=2s]) to give the listener time to process. Avoid complex or intense emotional tags.
"""
        elif self.english_level in ['B1', 'B2']:
            prompt += """
- **Goal:** Achieve a balanced, natural, and engaging conversational flow.
- **Guidance:** Use a wider range of balanced emotions like [thoughtful], [engaged], [analytical], [amused]. Employ moderate and varied pauses to create a natural rhythm. Feel free to use selective emphasis.
"""
        else:  # C1, C2
            prompt += """
- **Goal:** Deliver a sophisticated, nuanced, and professional discourse.
- **Guidance:** Use a rich palette of complex emotions like [analytical], [insightful], [sincere], [sophisticated]. Employ strategic and dramatic pauses to underscore key points and arguments.
"""

        prompt += f"""

=== Final Output ===
Now, please apply your expertise to the following script. Remember the critical directive: do not change the original text.

Original Script:
{script_content}

Tagged Script:
"""
        
        return prompt
    
    def embed_tags_with_llm(self, script_content: str) -> str:
        """使用 LLM 進行智能標籤嵌入"""
        
        print("🧠 分析對話內容...")
        analysis = self.analyze_dialogue_context(script_content)
        
        print(f"📊 分析結果：{analysis['mood']} 氛圍，{analysis['pace']} 節奏")
        
        print("🏷️ 生成標籤嵌入提示...")
        prompt = self.generate_tag_embedding_prompt(script_content, analysis)
        
        print("🤖 LLM 執行標籤嵌入...")
        try:
            response = self.tagging_model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            tagged_content = response.text.strip()
            
            # 移除可能的 markdown 格式標記
            if tagged_content.startswith('```'):
                lines = tagged_content.split('\n')
                start_idx = 1 if lines[0].startswith('```') else 0
                end_idx = len(lines)
                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip() == '```':
                        end_idx = i
                        break
                tagged_content = '\n'.join(lines[start_idx:end_idx])
            
            return tagged_content
            
        except Exception as e:
            print(f"❌ LLM 標籤嵌入失敗: {e}")
            return script_content  # 返回原始腳本作為降級方案
    
    def post_process_tags(self, tagged_script: str) -> str:
        """後處理：驗證標籤格式，修正錯誤"""
        
        # 基本格式檢查和修正
        processed = tagged_script
        
        # 修正常見的標籤格式錯誤
        replacements = {
            '[PAUSE:': '[PAUSE=',  # 修正停頓格式
            '[pause=': '[PAUSE=',  # 統一大小寫
            '[Pause=': '[PAUSE=',  # 統一大小寫
            '[BREAK=': '[PAUSE=',  # 統一停頓標籤
        }
        
        for old, new in replacements.items():
            processed = processed.replace(old, new)
        
        # 移除可能的重複空行
        lines = processed.split('\n')
        clean_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = line.strip() == ''
            if not (is_empty and prev_empty):  # 避免連續空行
                clean_lines.append(line)
            prev_empty = is_empty
        
        return '\n'.join(clean_lines)
    
    def calculate_tag_statistics(self, original_script: str, tagged_script: str) -> Dict[str, Any]:
        """計算標籤使用統計"""
        
        import re
        
        # 計算不同類型標籤的使用次數
        emotion_pattern = r'\[(happy|sad|angry|excited|calm|nervous|thoughtful|curious|gentle|confident|analytical|professional|sophisticated|insightful)\]'
        pause_pattern = r'\[PAUSE=\d+(?:s|ms)\]|\[(?:brief|long|dramatic) pause\]'
        prosody_pattern = r'<prosody[^>]*>.*?</prosody>'
        style_pattern = r'\[(conversational|professional|storytelling|narrator|dramatic)\]'
        
        emotion_tags = len(re.findall(emotion_pattern, tagged_script, re.IGNORECASE))
        pause_tags = len(re.findall(pause_pattern, tagged_script, re.IGNORECASE))
        prosody_tags = len(re.findall(prosody_pattern, tagged_script, re.IGNORECASE))
        style_tags = len(re.findall(style_pattern, tagged_script, re.IGNORECASE))
        
        total_tags = emotion_tags + pause_tags + prosody_tags + style_tags
        original_words = len(original_script.split())
        tag_density = total_tags / original_words if original_words > 0 else 0
        
        return {
            "total_tags": total_tags,
            "emotion_tags": emotion_tags,
            "pause_tags": pause_tags,
            "prosody_tags": prosody_tags,
            "style_tags": style_tags,
            "original_words": original_words,
            "tag_density": f"{tag_density:.3f}",
            "tags_per_100_words": f"{(total_tags / original_words * 100):.1f}" if original_words > 0 else "0"
        }

def load_config(config_path: str = "./podcast_config.yaml"):
    """載入配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def embed_tags_with_llm(script_dir: str, config_path: str = "./podcast_config.yaml") -> Optional[str]:
    """
    主要功能：為腳本嵌入 LLM 生成的標籤
    
    Args:
        script_dir: 原始腳本目錄路徑
        config_path: 配置文件路徑
        
    Returns:
        帶標籤腳本的輸出目錄路徑，失敗時返回 None
    """
    
    print("=" * 60)
    print("🏷️ LLM 智能標籤嵌入")
    print("=" * 60)
    
    try:
        # 載入配置
        config = load_config(config_path)
        
        # 檢查標籤嵌入是否啟用
        if not config.get('tag_embedding', {}).get('enabled', False):
            print("⚠️ 標籤嵌入功能未啟用，跳過此步驟")
            return script_dir  # 返回原始腳本目錄
        
        # 讀取原始腳本
        script_path = Path(script_dir)
        script_file = script_path / "podcast_script.txt"
        metadata_file = script_path / "metadata.json"
        
        if not script_file.exists():
            print(f"❌ 找不到腳本檔案: {script_file}")
            return None
        
        if not metadata_file.exists():
            print(f"❌ 找不到元數據檔案: {metadata_file}")
            return None
        
        # 讀取腳本內容和元數據
        with open(script_file, 'r', encoding='utf-8') as f:
            original_script = f.read()
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        english_level = metadata.get('english_level', 'B1')
        
        print(f"📝 原始腳本: {len(original_script.split())} 字")
        print(f"🎯 等級設定: {english_level}")
        
        # 初始化標籤嵌入引擎
        engine = TagEmbeddingEngine(config, english_level)
        
        print(f"🏷️ 標籤策略: {engine.tag_config.get('density', 'moderate')} 密度")
        print(f"🎭 情感範圍: {', '.join(engine.tag_config.get('emotion_range', ['conversational']))}")
        
        # 執行標籤嵌入
        tagged_script = engine.embed_tags_with_llm(original_script)
        
        # 後處理標籤
        print("🔧 後處理標籤格式...")
        final_script = engine.post_process_tags(tagged_script)
        
        # 計算統計
        tag_stats = engine.calculate_tag_statistics(original_script, final_script)
        
        # 創建輸出目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"./output/tagged_scripts/tagged_{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存帶標籤腳本
        tagged_script_file = output_dir / "podcast_script_tagged.txt"
        tagged_script_file.write_text(final_script, encoding='utf-8')
        
        # 保存原始腳本備份
        original_backup = output_dir / "original_script.txt"
        original_backup.write_text(original_script, encoding='utf-8')
        
        # 更新元數據
        enhanced_metadata = metadata.copy()
        enhanced_metadata.update({
            "tag_embedding": {
                "enabled": True,
                "models": {
                    "analysis": engine.analysis_model_name,
                    "tagging": engine.tagging_model_name
                },
                "english_level": english_level,
                "tag_strategy": engine.tag_config,
                "statistics": tag_stats,
                "timestamp": timestamp
            },
            "tagged_script_file": str(tagged_script_file),
            "original_script_backup": str(original_backup),
            "original_script_dir": str(script_dir)
        })
        
        # 保存標籤元數據
        tag_metadata_file = output_dir / "tag_metadata.json"
        tag_metadata_file.write_text(json.dumps(enhanced_metadata, indent=2), encoding='utf-8')
        
        # 顯示結果
        print("\n" + "=" * 60)
        print("✅ 標籤嵌入完成！")
        print(f"📁 輸出目錄: {output_dir}")
        print(f"📝 帶標籤腳本: {tagged_script_file.name}")
        print(f"📊 標籤統計:")
        print(f"   - 總標籤數: {tag_stats['total_tags']}")
        print(f"   - 情感標籤: {tag_stats['emotion_tags']}")
        print(f"   - 停頓標籤: {tag_stats['pause_tags']}")
        print(f"   - 語調標籤: {tag_stats['prosody_tags']}")
        print(f"   - 風格標籤: {tag_stats['style_tags']}")
        print(f"   - 標籤密度: 每100字 {tag_stats['tags_per_100_words']} 個標籤")
        print("=" * 60)
        
        return str(output_dir)
        
    except Exception as e:
        print(f"❌ 標籤嵌入失敗: {e}")
        return None

def main():
    """主程式入口，用於測試"""
    if len(sys.argv) < 2:
        print("用法: python embed_tags.py <script_directory> [config_path]")
        sys.exit(1)
    
    script_dir = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else "./podcast_config.yaml"
    
    result = embed_tags_with_llm(script_dir, config_path)
    if result:
        print(f"\n💡 下一步：執行 python generate_audio.py {result}")
    else:
        print("\n❌ 標籤嵌入失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()