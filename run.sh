#!/bin/bash

# 🎙️ Podcastfy 播客生成系統 - 快速執行腳本
# 讓你輕鬆選擇要執行的操作，不用記複雜指令

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 標題
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    🎙️ Podcastfy 播客生成系統                            ║${NC}"
echo -e "${CYAN}║                      快速執行腳本 - run.sh                                ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 檢查虛擬環境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  警告：未檢測到虛擬環境，建議先執行：source venv/bin/activate${NC}"
    echo ""
fi

# 主選單
echo -e "${WHITE}請選擇執行模式：${NC}"
echo ""
echo -e "${GREEN}🔧 開發模式（推薦）${NC}"
echo -e "   ${BLUE}1)${NC} 逐步執行 - 每步確認，可隨時中斷查看結果"
echo -e "   ${BLUE}2)${NC} 逐步執行（跳過標籤嵌入）- 省成本，直接腳本→音頻"
echo ""
echo -e "${PURPLE}⚡ 自動化模式${NC}" 
echo -e "   ${BLUE}3)${NC} 全自動三步驟 - 一鍵完成：腳本→標籤→音頻"
echo -e "   ${BLUE}4)${NC} 全自動（跳過標籤）- 快速生成：腳本→音頻"
echo ""
echo -e "${CYAN}🎯 自訂模式${NC}"
echo -e "   ${BLUE}5)${NC} 只生成腳本 - 測試配置和內容"
echo -e "   ${BLUE}6)${NC} 只嵌入標籤 - 為已有腳本添加標籤（需要腳本目錄）"
echo -e "   ${BLUE}7)${NC} 只生成音頻 - 為已有腳本生成音頻（需要腳本目錄）"
echo ""
echo -e "${YELLOW}🛠️ 工具功能${NC}"
echo -e "   ${BLUE}8)${NC} 測試 API 連線 - 檢查 Gemini API 是否正常"
echo -e "   ${BLUE}9)${NC} 查看配置說明 - 了解如何調整設置"
echo -e "   ${BLUE}0)${NC} 退出"
echo ""

# 讀取用戶選擇
read -p "請輸入選項 (0-9): " choice
echo ""

