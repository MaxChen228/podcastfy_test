#!/usr/bin/env python3
"""
Step 2: 經濟高效的規則式標籤嵌入引擎
使用智能規則檢測停頓點和語音效果，無需 LLM 成本
"""

import os
import sys
import json
import yaml
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RuleBasedTagEngine:
    """經濟高效的規則式標籤嵌入引擎"""
    
    def __init__(self, config: Dict[Any, Any], english_level: str):
        """
        初始化規則式標籤嵌入引擎
        
        Args:
            config: 播客配置字典
            english_level: 英語等級 (A1-C2)
        """
        self.config = config
        self.english_level = english_level
        self.level_config = config['level_configs'][english_level]
        self.tag_config = self.level_config.get('tag_embedding', {})
        
        # 初始化規則引擎配置
        self._init_pause_rules()
        self._init_voice_effects()
        
        print(f"🚀 規則式標籤引擎初始化完成 - 等級: {english_level}")
    
    def _init_pause_rules(self):
        """初始化停頓規則配置"""
        self.pause_strategies = {
            'A1': {
                'density': 0.15,  # 15%的標點符號加停頓 - 大幅降低
                'pause_mapping': {
                    '.': '[PAUSE=1.5s]',
                    '?': '[PAUSE=1.5s]',
                    '!': '[PAUSE=1s]',
                    # 移除逗號等小停頓
                }
            },
            'A2': {
                'density': 0.12,  # 12%
                'pause_mapping': {
                    '.': '[PAUSE=1s]',
                    '?': '[PAUSE=1.2s]',
                    '!': '[PAUSE=800ms]',
                }
            },
            'B1': {
                'density': 0.10,  # 10%
                'pause_mapping': {
                    '.': '[PAUSE=800ms]',
                    '?': '[PAUSE=1s]',
                    '!': '[PAUSE=600ms]',
                }
            },
            'B2': {
                'density': 0.08,  # 8%
                'pause_mapping': {
                    '.': '[PAUSE=600ms]',
                    '?': '[PAUSE=800ms]',
                    '!': '[PAUSE=500ms]',
                }
            },
            'C1': {
                'density': 0.06,  # 6%
                'pause_mapping': {
                    '.': '[PAUSE=500ms]',
                    '?': '[PAUSE=600ms]',
                    '!': '[PAUSE=400ms]',
                }
            },
            'C2': {
                'density': 0.05, # 5% - 最少停頓
                'pause_mapping': {
                    '.': '[PAUSE=400ms]',
                    '?': '[PAUSE=500ms]',
                    '!': '[PAUSE=300ms]',
                }
            }
        }
    
    def _init_voice_effects(self):
        """初始化語音效果檢測規則"""
        self.voice_effects = {
            # 笑聲系列
            'laugh_triggers': {
                'keywords': ['haha', 'hehe', 'lol', 'funny', 'hilarious', 'joke', 'laugh'],
                'effects': ['[laughing]', '[chuckling]', '[giggles]']
            },
            'amused_triggers': {
                'keywords': ['amusing', 'witty', 'clever', 'humor'],
                'effects': ['[amused]', '[chuckling]']
            },
            
            # 情緒效果
            'sigh_triggers': {
                'keywords': ['unfortunately', 'sadly', 'however', 'sigh'],
                'effects': ['[sighing]']
            },
            'gasp_triggers': {
                'keywords': ['suddenly', 'shocking', 'incredible', 'wow', 'amazing'],
                'effects': ['[gasping]']
            },
            
            # 呼吸音效
            'thinking_triggers': {
                'keywords': ['um', 'uh', 'well...', 'let me think'],
                'effects': ['[breathing]']
            },
            'cough_triggers': {
                'keywords': ['excuse me', 'sorry', 'pardon'],
                'effects': ['[coughing]']
            }
        }
    
    def analyze_dialogue_context(self, script_content: str) -> Dict[str, Any]:
        """使用規則分析對話內容，識別停頓點和語音效果"""
        
        # 基本統計
        word_count = len(script_content.split())
        sentence_count = len(re.findall(r'[.!?]', script_content))
        
        # 簡單的規則分析
        analysis = {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": word_count / max(sentence_count, 1),
            "pause_points": self._identify_pause_points(script_content),
            "voice_effects": self._identify_voice_effects(script_content)
        }
        
        print(f"📊 內容分析: {word_count}字, {sentence_count}句, 平均{analysis['avg_sentence_length']:.1f}字/句")
        print(f"⏸️ 檢測到 {len(analysis['pause_points'])}個停頓點")
        print(f"🎭 檢測到 {len(analysis['voice_effects'])}個語音效果")
        
        return analysis
    
    def _identify_pause_points(self, text: str) -> List[Dict[str, Any]]:
        """識別停頓點"""
        strategy = self.pause_strategies[self.english_level]
        pause_points = []
        
        # 找到所有標點符號位置
        for punct, pause_tag in strategy['pause_mapping'].items():
            positions = [m.start() for m in re.finditer(re.escape(punct), text)]
            for pos in positions:
                # 根據密度決定是否新增停頓
                if len(pause_points) == 0 or pos > pause_points[-1]['position'] + 10:  # 避免太密集
                    if len(pause_points) / max(len(text.split()), 1) < strategy['density']:
                        pause_points.append({
                            'position': pos,
                            'punctuation': punct,
                            'pause_tag': pause_tag
                        })
        
        return sorted(pause_points, key=lambda x: x['position'])
    
    def _identify_voice_effects(self, text: str) -> List[Dict[str, Any]]:
        """識別語音效果"""
        voice_effects = []
        text_lower = text.lower()
        
        for effect_type, config in self.voice_effects.items():
            for keyword in config['keywords']:
                if keyword in text_lower:
                    # 找到關鍵詞的位置
                    positions = [m.start() for m in re.finditer(re.escape(keyword), text_lower)]
                    for pos in positions:
                        # 隨機選擇一個效果
                        import random
                        effect = random.choice(config['effects'])
                        voice_effects.append({
                            'position': pos,
                            'keyword': keyword,
                            'effect': effect,
                            'type': effect_type
                        })
        
        return sorted(voice_effects, key=lambda x: x['position'])
    
    def generate_statistics(self, original_content: str, tagged_content: str) -> Dict[str, Any]:
        """統計標籤嵌入結果"""
        
        # 統計標籤數量
        pause_count = len(re.findall(r'\[PAUSE=\w+\]', tagged_content))
        voice_effect_count = len(re.findall(r'\[(?:laughing|chuckling|sighing|gasping|breathing|coughing|sniffing|groaning|giggles|amused|crying|sobbing|panting|yawning)\]', tagged_content))
        
        original_words = len(original_content.split())
        
        return {
            'total_tags': pause_count + voice_effect_count,
            'pause_tags': pause_count,
            'voice_effect_tags': voice_effect_count,
            'original_words': original_words,
            'tag_density': f"{((pause_count + voice_effect_count) / original_words * 100):.1f}%",
            'tags_per_100_words': f"{(pause_count + voice_effect_count) / original_words * 100:.1f}"
        }
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
    
    def embed_tags_with_rules(self, script_content: str) -> str:
        """使用規則引擎進行標籤嵌入，無需 LLM 成本"""
        
        print("🚀 分析對話內容...")
        analysis = self.analyze_dialogue_context(script_content)
        
        print("⏸️ 新增停頓標籤...")
        tagged_content = self._add_pause_tags(script_content, analysis['pause_points'])
        
        print("🎭 新增語音效果...")
        tagged_content = self._add_voice_effects(tagged_content, analysis['voice_effects'])
        
        print("✨ 標籤嵌入完成!")
            
        return tagged_content
    
    def _add_pause_tags(self, content: str, pause_points: List[Dict[str, Any]]) -> str:
        """在指定位置新增停頓標籤"""
        result = content
        
        # 從後向前處理，避免位置偏移
        for pause_info in reversed(pause_points):
            pos = pause_info['position']
            punct = pause_info['punctuation']
            pause_tag = pause_info['pause_tag']
            
            # 在標點符號後加入停頓
            if pos < len(result) and result[pos] == punct:
                result = result[:pos+1] + f" {pause_tag}" + result[pos+1:]
        
        return result
    
    def _add_voice_effects(self, content: str, voice_effects: List[Dict[str, Any]]) -> str:
        """在關鍵詞附近新增語音效果"""
        result = content
        
        # 從後向前處理，避免位置偏移
        for effect_info in reversed(voice_effects):
            pos = effect_info['position']
            effect = effect_info['effect']
            keyword = effect_info['keyword']
            
            # 在關鍵詞前加入語音效果
            if pos < len(result):
                # 找到關鍵詞的結束位置
                end_pos = pos + len(keyword)
                if end_pos <= len(result):
                    result = result[:pos] + f"{effect} " + result[pos:]
        
        return result
    
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

def embed_tags_with_rules(script_dir: str, config_path: str = "./podcast_config.yaml") -> Optional[str]:
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
        
        # 初始化規則式標籤引擎
        engine = RuleBasedTagEngine(config, english_level)
        
        print(f"⏸️ 停頓策略: {engine.pause_strategies[english_level]['density']*100:.0f}% 密度")
        
        # 執行標籤嵌入
        tagged_script = engine.embed_tags_with_rules(original_script)
        
        # 統計結果
        print("📊 統計標籤結果...")
        tag_stats = engine.generate_statistics(original_script, tagged_script)
        
        final_script = tagged_script
        
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
                "engine_type": "rule_based",
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
        print(f"   - 停頓標籤: {tag_stats['pause_tags']}")
        print(f"   - 語音效果: {tag_stats['voice_effect_tags']}")
        print(f"   - 標籤密度: {tag_stats['tag_density']}")
        print(f"   - 每100字 {tag_stats['tags_per_100_words']} 個標籤")
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
    
    result = embed_tags_with_rules(script_dir, config_path)
    if result:
        print(f"\n💡 下一步：執行 python generate_audio.py {result}")
    else:
        print("\n❌ 標籤嵌入失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()