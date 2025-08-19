# 🎙️ Podcastfy 測試環境

這是一個獨立的測試環境，用於驗證 Podcastfy 是否能正常運作，以及測試與現有系統的整合。

## 📋 前置需求

- Python 3.10 或以上
- ffmpeg（音頻處理）
- OpenAI API Key

## 🚀 快速開始

### 1. 設置環境

```bash
# 執行自動設置腳本
./setup.sh

# 或手動設置
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. 配置 API Keys

編輯 `.env` 檔案，確保已設置：
```
OPENAI_API_KEY=your-api-key-here
```

### 3. 執行測試

```bash
# 啟動虛擬環境
source venv/bin/activate

# 基礎功能測試
python test_basic.py

# 進階功能測試
python test_advanced.py

# 系統整合測試
python test_integration.py
```

## 📁 檔案結構

```
podcastfy_test/
├── test_basic.py        # 基礎功能測試
├── test_advanced.py     # 進階功能測試
├── test_integration.py  # 整合測試
├── setup.sh            # 環境設置腳本
├── requirements.txt    # Python 依賴
├── .env               # 環境變數配置
├── output/            # 基礎測試輸出
├── output_advanced/   # 進階測試輸出
└── cache/            # 緩存目錄
```

## 🧪 測試內容

### 基礎測試 (test_basic.py)
- ✅ Podcastfy 導入測試
- ✅ 簡單文本轉播客
- ✅ URL 內容轉播客
- ✅ 中文內容處理

### 進階測試 (test_advanced.py)
- ✅ 多人對話生成
- ✅ 自定義提示詞模板
- ✅ 不同 TTS 提供商測試
- ✅ 多種內容格式支援

### 整合測試 (test_integration.py)
- ✅ 與 ContentFetcher 整合
- ✅ 與記憶系統整合
- ✅ 性能對比分析
- ✅ 錯誤處理機制

## 🔧 常見問題

### 1. ImportError: No module named 'podcastfy'
```bash
pip install podcastfy --upgrade
```

### 2. ffmpeg not found
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

### 3. OpenAI API 錯誤
- 檢查 API Key 是否正確
- 確認帳戶有足夠額度
- 檢查網路連接

## 🎯 測試結果預期

成功執行後，您應該看到：

1. **基礎測試**：
   - 生成簡單的播客音頻檔案
   - 中文內容正確處理

2. **進階測試**：
   - 多人對話播客生成
   - 不同 TTS 服務測試結果

3. **整合測試**：
   - 與現有系統無縫整合
   - 性能對比數據

## 📊 性能基準

| 測試項目 | 預期時間 | 備註 |
|---------|---------|------|
| 簡單文本 (200字) | < 5秒 | 不含 TTS |
| 中文內容 (500字) | < 10秒 | 含腳本優化 |
| 多人對話 (800字) | < 15秒 | 3個角色 |

## 🔄 下一步

測試成功後，可以：

1. **整合到主專案**：
   ```python
   # 在主專案中使用
   from src.podcast_factory import PodcastFactory
   ```

2. **自定義配置**：
   - 調整對話風格
   - 配置多語言支援
   - 設定不同 TTS 提供商

3. **優化性能**：
   - 實現響應緩存
   - 使用異步處理
   - 配置本地 LLM

## 📝 注意事項

- 測試會產生 OpenAI API 費用（約 $0.01-0.05）
- 首次執行需要下載模型，可能較慢
- 生成的音頻檔案會保存在 output/ 目錄

## 🐛 問題回報

如遇到問題，請檢查：
1. Python 版本是否 >= 3.10
2. 所有依賴是否正確安裝
3. API Key 是否有效
4. 網路連接是否正常

---

**提示**：執行 `./setup.sh` 會自動檢查環境並安裝所需依賴。