case $choice in
    1)
        echo -e "${GREEN}🔧 啟動開發模式 - 逐步執行（含標籤嵌入）${NC}"
        echo -e "每個步驟完成後會詢問是否繼續，輸入 'view' 可查看腳本內容"
        echo ""
        python podcast_workflow.py --mode dev
        ;;
    
    2)
        echo -e "${GREEN}🔧 啟動開發模式 - 逐步執行（跳過標籤）${NC}"
        echo -e "只執行：腳本生成 → 音頻生成，省略標籤嵌入步驟"
        echo ""
        
        # 臨時修改配置，關閉標籤嵌入
        echo -e "${YELLOW}暫時關閉標籤嵌入功能...${NC}"
        sed -i.bak 's/enabled: true/enabled: false/' podcast_config.yaml
        
        python podcast_workflow.py --mode dev
        
        # 恢復配置
        mv podcast_config.yaml.bak podcast_config.yaml
        echo -e "${YELLOW}已恢復標籤嵌入配置${NC}"
        ;;
    
    3)
        echo -e "${PURPLE}⚡ 啟動全自動模式 - 完整三步驟${NC}"
        echo -e "自動執行：腳本生成 → 標籤嵌入 → 音頻生成"
        echo ""
        python podcast_workflow.py --mode prod
        ;;
    
    4)
        echo -e "${PURPLE}⚡ 啟動全自動模式 - 跳過標籤嵌入${NC}"
        echo -e "自動執行：腳本生成 → 音頻生成"
        echo ""
        
        # 臨時關閉標籤嵌入
        echo -e "${YELLOW}暫時關閉標籤嵌入功能...${NC}"
        sed -i.bak 's/enabled: true/enabled: false/' podcast_config.yaml
        
        python podcast_workflow.py --mode prod
        
        # 恢復配置
        mv podcast_config.yaml.bak podcast_config.yaml
        echo -e "${YELLOW}已恢復標籤嵌入配置${NC}"
        ;;
    
    5)
        echo -e "${CYAN}🎯 只生成腳本${NC}"
        echo -e "測試你的配置是否正確，查看生成的對話內容"
        echo ""
        python podcast_workflow.py --mode custom --steps script
        ;;
    
    6)
        echo -e "${CYAN}🎯 只嵌入標籤${NC}"
        echo ""
        echo -e "${YELLOW}可用的腳本目錄：${NC}"
        if [ -d "output/scripts" ]; then
            ls -la output/scripts/ | grep "^d" | tail -5
        else
            echo "未找到 output/scripts 目錄"
            exit 1
        fi
        echo ""
        read -p "請輸入腳本目錄名稱（例如：script_20250821_143057）: " script_dir
        
        if [ -d "output/scripts/$script_dir" ]; then
            python podcast_workflow.py --mode custom --steps tags --script-dir "./output/scripts/$script_dir"
        else
            echo -e "${RED}❌ 目錄不存在：output/scripts/$script_dir${NC}"
            exit 1
        fi
        ;;
    
    7)
        echo -e "${CYAN}🎯 只生成音頻${NC}"
        echo ""
        echo -e "${YELLOW}可用的腳本目錄：${NC}"
        echo "原始腳本："
        if [ -d "output/scripts" ]; then
            ls -la output/scripts/ | grep "^d" | tail -3
        fi
        echo ""
        echo "帶標籤腳本："
        if [ -d "output/tagged_scripts" ]; then
            ls -la output/tagged_scripts/ | grep "^d" | tail -3
        fi
        echo ""
        read -p "請輸入標籤腳本目錄名稱（例如：tagged_20250821_143145）: " tagged_dir
        
        if [ -d "output/tagged_scripts/$tagged_dir" ]; then
            python podcast_workflow.py --mode custom --steps audio --script-dir "./output/tagged_scripts/$tagged_dir"
        else
            echo -e "${RED}❌ 目錄不存在：output/tagged_scripts/$tagged_dir${NC}"
            exit 1
        fi
        ;;
    
    8)
        echo -e "${YELLOW}🛠️ 測試 API 連線${NC}"
        echo ""
        python test_api.py
        ;;
    
    9)
        echo -e "${YELLOW}🛠️ 配置說明${NC}"
        echo ""
        echo -e "${WHITE}📋 配置文件位置：${NC}podcast_config.yaml"
        echo ""
        echo -e "${WHITE}🎓 英語等級選擇 (basic.english_level):${NC}"
        echo -e "  • A1 英語老師    - 明確教學，80% 語言學習"
        echo -e "  • A2 語言引導者  - 自然指導，60% 語言學習"
        echo -e "  • B1 對話導師    - 穿插教學，40% 語言學習"
        echo -e "  • B2 分析者      - 偶爾提點，20% 語言學習"
        echo -e "  • C1 智者        - 內容導向，5% 語言提點"
        echo -e "  • C2 大師        - 純內容討論"
        echo ""
        echo -e "${WHITE}⏱️ 播客長度選擇 (basic.podcast_length):${NC}"
        echo -e "  • short      - 3-5分鐘"
        echo -e "  • medium     - 6-10分鐘"
        echo -e "  • long       - 11-15分鐘"
        echo -e "  • extra-long - 16-45分鐘"
        echo ""
        echo -e "${WHITE}🏷️ 標籤嵌入功能 (tag_embedding.enabled):${NC}"
        echo -e "  • true  - 開啟（提升音頻品質，但增加成本）"
        echo -e "  • false - 關閉（節省成本）"
        echo ""
        echo -e "${WHITE}📝 詳細文檔：${NC}"
        echo -e "  • 快速開始：快速開始指南.md"
        echo -e "  • 完整配置：configSetting.md"
        echo -e "  • 文檔索引：文檔索引.md"
        echo ""
        ;;
    
    0)
        echo -e "${WHITE}👋 再見！${NC}"
        exit 0
        ;;
    
    *)
        echo -e "${RED}❌ 無效選項：$choice${NC}"
        echo "請重新執行腳本並選擇正確選項 (0-9)"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ 操作完成！${NC}"

# 顯示輸出目錄
if [ -d "output" ]; then
    echo -e "${WHITE}📁 輸出目錄內容：${NC}"
    echo -e "${YELLOW}腳本：${NC}"
    ls -la output/scripts/ 2>/dev/null | tail -3 || echo "  無腳本文件"
    echo -e "${YELLOW}標籤腳本：${NC}"
    ls -la output/tagged_scripts/ 2>/dev/null | tail -3 || echo "  無標籤腳本文件"  
    echo -e "${YELLOW}音頻：${NC}"
    ls -la output/audio/ 2>/dev/null | tail -3 || echo "  無音頻文件"
fi

echo ""
echo -e "${CYAN}💡 提示：重新執行 ${WHITE}./run.sh${CYAN} 來執行其他操作${NC}"