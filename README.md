# 🎙️ Podcastfy 播客生成系統

一個模組化的播客生成工具，使用 AI 將各種內容（文章、PDF、網頁、YouTube）轉換成自然的對話式播客。

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設置 API Key
```bash
# 複製 .env 範例並填入你的 API Key
echo "GEMINI_API_KEY=你的_API_KEY" > .env
```

### 3. 設定內容源
編輯 `podcast_config.yaml`：
```yaml
input:
  sources:                  # 支援多資料來源
    - "你的文章.txt"        # 本地文件
    - "https://example.com" # 網頁 URL
    - "youtube_url"         # YouTube 影片
  type: "multi"             # multi/auto/single

basic:
  english_level: "A1"       # A1(探索者)-C2(大師)
  podcast_length: "medium"  # short/medium/long/extra-long
```

### 4. 生成播客

#### 🔧 開發模式（推薦）
三步驟分離，每步確認：
```bash
python podcast_workflow.py --mode dev
```

#### ⚡ 生產模式
一鍵完成三步驟流程：
```bash
python podcast_workflow.py --mode prod
```

#### 🎯 自訂模式
選擇性執行特定步驟：
```bash
# 僅生成腳本
python podcast_workflow.py --mode custom --steps script

# 僅標籤嵌入（需要已有腳本）
python podcast_workflow.py --mode custom --steps tags --script-dir ./output/scripts/script_xxx

# 完整三步驟
python podcast_workflow.py --mode custom --steps script tags audio
```

## 📁 專案結構

```
podcastfy_test/
├── 📝 核心腳本（三步驟工作流程）
│   ├── generate_script.py          # Step 1: 生成腳本
│   ├── embed_tags.py               # Step 2: LLM智能標籤嵌入
│   ├── generate_audio.py           # Step 3: 生成音頻
│   └── podcast_workflow.py         # 工作流控制器
│
├── ⚙️ 配置
│   ├── podcast_config.yaml         # 主配置文件（含標籤嵌入配置）
│   └── .env                        # API Keys（私密）
│
├── 📂 輸出
│   └── output/
│       ├── scripts/                # Step 1: 原始腳本
│       ├── tagged_scripts/         # Step 2: 帶標籤腳本
│       └── audio/                  # Step 3: 最終音頻
│
└── 🗃️ 其他
    ├── test_api.py                 # API 連線測試
    ├── LLM標籤嵌入系統實施計劃.md   # 技術實施文檔
    ├── gemini tts 標籤.md          # 標籤系統完整指南
    └── archive/                    # 封存的舊檔案
```

## 🎯 三步驟工作流程

### Step 1: 腳本生成 📝
```bash
# 使用 Podcastfy + Gemini API 生成自然對話腳本
python generate_script.py
# 或通過工作流程
python podcast_workflow.py --mode custom --steps script
```

### Step 2: LLM 智能標籤嵌入 🏷️
```bash
# 使用 LLM 分析內容，智能嵌入 SSML 和情感標籤
python embed_tags.py <script_directory>
# 或通過工作流程
python podcast_workflow.py --mode custom --steps tags --script-dir <directory>
```

### Step 3: 音頻生成 🎵
```bash
# 使用 Gemini Multi-Speaker TTS 生成最終音頻
python generate_audio.py <tagged_script_directory>
# 或通過工作流程
python podcast_workflow.py --mode custom --steps audio --script-dir <directory>
```

## 🎯 使用場景

### 場景1：開發調試
```bash
# 三步驟分離，逐步檢查和調整
python podcast_workflow.py --mode dev

# 不滿意腳本？調整配置重新生成
vim podcast_config.yaml
python podcast_workflow.py --mode custom --steps script

# 標籤效果不好？重新嵌入
python podcast_workflow.py --mode custom --steps tags --script-dir <directory>
```

### 場景2：批量生產
```bash
# 確定流程後，自動執行三步驟
python podcast_workflow.py --mode prod --auto-confirm
```

### 場景3：單獨重做某步驟
```bash
# 只重新嵌入標籤
python podcast_workflow.py --mode custom --steps tags --script-dir ./output/scripts/script_xxx

# 只重新生成音頻（使用帶標籤腳本）
python podcast_workflow.py --mode custom --steps audio --script-dir ./output/tagged_scripts/tagged_xxx
```

## 🎨 配置說明

