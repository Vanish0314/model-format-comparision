#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键运行所有3D模型格式分析
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name):
    """运行指定的脚本"""
    script_path = Path("scripts") / script_name
    if not script_path.exists():
        print(f"错误：找不到脚本 {script_path}")
        return False
    
    try:
        print(f"正在运行 {script_name}...")
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ {script_name} 执行成功")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"✗ {script_name} 执行失败")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ 运行 {script_name} 时出错: {e}")
        return False

def main():
    """主函数"""
    print("=== 3D模型格式分析工具 ===")
    
    # 检查数据文件是否存在
    if not Path("data/model_data.csv").exists():
        print("错误：找不到数据文件 data/model_data.csv")
        return
    
    # 检查charts目录
    charts_dir = Path("charts")
    charts_dir.mkdir(exist_ok=True)
    
    # 运行所有分析脚本
    scripts = [
        "generate_charts_simple.py",
        "generate_html_report.py"
    ]
    
    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1
    
    print(f"\n=== 分析完成 ===")
    print(f"成功运行 {success_count}/{len(scripts)} 个脚本")
    
    if success_count > 0:
        print("\n生成的文件：")
        charts_dir = Path("charts")
        if charts_dir.exists():
            for file_path in charts_dir.glob("*"):
                if file_path.is_file():
                    print(f"  - {file_path}")
        
        print("\n查看结果：")
        print("  - 文本报告: charts/analysis_report.txt")
        print("  - HTML报告: charts/analysis_report.html (在浏览器中打开)")
        print("  - 汇总数据: charts/summary_statistics.csv")
        print("  - JSON数据: charts/summary_report.json")

if __name__ == "__main__":
    main()