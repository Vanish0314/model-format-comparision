#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键运行3D模型格式分析
"""

import subprocess
import sys
from pathlib import Path

def install_requirements():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 依赖包安装完成")
    except subprocess.CalledProcessError:
        print("✗ 依赖包安装失败")
        return False
    return True

def run_analysis():
    """运行分析脚本"""
    print("正在运行分析脚本...")
    try:
        subprocess.check_call([sys.executable, "scripts/generate_charts.py"])
        print("✓ 分析完成")
        return True
    except subprocess.CalledProcessError:
        print("✗ 分析失败")
        return False

def main():
    """主函数"""
    print("=== 3D模型格式分析工具 ===")
    
    # 检查数据文件是否存在
    if not Path("data/model_data.csv").exists():
        print("错误：找不到数据文件 data/model_data.csv")
        return
    
    # 安装依赖
    if not install_requirements():
        return
    
    # 运行分析
    if run_analysis():
        print("\n=== 分析完成 ===")
        print("生成的图表文件：")
        charts_dir = Path("charts")
        if charts_dir.exists():
            for chart_file in charts_dir.glob("*.png"):
                print(f"  - {chart_file}")
        print(f"\n汇总数据：charts/summary_statistics.csv")
    else:
        print("\n=== 分析失败 ===")

if __name__ == "__main__":
    main()