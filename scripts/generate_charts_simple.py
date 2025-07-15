#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版3D模型格式分析图表生成器
使用基础库生成图表
"""

import csv
import json
from pathlib import Path
import math

class SimpleModelAnalyzer:
    def __init__(self, csv_path):
        """初始化分析器"""
        self.csv_path = csv_path
        self.data = []
        self.charts_dir = Path("charts")
        self.charts_dir.mkdir(exist_ok=True)
        self.load_data()
    
    def load_data(self):
        """加载CSV数据"""
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 转换数据类型
                row['face_count'] = int(row['face_count'])
                row['texture_count'] = int(row['texture_count'])
                row['original_size_mb'] = float(row['original_size_mb'])
                row['compressed_size_mb'] = float(row['compressed_size_mb'])
                row['texture_size_mb'] = float(row['texture_size_mb'])
                
                # 计算压缩率
                row['compression_ratio'] = (row['original_size_mb'] - row['compressed_size_mb']) / row['original_size_mb'] * 100
                # 计算纹理占比
                row['texture_percentage'] = row['texture_size_mb'] / row['original_size_mb'] * 100
                
                self.data.append(row)
    
    def generate_summary_report(self):
        """生成汇总报告"""
        formats = ['fbx', 'obj', 'gltf', 'glb']
        summary = {}
        
        for format_type in formats:
            format_data = [row for row in self.data if row['format'] == format_type]
            
            if format_data:
                summary[format_type] = {
                    'avg_original_size': sum(row['original_size_mb'] for row in format_data) / len(format_data),
                    'avg_compressed_size': sum(row['compressed_size_mb'] for row in format_data) / len(format_data),
                    'avg_compression_ratio': sum(row['compression_ratio'] for row in format_data) / len(format_data),
                    'avg_texture_percentage': sum(row['texture_percentage'] for row in format_data) / len(format_data),
                    'count': len(format_data)
                }
        
        # 保存JSON格式的汇总数据
        with open(self.charts_dir / 'summary_report.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # 生成文本报告
        report_lines = [
            "=== 3D模型格式分析报告 ===",
            "",
            "各格式性能汇总：",
            ""
        ]
        
        for format_type, stats in summary.items():
            report_lines.extend([
                f"{format_type.upper()} 格式:",
                f"  平均原始大小: {stats['avg_original_size']:.1f} MB",
                f"  平均压缩后大小: {stats['avg_compressed_size']:.1f} MB",
                f"  平均压缩率: {stats['avg_compression_ratio']:.1f}%",
                f"  平均纹理占比: {stats['avg_texture_percentage']:.1f}%",
                f"  样本数量: {stats['count']}",
                ""
            ])
        
        # 添加详细数据
        report_lines.extend([
            "详细数据：",
            ""
        ])
        
        models = set(row['model_name'] for row in self.data)
        for model in sorted(models):
            model_data = [row for row in self.data if row['model_name'] == model]
            report_lines.append(f"模型: {model}")
            report_lines.append(f"  面数: {model_data[0]['face_count']:,}")
            report_lines.append(f"  纹理数量: {model_data[0]['texture_count']}")
            
            for row in model_data:
                report_lines.append(f"  {row['format'].upper()}: 原始{row['original_size_mb']:.1f}MB, 压缩{row['compressed_size_mb']:.1f}MB, 压缩率{row['compression_ratio']:.1f}%")
            report_lines.append("")
        
        # 保存文本报告
        with open(self.charts_dir / 'analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print("✓ 汇总报告已生成")
    
    def generate_csv_summary(self):
        """生成CSV格式的汇总数据"""
        formats = ['fbx', 'obj', 'gltf', 'glb']
        
        with open(self.charts_dir / 'summary_statistics.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['格式', '平均原始大小(MB)', '平均压缩后大小(MB)', '平均压缩率(%)', '平均纹理占比(%)', '样本数量'])
            
            for format_type in formats:
                format_data = [row for row in self.data if row['format'] == format_type]
                
                if format_data:
                    avg_original = sum(row['original_size_mb'] for row in format_data) / len(format_data)
                    avg_compressed = sum(row['compressed_size_mb'] for row in format_data) / len(format_data)
                    avg_compression = sum(row['compression_ratio'] for row in format_data) / len(format_data)
                    avg_texture = sum(row['texture_percentage'] for row in format_data) / len(format_data)
                    
                    writer.writerow([
                        format_type.upper(),
                        f"{avg_original:.1f}",
                        f"{avg_compressed:.1f}",
                        f"{avg_compression:.1f}",
                        f"{avg_texture:.1f}",
                        len(format_data)
                    ])
        
        print("✓ CSV汇总数据已生成")
    
    def generate_model_comparison_data(self):
        """生成模型对比数据"""
        models = set(row['model_name'] for row in self.data)
        formats = ['fbx', 'obj', 'gltf', 'glb']
        
        comparison_data = []
        
        for model in sorted(models):
            model_data = [row for row in self.data if row['model_name'] == model]
            face_count = model_data[0]['face_count']
            texture_count = model_data[0]['texture_count']
            
            for format_type in formats:
                format_row = next((row for row in model_data if row['format'] == format_type), None)
                if format_row:
                    comparison_data.append({
                        'model': model.split('_')[0],  # 简化模型名
                        'face_count_k': face_count / 1000,
                        'texture_count': texture_count,
                        'format': format_type.upper(),
                        'original_size': format_row['original_size_mb'],
                        'compressed_size': format_row['compressed_size_mb'],
                        'compression_ratio': format_row['compression_ratio'],
                        'texture_percentage': format_row['texture_percentage']
                    })
        
        # 保存为JSON格式，便于其他工具使用
        with open(self.charts_dir / 'model_comparison_data.json', 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2, ensure_ascii=False)
        
        print("✓ 模型对比数据已生成")
    
    def generate_all_reports(self):
        """生成所有报告"""
        print("正在生成分析报告...")
        
        self.generate_summary_report()
        self.generate_csv_summary()
        self.generate_model_comparison_data()
        
        print(f"\n所有报告已保存到 {self.charts_dir} 目录")
        print("\n生成的文件：")
        print("  - analysis_report.txt (详细文本报告)")
        print("  - summary_report.json (JSON格式汇总)")
        print("  - summary_statistics.csv (CSV格式汇总)")
        print("  - model_comparison_data.json (模型对比数据)")

def main():
    """主函数"""
    csv_path = Path("data/model_data.csv")
    
    if not csv_path.exists():
        print(f"错误：找不到数据文件 {csv_path}")
        return
    
    analyzer = SimpleModelAnalyzer(csv_path)
    analyzer.generate_all_reports()

if __name__ == "__main__":
    main()