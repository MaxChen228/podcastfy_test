#!/bin/bash

# Podcastfy 測試環境設置腳本
set -e

echo "🎙️ Podcastfy 測試環境設置"
echo "=========================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 Python 版本
echo -e "\n${YELLOW}檢查 Python 版本...${NC}"
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo -e "${GREEN}✓ Python $python_version 符合要求${NC}"
else
    echo -e "${RED}✗ Python 版本過低，需要 3.9 或以上${NC}"
    exit 1
fi

# 檢查 ffmpeg
echo -e "\n${YELLOW}檢查 ffmpeg...${NC}"
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✓ ffmpeg 已安裝${NC}"
else
    echo -e "${RED}✗ ffmpeg 未安裝${NC}"
    echo "請安裝 ffmpeg:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install ffmpeg"
    else
        echo "  sudo apt-get install ffmpeg"
    fi
    exit 1
fi

# 建立虛擬環境
echo -e "\n${YELLOW}建立虛擬環境...${NC}"
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo -e "${GREEN}✓ 虛擬環境建立成功 (Python 3.11)${NC}"
else
    echo -e "${GREEN}✓ 虛擬環境已存在${NC}"
fi

# 啟動虛擬環境
source venv/bin/activate

# 升級 pip
echo -e "\n${YELLOW}升級 pip...${NC}"
pip install --upgrade pip -q

# 安裝依賴
echo -e "\n${YELLOW}安裝 Podcastfy 和依賴...${NC}"
pip install -r requirements.txt

# 檢查安裝結果
echo -e "\n${YELLOW}驗證安裝...${NC}"
python3 -c "import podcastfy; print('✓ Podcastfy 版本:', podcastfy.__version__ if hasattr(podcastfy, '__version__') else 'OK')"

# 檢查 API Keys
echo -e "\n${YELLOW}檢查 API Keys...${NC}"
if [ -f ".env" ]; then
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        echo -e "${GREEN}✓ OpenAI API Key 已設置${NC}"
    else
        echo -e "${YELLOW}⚠ OpenAI API Key 未設置或無效${NC}"
    fi
else
    echo -e "${RED}✗ .env 檔案不存在${NC}"
fi

# 建立必要目錄
echo -e "\n${YELLOW}建立輸出目錄...${NC}"
mkdir -p output
mkdir -p output_advanced
mkdir -p cache
echo -e "${GREEN}✓ 目錄建立完成${NC}"

echo -e "\n${GREEN}========== 設置完成 ==========${NC}"
echo -e "執行測試:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}  # 啟動虛擬環境"
echo -e "  ${YELLOW}python test_basic.py${NC}       # 基礎測試"
echo -e "  ${YELLOW}python test_advanced.py${NC}    # 進階測試"
echo ""