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
        
        # 獲取標籤嵌入配置
        self.tag_embedding_config = config.get('tag_embedding', {})
        self.llm_model = self.tag_embedding_config.get('llm_model', 'gemini-2.0-flash-exp')
        
        # 獲取模型參數
        self.model_params = self.tag_embedding_config.get('model_parameters', {})
        self.content_processing = self.tag_embedding_config.get('content_processing', {})
        self.tag_validation = self.tag_embedding_config.get('tag_validation', {})
        
        # 配置 Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY 環境變量未設置")
        
        genai.configure(api_key=api_key)
        
        # 初始化模型與生成配置
        self.model = genai.GenerativeModel(self.llm_model)
        self.generation_config = genai.types.GenerationConfig(
            temperature=self.model_params.get('temperature', 0.3),
            top_p=self.model_params.get('top_p', 0.8),
            top_k=self.model_params.get('top_k', 40),
            max_output_tokens=self.model_params.get('max_output_tokens', 8192)
        )
    
    def analyze_dialogue_context(self, script_content: str) -> Dict[str, Any]:
        """分析對話內容，識別情境和情緒"""
        
        analysis_prompt = f"""
        請分析以下播客對話腳本的內容和情境：

        {script_content}

        請回答：
        1. 對話的主要情緒氛圍（例如：正面、中性、嚴肅等）
        2. 對話節奏（例如：緩慢、中等、快速）
        3. 主要討論主題的複雜度（例如：基礎、中等、高級）
        4. 建議的主要情感標籤（3-5個）
        5. 建議的停頓位置類型（例如：段落間長停頓、句子間短停頓）

        請以 JSON 格式回答：
        {{
            "mood": "正面/中性/嚴肅",
            "pace": "緩慢/中等/快速", 
            "complexity": "基礎/中等/高級",
            "suggested_emotions": ["emotion1", "emotion2", "emotion3"],
            "pause_strategy": "描述停頓策略"
        }}
        """
        
        try:
            response = self.model.generate_content(
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
        """根據等級配置和內容分析生成 LLM 提示"""
        
        # 獲取等級特定的標籤策略
        density = self.tag_config.get('density', 'moderate')
        emotion_range = self.tag_config.get('emotion_range', ['conversational', 'thoughtful'])
        pause_frequency = self.tag_config.get('pause_frequency', 'moderate')
        prosody_usage = self.tag_config.get('prosody_usage', 'selective')
        primary_style = self.tag_config.get('primary_style', '[conversational]')
        
        # 構建提示模板
        prompt = f"""
你是專業的播客製作助理。請為以下腳本嵌入適當的 Gemini TTS 語音標籤。

=== 等級配置 ===
英語等級: {self.english_level} ({self.level_config['style_name']})
對話風格: {', '.join(self.level_config['conversation_style'])}
語速設定: {self.level_config['pace']}

=== 標籤策略 ===
標籤密度: {density}
情感範圍: {', '.join(emotion_range)}
停頓頻率: {pause_frequency}
語調控制: {prosody_usage}
主要風格: {primary_style}

=== 內容分析 ===
情緒氛圍: {analysis['mood']}
對話節奏: {analysis['pace']}
內容複雜度: {analysis['complexity']}
建議情感: {', '.join(analysis['suggested_emotions'])}

=== 可用標籤參考 ===
基礎情感標籤: [happy], [sad], [excited], [calm], [thoughtful], [curious], [gentle], [confident], [analytical], [professional]

進階情感標籤: [passionate], [amused], [empathetic], [sincere], [surprised], [delighted], [frustrated], [nervous], [proud], [grateful], [relaxed], [serious], [interested], [confused], [hesitating]

情感強度標籤: 
- 開心系列: [happy] → [excited] → [delighted] → [joyful]
- 思考系列: [curious] → [thoughtful] → [analytical] → [insightful]
- 專業系列: [conversational] → [professional] → [authoritative] → [expert]

語音效果標籤: [laughing], [chuckling], [giggles], [sighing], [breathing], [whisper], [dramatic], [gasping], [yawning], [coughing], [sniffing], [groaning]

複合情感標籤: [thoughtfully curious], [analytically engaged], [gently excited], [professionally passionate], [confidently analytical], [warmly supportive]

停頓控制: [PAUSE=1s], [PAUSE=2s], [PAUSE=500ms], [PAUSE=3s], [brief pause], [long pause], [dramatic pause]

語調風格: [conversational], [professional], [storytelling], [narrator], [robotic], [childlike], [sarcastic], [comforting]

音量與強度: [whisper], [soft], [loud], [shout], [gentle], [dramatic], [emphasized], [intense]

語速控制: [slow], [fast], [rushed], [relaxed pace]

=== 標籤嵌入指引 ===
"""

        # 根據等級提供具體指引
        if self.english_level in ['A1', 'A2']:
            prompt += """
A1/A2 等級指引：
- 使用基礎溫和標籤：[gentle], [curious], [supportive], [happy], [thoughtful]
- 充分停頓：在段落間使用 [PAUSE=2s]，句子間使用 [PAUSE=1s]
- 語調控制最小化：偶爾使用 <prosody rate="slow"> 強調重點
- 保持溫和友善的氛圍，避免強烈情感標籤
"""
        elif self.english_level in ['B1', 'B2']:
            prompt += """
B1/B2 等級指引：
- 平衡情感標籤：[thoughtful], [engaged], [analytical], [curious], [confident]
- 適度停頓：[PAUSE=1s] 用於重點，[brief pause] 用於自然節奏
- 選擇性語調控制：使用 <prosody rate="slow/fast"> 和 <prosody pitch="high/low">
- 支援自然對話節奏和適度的情感表達
"""
        else:  # C1, C2
            prompt += """
C1/C2 等級指引：
- 豐富情感表達：[analytical], [insightful], [professional], [sophisticated], [confident]
- 戰略性停頓：[PAUSE=1s] 用於強調，[dramatic pause] 用於重點轉折
- 豐富語調控制：頻繁使用 <prosody> 調節音調、語速、音量
- 支援專業論述風格和複雜情感表達
"""

        prompt += f"""

=== 標籤嵌入規則 ===
1. 在適當位置嵌入標籤，不要破壞原始對話結構
2. 標籤應該增強自然表達，不要過度使用
3. 保持 <Person1> 和 <Person2> 的格式標記
4. 可以在句子開始、中間或結尾添加標籤
5. 停頓標籤優先放在標點符號附近
6. 根據 {density} 密度控制標籤使用頻率

=== 輸出格式 ===
請輸出完整的帶標籤腳本，保持原有的對話結構。

原始腳本：
{script_content}

帶標籤腳本：
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
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            print(f"🔍 LLM 回應狀態: {response}")
            
            if not response or not response.text:
                print("❌ LLM 沒有返回內容")
                return script_content
            
            tagged_content = response.text.strip()
            print(f"📝 LLM 回應長度: {len(tagged_content)} 字符")
            
            if len(tagged_content) < 100:
                print(f"⚠️ 回應內容異常短: {tagged_content[:200]}...")
                return script_content
            
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
                print("🔧 移除了 markdown 格式標記")
            
            return tagged_content
            
        except Exception as e:
            print(f"❌ LLM 標籤嵌入失敗: {e}")
            import traceback
            print(f"🔍 詳細錯誤: {traceback.format_exc()}")
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
                "llm_model": engine.llm_model,
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