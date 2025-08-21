# Gemini TTS 完整 [] 標籤系統指南

## 🎭 基本情感標籤

### 正面情感
```
[happy]        - 開心的
[excited]      - 興奮的
[joyful]       - 快樂的
[satisfied]    - 滿足的
[delighted]    - 愉快的
[proud]        - 驕傲的
[grateful]     - 感激的
[relaxed]      - 放鬆的
[confident]    - 自信的
[amused]       - 被逗樂的
```

### 負面情感
```
[sad]          - 悲傷的
[angry]        - 生氣的
[frustrated]   - 沮喪的
[disappointed] - 失望的
[worried]      - 擔心的
[nervous]      - 緊張的
[scared]       - 害怕的
[upset]        - 不安的
[depressed]    - 抑鬱的
[embarrassed]  - 尷尬的
```

### 中性/複雜情感
```
[serious]      - 嚴肅的
[curious]      - 好奇的
[interested]   - 感興趣的
[confused]     - 困惑的
[surprised]    - 驚訝的
[empathetic]   - 同理心的
[sincere]      - 真誠的
[hesitating]   - 猶豫的
[yielding]     - 順從的
[awkward]      - 尷尬的
```

## 🔥 進階情感強度標籤

### 憤怒系列 (遞增強度)
```
[angry]        - 生氣
[frustrated]   - 沮喪
[furious]      - 憤怒
[panicked]     - 恐慌
[scornful]     - 輕蔑
[disdainful]   - 鄙視
```

### 悲傷系列 (遞增強度)
```
[sad]          - 悲傷
[worried]      - 擔心
[depressed]    - 抑鬱
[painful]      - 痛苦
[hysterical]   - 歇斯底里
```

### 開心系列 (遞增強度)
```
[happy]        - 開心
[excited]      - 興奮
[delighted]    - 愉快
[joyful]       - 快樂
```

## 🎵 語音效果標籤

### 笑聲系列
```
[laughing]       - 笑聲
[chuckling]      - 輕笑
[laughs harder]  - 更大聲的笑
[giggles]        - 咯咯笑
[amused]         - 被逗樂
```

### 哭泣系列
```
[crying]         - 哭泣
[sobbing]        - 抽泣
[crying loudly]  - 大聲哭泣
```

### 呼吸音效
```
[sighing]        - 嘆氣
[panting]        - 喘氣
[gasping]        - 喘息
[breathing]      - 呼吸聲
[yawning]        - 打哈欠
[coughing]       - 咳嗽
[sniffing]       - 抽鼻子
[groaning]       - 呻吟
```

### ❌ 不支援的環境音效
```
[crowd laughing]     - 群眾笑聲 ❌
[audience applause]  - 觀眾掌聲 ❌
[background music]   - 背景音樂 ❌
```

## 🗣️ 語調風格標籤

### 說話風格
```
[conversational]  - 對話式
[professional]    - 專業的
[formal]          - 正式的
[informal]        - 非正式的
[storytelling]    - 說故事的
[narrator]        - 旁白者
[robotic]         - 機器人的
[childlike]       - 孩子氣的
```

### 語調特色
```
[sarcastic]       - 諷刺的
[sneering]        - 冷笑的
[comforting]      - 安慰的
[conciliative]    - 和解的
[disapproving]    - 不贊成的
[denying]         - 否認的
[astonished]      - 震驚的
```

## 🔊 音量與強度標籤

### 音量控制
```
[whisper]         - 耳語
[soft]            - 輕柔
[loud]            - 大聲
[shout]           - 大喊
```

### 強調程度
```
[gentle]          - 溫和的
[dramatic]        - 戲劇性的
[emphasized]      - 強調的
[intense]         - 強烈的
[calm]            - 冷靜的
```

## ⏸️ 停頓控制標籤

### 時間停頓
```
[PAUSE=1s]        - 1秒停頓
[PAUSE=2s]        - 2秒停頓
[PAUSE=500ms]     - 500毫秒停頓
[PAUSE=3s]        - 3秒停頓
```

### 停頓強度
```
[brief pause]     - 短暫停頓
[long pause]      - 長停頓
[dramatic pause]  - 戲劇性停頓
```

## 🌍 特殊控制標籤

### 語速控制
```
[slow]            - 慢速
[fast]            - 快速
[rushed]          - 匆忙的
[relaxed pace]    - 放鬆的節奏
```

### 口音和語言風格
```
[british accent]  - 英式口音
[american accent] - 美式口音
[formal tone]     - 正式語調
[casual tone]     - 隨意語調
```

## 💡 標籤使用技巧

### 1. 單一標籤使用
```
[happy] Hello everyone! Welcome to our show today.
[whisper] I have a secret to tell you.
[dramatic] The end is near...
```

### 2. 多標籤組合
```
[excited] [fast] I can't believe we won the lottery!
[sad] [slow] [PAUSE=2s] I guess this is goodbye.
[dramatic] [PAUSE=1s] [whisper] The truth will be revealed.
```

### 3. 混合 SSML 使用
```
[angry] <break time="1s"/> I've had enough of this!
[happy] <prosody rate="fast">This is the best day ever!</prosody>
[whisper] <prosody volume="soft">Can you hear me?</prosody>
```

## ⚠️ 使用注意事項

### 最佳實踐
- **Pro 模型更佳**：Gemini 2.5 Pro 在細緻標籤解釋方面明顯優於 Flash
- **避免過度使用**：在長文本中避免使用過多標籤，可能導致標籤被朗讀出來
- **分段處理**：複雜內容建議分成較小段落分別生成
- **測試優先**：在 AI Studio 中測試效果後再集成到應用

### 標籤組合規則
1. **情感 + 音量**：`[happy] [loud]` 開心大聲
2. **情感 + 停頓**：`[sad] [PAUSE=2s]` 悲傷停頓
3. **風格 + 語速**：`[dramatic] [slow]` 戲劇性慢速
4. **效果 + 情感**：`[laughing] [happy]` 開心笑聲

## 🎯 實際應用範例

### Podcast 對話
```
Speaker A: [conversational] Welcome back to Tech Talk! 
[PAUSE=1s] [excited] Today we have an amazing guest.

Speaker B: [professional] [calm] Thanks for having me. 
[happy] I'm thrilled to be here.
```

### 故事旁白
```
[narrator] [dramatic] Once upon a time, in a land far away...
[PAUSE=2s] [whisper] [mysterious] Something was stirring in the darkness.
[scared] [fast] Suddenly, a loud crash echoed through the forest!
```

### 客服對話
```
[professional] [empathetic] I understand your frustration, 
[PAUSE=1s] [comforting] and I'm here to help you resolve this issue.
```

這套標籤系統為 Gemini TTS 提供了前所未有的表達控制能力，讓 AI 語音更加自然和富有情感。