### 英語等級（教學導向設計）
- **A1 英語老師**: 明確語言教學，80% 語言學習 + 20% 內容討論
- **A2 語言引導者**: 自然語言指導，60% 語言學習 + 40% 內容討論  
- **B1 對話導師**: 內容中穿插語言教導，40% 語言學習 + 60% 內容討論
- **B2 分析者**: 深入對話偶爾語言提點，20% 語言學習 + 80% 內容討論
- **C1 智者**: 專注內容分析，5% 語言提點 + 95% 內容討論
- **C2 大師**: 純內容導向，100% 內容討論

### 時長建議
- **1-2 分鐘**: 快速概覽
- **3-5 分鐘**: 標準討論
- **5-10 分鐘**: 深入分析

### 語音選擇
在 `podcast_config.yaml` 中設定：
```yaml
voices:
  host_voice: "Kore"    # 溫和女聲
  expert_voice: "Puck"  # 活潑男聲
```

可選語音：
- **Kore**: 溫和親切的女聲
- **Puck**: 活潑年輕的男聲
- **Charon**: 沈穩權威的男聲
- **Fenrir**: 專業清晰的男聲
- **Aoede**: 優雅文藝的女聲

## 🔍 常見問題

### Q: API Key 無效？
```bash
# 測試 API 連線
python test_api.py
```

### Q: 腳本太長/太短？
調整 `podcast_config.yaml` 中的 `target_minutes`

### Q: 想要不同的對話風格？
修改 `style_instructions` 和 `conversation_style`

## 📊 支援的輸入格式

- 📄 文本文件 (.txt, .md)
- 📑 PDF 文檔
- 🌐 網頁文章
- 📺 YouTube 影片

## 🛠️ 進階配置

如需手動控制長度參數，在 `podcast_config.yaml` 中設定：
```yaml
advanced:
  word_count: 500        # 覆蓋自動計算
  max_num_chunks: 6      # 對話輪次
  min_chunk_size: 600    # 最小塊大小
```

## 🆕 LLM 智能標籤嵌入系統

### 核心特色
- **智能分析**：LLM 自動分析對話情境和情緒
- **等級適配**：根據 A1-C2 英語等級自動調整標籤策略
- **豐富標籤**：支援 50+ 種情感和語音效果標籤
- **品質提升**：顯著改善 TTS 音頻的自然度和表現力

### 配置標籤嵌入
```yaml
tag_embedding:
  enabled: true                    # 開啟標籤嵌入功能
  models:
    analysis_model: "gemini-2.5-flash"  # 快速分析模型
    tagging_model: "gemini-2.5-pro"     # 精細標記模型
```

### 等級特定策略
- **A1-A2**: 溫和情感 + 充分暫停，適合初學者
- **B1-B2**: 平衡標籤使用，自然對話節奏  
- **C1-C2**: 豐富表達 + 專業語調控制

## 📝 開發筆記

- **三步驟架構**：腳本生成 → 標籤嵌入 → 音頻生成
- **腳本生成**：使用 Podcastfy + Gemini API
- **標籤嵌入**：使用 LLM 智能分析和標記
- **音頻生成**：使用 Gemini Multi-Speaker TTS
- **模組化設計**：每步可獨立執行，便於調試和成本控制

## ⚠️ 注意事項

1. **API 成本**: 標籤嵌入和音頻生成會消耗 API 配額，建議使用開發模式逐步確認
2. **標籤功能**: 預設關閉標籤嵌入，需在 `podcast_config.yaml` 中設定 `tag_embedding.enabled: true`
3. **檔案大小**: PDF 和影片可能需要較長處理時間
4. **語言支援**: 目前主要支援英語內容，標籤系統針對英語優化

---

## 🚀 **一鍵啟動**

```bash
./run.sh
```

這個腳本提供直觀的選單，讓你輕鬆選擇：
- 🔧 **開發模式**：逐步執行，每步確認
- ⚡ **自動化模式**：一鍵完成所有步驟  
- 🎯 **自訂模式**：只執行特定步驟
- 🛠️ **工具功能**：API 測試、配置說明

💡 **提示**: 第一次使用建議選擇「開發模式」熟悉流程，或先查看「配置說明」了解等級設置。

## 📚 相關文檔

- 📖 **[快速開始指南.md](快速開始指南.md)** - 完整三步驟使用教程
- ⚙️ **[configSetting.md](configSetting.md)** - 所有配置參數詳解
- 🏷️ **[gemini tts 標籤.md](gemini tts 標籤.md)** - 標籤系統完整指南  
- 📋 **[LLM標籤嵌入系統實施計劃.md](LLM標籤嵌入系統實施計劃.md)** - 技術實施文檔
- 🔧 **[Gemini Multi-Speaker TTS 完整使用文檔.md](Gemini Multi-Speaker TTS 完整使用文檔.md)** - TTS API 詳細說明