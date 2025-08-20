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
  source: "你的文章.txt"  # 或 URL、PDF、YouTube 連結
  type: "auto"            # 自動檢測類型

basic:
  english_level: "B2"     # A1-C2
  target_minutes: 3       # 目標長度（分鐘）
```

### 4. 生成播客

#### 🔧 開發模式（推薦）
每步確認，可隨時中斷：
```bash
python podcast_workflow.py --mode dev
```

#### ⚡ 生產模式
一鍵完成所有步驟：
```bash
python podcast_workflow.py --mode prod
```

## 📁 專案結構

```
podcastfy_test/
├── 📝 核心腳本
│   ├── generate_script.py          # 生成腳本
│   ├── generate_audio.py           # 生成音頻
│   └── podcast_workflow.py         # 工作流控制器
│
├── ⚙️ 配置
│   ├── podcast_config.yaml         # 主配置文件
│   └── .env                        # API Keys（私密）
│
├── 📂 輸出
│   └── output/
│       ├── scripts/                # 生成的腳本
│       └── audio/                  # 生成的音頻
│
└── 🗃️ 其他
    ├── test_api.py                 # API 連線測試
    └── archive/                    # 封存的舊檔案

```

## 🎯 使用場景

### 場景1：開發調試
```bash
# 生成腳本，檢查內容
python podcast_workflow.py --mode dev

# 不滿意？調整配置重新生成
vim podcast_config.yaml
python podcast_workflow.py --mode dev
```

### 場景2：批量生產
```bash
# 確定流程後，自動執行
python podcast_workflow.py --mode prod --auto-confirm
```

### 場景3：單獨重做某步驟
```bash
# 只重新生成音頻（保留腳本）
python podcast_workflow.py --mode custom --steps audio \
  --script-dir ./output/scripts/script_20250820_143057
```

## 🎨 配置說明

### 英語等級
- **A1-A2**: 初學者，基礎詞彙
- **B1-B2**: 中級，日常對話
- **C1-C2**: 高級，專業內容

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

## 📝 開發筆記

- 使用拆分架構便於調試和節省 API 成本
- 腳本生成使用 Podcastfy + Gemini API
- 音頻生成使用 Gemini Multi-Speaker TTS
- 所有輸出保存在 `output/` 目錄

## ⚠️ 注意事項

1. **API 成本**: 音頻生成會消耗 API 配額，建議先在開發模式確認腳本
2. **檔案大小**: PDF 和影片可能需要較長處理時間
3. **語言支援**: 目前主要支援英語內容

---

💡 **提示**: 第一次使用建議用 `test_api.py` 測試連線，然後用開發模式熟悉流程。