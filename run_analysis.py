#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D模型格式性能分析工具
使用新的模块化架构
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.analyzer import ModelAnalyzer
from src.memory_analyzer import MemoryAnalyzer
from src.report_generator import ReportGenerator


def main():
    """主函数"""
    print("=== 3D模型格式性能分析工具 ===")
    print("使用新的模块化架构")
    print()
    
    # 检查数据文件
    csv_path = Path("data/model_data.csv")
    if not csv_path.exists():
        print(f"错误：找不到数据文件 {csv_path}")
        return
    
    try:
        # 初始化分析器
        print("正在初始化分析器...")
        analyzer = ModelAnalyzer(str(csv_path))
        
        # 初始化内存分析器
        print("正在初始化内存分析器...")
        memory_analyzer = MemoryAnalyzer(analyzer.data)
        
        # 初始化报告生成器
        print("正在初始化报告生成器...")
        report_generator = ReportGenerator(analyzer, memory_analyzer)
        
        # 生成所有报告
        print("正在生成分析报告...")
        generated_files = report_generator.generate_all_reports()
        
        # 显示结果
        print("\n=== 分析完成 ===")
        print("生成的文件：")
        
        for file_type, file_path in generated_files.items():
            print(f"  - {file_type}: {file_path}")
        
        print("\n查看结果：")
        print("  - 文本报告: charts/analysis_report.txt")
        print("  - HTML报告: charts/analysis_report.html (在浏览器中打开)")
        print("  - 内存分析: charts/memory_analysis_report.txt")
        print("  - 汇总数据: charts/summary_statistics.csv")
        print("  - JSON数据: charts/summary_report.json")
        print("  - 详细内存分析: charts/detailed_memory_analysis.json")
        
        # 显示一些关键统计信息
        print("\n=== 关键统计信息 ===")
        format_analyses = analyzer.analyze_all_formats()
        
        for format_type, stats in format_analyses.items():
            print(f"{format_type.upper()}:")
            print(f"  平均压缩率: {stats['avg_compression_ratio']:.1f}%")
            print(f"  平均压缩后大小: {stats['avg_compressed_size']:.1f} MB")
            if stats['avg_peak_memory']:
                print(f"  平均峰值内存: {stats['avg_peak_memory']:.1f} MB")
            print()
        
        # 显示最佳格式推荐
        print("=== 最佳格式推荐 ===")
        try:
            best_compression, _ = analyzer.find_best_format('compression')
            best_size, _ = analyzer.find_best_format('size')
            best_memory, _ = analyzer.find_best_format('memory')
            
            print(f"最佳压缩率格式: {best_compression.upper()}")
            print(f"最小文件大小格式: {best_size.upper()}")
            print(f"最低内存占用格式: {best_memory.upper()}")
        except Exception as e:
            print(f"无法确定最佳格式: {e}")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()