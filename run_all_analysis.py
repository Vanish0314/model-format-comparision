#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键运行所有3D模型格式分析
使用新的模块化架构
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

def run_new_analysis():
    """运行新的模块化分析"""
    print("正在运行新的模块化分析...")
    try:
        result = subprocess.run([sys.executable, "run_analysis.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ 新的模块化分析执行成功")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("✗ 新的模块化分析执行失败")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ 运行新的模块化分析时出错: {e}")
        return False

def main():
    """主函数"""
    print("=== 3D模型格式分析工具 ===")
    print("一键运行所有分析")
    print()
    
    # 检查rawdata目录和数据文件
    json_path = Path("rawdata/model_data.json")
    csv_path = Path("data/model_data.csv")
    
    if not json_path.exists():
        print("错误：找不到原始数据文件 rawdata/model_data.json")
        return
    
    # 如果CSV文件不存在，先转换数据
    if not csv_path.exists():
        print("正在转换JSON数据为CSV格式...")
        if not run_script("convert_json_to_csv.py"):
            print("错误：数据转换失败")
            return
    
    # 检查charts目录
    charts_dir = Path("charts")
    charts_dir.mkdir(exist_ok=True)
    
    success_count = 0
    total_scripts = 0
    
    # 首先运行新的模块化分析
    print("=== 运行新的模块化分析 ===")
    if run_new_analysis():
        success_count += 1
    total_scripts += 1
    
    # 然后运行传统的脚本（如果存在）
    print("\n=== 运行传统分析脚本 ===")
    scripts = [
        "convert_json_to_csv.py",
        "generate_charts_simple.py",
        "generate_advanced_charts.py",
        "generate_html_report.py"
    ]
    
    for script in scripts:
        if run_script(script):
            success_count += 1
        total_scripts += 1
    
    print(f"\n=== 分析完成 ===")
    print(f"成功运行 {success_count}/{total_scripts} 个分析")
    
    if success_count > 0:
        print("\n生成的文件：")
        charts_dir = Path("charts")
        if charts_dir.exists():
            for file_path in charts_dir.glob("*"):
                if file_path.is_file():
                    print(f"  - {file_path}")
        
        print("\n查看结果：")
        print("  - 基础文本报告: charts/analysis_report.txt")
        print("  - 高级文本报告: charts/advanced_analysis_report.txt")
        print("  - HTML报告: charts/analysis_report.html (在浏览器中打开)")
        print("  - 内存分析: charts/memory_analysis_report.txt")
        print("  - 汇总数据: charts/summary_statistics.csv")
        print("  - JSON数据: charts/summary_report.json")
        print("  - 详细内存分析: charts/detailed_memory_analysis.json")
        print("  - 模型对比数据: charts/model_comparison_data.json")
        
        print("\n推荐查看顺序：")
        print("1. charts/analysis_report.html (完整的HTML报告)")
        print("2. charts/memory_analysis_report.txt (内存分析报告)")
        print("3. charts/summary_statistics.csv (汇总数据)")

if __name__ == "__main__":
    main()