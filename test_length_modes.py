#!/usr/bin/env python3
"""
測試三種播客長度模式
- short: 1-2分鐘快速導覽
- medium: 3-5分鐘適度深入  
- long: 8-12分鐘詳盡分析
"""

import os
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime

def test_mode(mode: str, test_input: str = None):
    """測試特定的長度模式"""
    
    print("=" * 60)
    print(f"📏 測試 '{mode}' 模式")
    print("=" * 60)
    
    # 載入並修改配置
    config_path = "./podcast_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 設定測試模式
    original_mode = config['basic']['podcast_length']
    config['basic']['podcast_length'] = mode
    
    # 使用測試輸入或預設輸入
    if test_input:
        config['input']['source'] = test_input
    
    # 保存臨時配置
    temp_config = f"test_config_{mode}.yaml"
    with open(temp_config, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
    
    try:
        # 執行腳本生成
        from generate_script import generate_script_only
        result = generate_script_only(temp_config)
        
        if result:
            # 讀取並顯示結果
            metadata_file = Path(result) / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                print(f"\n✅ {mode} 模式測試成功！")
                print(f"📊 結果統計：")
                print(f"   - 播客長度: {metadata['podcast_length']} ({metadata['time_range']})")
                print(f"   - 實際字數: {metadata['actual_words']}")
                print(f"   - 目標字數: {metadata['target_words']}")
                print(f"   - 準確度: {metadata['accuracy']}")
                
                # 顯示腳本片段
                script_file = Path(result) / "podcast_script.txt"
                if script_file.exists():
                    with open(script_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        print(f"\n📝 腳本預覽（前5行）：")
                        for line in lines[:5]:
                            if line.strip():
                                print(f"   {line[:100]}...")
                
                return True
        else:
            print(f"❌ {mode} 模式測試失敗")
            return False
            
    finally:
        # 清理臨時配置
        if os.path.exists(temp_config):
            os.remove(temp_config)
        
        # 恢復原始配置
        config['basic']['podcast_length'] = original_mode
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)


def main():
    """主程式"""
    
    # 預設測試輸入（一個簡短的新聞）
    default_input = """
    人工智慧的快速發展正在改變我們的生活方式。
    從智能助手到自動駕駛，AI技術無處不在。
    專家預測，未來十年將是AI發展的黃金時期。
    """
    
    if len(sys.argv) > 1:
        # 測試特定模式
        mode = sys.argv[1]
        if mode in ['short', 'medium', 'long']:
            test_mode(mode, default_input)
        else:
            print(f"❌ 未知模式: {mode}")
            print("可用模式: short, medium, long")
    else:
        # 測試所有模式
        print("🚀 測試所有播客長度模式\n")
        
        modes = ['short', 'medium', 'long']
        results = {}
        
        for mode in modes:
            success = test_mode(mode, default_input)
            results[mode] = "✅ 成功" if success else "❌ 失敗"
            print()
        
        # 顯示總結
        print("=" * 60)
        print("📊 測試總結：")
        for mode, status in results.items():
            print(f"   {mode:8} : {status}")
        print("=" * 60)


if __name__ == "__main__":
    main()