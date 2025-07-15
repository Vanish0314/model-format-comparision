#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级3D模型格式分析图表生成器
解决图表显示问题，为每个模型创建单独的图表
"""

import csv
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class AdvancedModelAnalyzer:
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
    
    def generate_overall_comparison(self):
        """生成总体对比图（使用对数坐标解决显示问题）"""
        formats = ['fbx', 'obj', 'gltf', 'glb']
        format_names = ['FBX', 'OBJ', 'glTF', 'GLB']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('3D模型格式总体性能对比', fontsize=16, fontweight='bold')
        
        # 1. 原始文件大小对比（对数坐标）
        original_sizes = []
        for format_type in formats:
            format_data = [row['original_size_mb'] for row in self.data if row['format'] == format_type]
            original_sizes.append(format_data)
        
        ax1.boxplot(original_sizes, labels=format_names)
        ax1.set_yscale('log')
        ax1.set_title('原始文件大小对比 (对数坐标)')
        ax1.set_ylabel('文件大小 (MB)')
        ax1.grid(True, alpha=0.3)
        
        # 2. 压缩后文件大小对比（对数坐标）
        compressed_sizes = []
        for format_type in formats:
            format_data = [row['compressed_size_mb'] for row in self.data if row['format'] == format_type]
            compressed_sizes.append(format_data)
        
        ax2.boxplot(compressed_sizes, labels=format_names)
        ax2.set_yscale('log')
        ax2.set_title('压缩后文件大小对比 (对数坐标)')
        ax2.set_ylabel('文件大小 (MB)')
        ax2.grid(True, alpha=0.3)
        
        # 3. 压缩率对比
        compression_ratios = []
        for format_type in formats:
            format_data = [row['compression_ratio'] for row in self.data if row['format'] == format_type]
            compression_ratios.append(format_data)
        
        ax3.boxplot(compression_ratios, labels=format_names)
        ax3.set_title('压缩率对比')
        ax3.set_ylabel('压缩率 (%)')
        ax3.grid(True, alpha=0.3)
        
        # 4. 纹理占比对比
        texture_percentages = []
        for format_type in formats:
            format_data = [row['texture_percentage'] for row in self.data if row['format'] == format_type]
            texture_percentages.append(format_data)
        
        ax4.boxplot(texture_percentages, labels=format_names)
        ax4.set_title('纹理占比对比')
        ax4.set_ylabel('纹理占比 (%)')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.charts_dir / 'overall_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ 总体对比图已生成")
    
    def generate_individual_model_charts(self):
        """为每个模型生成单独的图表"""
        models = set(row['model_name'] for row in self.data)
        formats = ['fbx', 'obj', 'gltf', 'glb']
        format_names = ['FBX', 'OBJ', 'glTF', 'GLB']
        
        for model in models:
            model_data = [row for row in self.data if row['model_name'] == model]
            if not model_data:
                continue
            
            # 创建图表
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f'模型: {model}', fontsize=16, fontweight='bold')
            
            # 提取数据
            original_sizes = []
            compressed_sizes = []
            compression_ratios = []
            texture_percentages = []
            
            for format_type in formats:
                format_row = next((row for row in model_data if row['format'] == format_type), None)
                if format_row:
                    original_sizes.append(format_row['original_size_mb'])
                    compressed_sizes.append(format_row['compressed_size_mb'])
                    compression_ratios.append(format_row['compression_ratio'])
                    texture_percentages.append(format_row['texture_percentage'])
                else:
                    original_sizes.append(0)
                    compressed_sizes.append(0)
                    compression_ratios.append(0)
                    texture_percentages.append(0)
            
            # 1. 文件大小对比
            x = np.arange(len(format_names))
            width = 0.35
            
            ax1.bar(x - width/2, original_sizes, width, label='原始大小', alpha=0.8)
            ax1.bar(x + width/2, compressed_sizes, width, label='压缩后大小', alpha=0.8)
            ax1.set_xlabel('格式')
            ax1.set_ylabel('文件大小 (MB)')
            ax1.set_title('文件大小对比')
            ax1.set_xticks(x)
            ax1.set_xticklabels(format_names)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. 压缩率对比
            bars = ax2.bar(format_names, compression_ratios, alpha=0.8, color='skyblue')
            ax2.set_xlabel('格式')
            ax2.set_ylabel('压缩率 (%)')
            ax2.set_title('压缩率对比')
            ax2.grid(True, alpha=0.3)
            
            # 在柱状图上添加数值标签
            for bar, ratio in zip(bars, compression_ratios):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{ratio:.1f}%', ha='center', va='bottom')
            
            # 3. 纹理占比对比
            bars = ax3.bar(format_names, texture_percentages, alpha=0.8, color='lightgreen')
            ax3.set_xlabel('格式')
            ax3.set_ylabel('纹理占比 (%)')
            ax3.set_title('纹理占比对比')
            ax3.grid(True, alpha=0.3)
            
            # 在柱状图上添加数值标签
            for bar, percentage in zip(bars, texture_percentages):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{percentage:.1f}%', ha='center', va='bottom')
            
            # 4. 模型信息
            face_count = model_data[0]['face_count']
            texture_count = model_data[0]['texture_count']
            
            ax4.axis('off')
            info_text = f"""
模型信息:
• 面数: {face_count:,}
• 纹理数量: {texture_count}

各格式性能排名:
"""
            
            # 按压缩率排序
            format_performance = list(zip(format_names, compression_ratios))
            format_performance.sort(key=lambda x: x[1], reverse=True)
            
            for i, (format_name, ratio) in enumerate(format_performance, 1):
                info_text += f"{i}. {format_name}: {ratio:.1f}%\n"
            
            ax4.text(0.1, 0.9, info_text, transform=ax4.transAxes, fontsize=12,
                    verticalalignment='top', fontfamily='monospace')
            
            plt.tight_layout()
            
            # 保存图表
            safe_model_name = model.replace(' ', '_').replace('/', '_')
            plt.savefig(self.charts_dir / f'model_{safe_model_name}.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"✓ 已为 {len(models)} 个模型生成单独图表")
    
    def generate_format_analysis(self):
        """生成格式分析图表"""
        formats = ['fbx', 'obj', 'gltf', 'glb']
        format_names = ['FBX', 'OBJ', 'glTF', 'GLB']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('各格式性能分析', fontsize=16, fontweight='bold')
        
        # 计算各格式的平均值
        format_stats = {}
        for format_type in formats:
            format_data = [row for row in self.data if row['format'] == format_type]
            if format_data:
                format_stats[format_type] = {
                    'avg_original': sum(row['original_size_mb'] for row in format_data) / len(format_data),
                    'avg_compressed': sum(row['compressed_size_mb'] for row in format_data) / len(format_data),
                    'avg_compression': sum(row['compression_ratio'] for row in format_data) / len(format_data),
                    'avg_texture': sum(row['texture_percentage'] for row in format_data) / len(format_data)
                }
        
        # 1. 平均文件大小对比
        avg_original = [format_stats[f]['avg_original'] for f in formats]
        avg_compressed = [format_stats[f]['avg_compressed'] for f in formats]
        
        x = np.arange(len(format_names))
        width = 0.35
        
        ax1.bar(x - width/2, avg_original, width, label='平均原始大小', alpha=0.8)
        ax1.bar(x + width/2, avg_compressed, width, label='平均压缩后大小', alpha=0.8)
        ax1.set_xlabel('格式')
        ax1.set_ylabel('文件大小 (MB)')
        ax1.set_title('平均文件大小对比')
        ax1.set_xticks(x)
        ax1.set_xticklabels(format_names)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 平均压缩率对比
        avg_compression = [format_stats[f]['avg_compression'] for f in formats]
        bars = ax2.bar(format_names, avg_compression, alpha=0.8, color='orange')
        ax2.set_xlabel('格式')
        ax2.set_ylabel('平均压缩率 (%)')
        ax2.set_title('平均压缩率对比')
        ax2.grid(True, alpha=0.3)
        
        for bar, ratio in zip(bars, avg_compression):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{ratio:.1f}%', ha='center', va='bottom')
        
        # 3. 平均纹理占比对比
        avg_texture = [format_stats[f]['avg_texture'] for f in formats]
        bars = ax3.bar(format_names, avg_texture, alpha=0.8, color='lightcoral')
        ax3.set_xlabel('格式')
        ax3.set_ylabel('平均纹理占比 (%)')
        ax3.set_title('平均纹理占比对比')
        ax3.grid(True, alpha=0.3)
        
        for bar, percentage in zip(bars, avg_texture):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{percentage:.1f}%', ha='center', va='bottom')
        
        # 4. 格式性能雷达图
        categories = ['压缩率', '文件大小效率', '纹理处理', '兼容性']
        
        # 简化的雷达图数据（基于压缩率和文件大小效率）
        compression_scores = [format_stats[f]['avg_compression'] for f in formats]
        size_efficiency = [100 - (format_stats[f]['avg_compressed'] / max(avg_compressed) * 100) for f in formats]
        texture_scores = [100 - format_stats[f]['avg_texture'] for f in formats]  # 纹理占比越低越好
        compatibility_scores = [85, 90, 95, 95]  # 假设的兼容性分数
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]  # 闭合图形
        
        for i, format_name in enumerate(format_names):
            values = [compression_scores[i], size_efficiency[i], texture_scores[i], compatibility_scores[i]]
            values += values[:1]  # 闭合图形
            ax4.plot(angles, values, 'o-', linewidth=2, label=format_name, alpha=0.8)
            ax4.fill(angles, values, alpha=0.1)
        
        ax4.set_xticks(angles[:-1])
        ax4.set_xticklabels(categories)
        ax4.set_ylim(0, 100)
        ax4.set_title('格式性能雷达图')
        ax4.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig(self.charts_dir / 'format_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ 格式分析图表已生成")
    
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
        with open(self.charts_dir / 'advanced_summary_report.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # 生成文本报告
        report_lines = [
            "=== 高级3D模型格式分析报告 ===",
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
        with open(self.charts_dir / 'advanced_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print("✓ 高级汇总报告已生成")
    
    def generate_all_charts(self):
        """生成所有图表"""
        print("正在生成高级分析图表...")
        
        self.generate_overall_comparison()
        self.generate_individual_model_charts()
        self.generate_format_analysis()
        self.generate_summary_report()
        
        print(f"\n所有图表已保存到 {self.charts_dir} 目录")
        print("\n生成的文件：")
        print("  - overall_comparison.png (总体对比图)")
        print("  - model_*.png (各模型单独图表)")
        print("  - format_analysis.png (格式分析图)")
        print("  - advanced_analysis_report.txt (详细文本报告)")
        print("  - advanced_summary_report.json (JSON格式汇总)")

def main():
    """主函数"""
    csv_path = Path("data/model_data.csv")
    
    if not csv_path.exists():
        print(f"错误：找不到数据文件 {csv_path}")
        print("请先运行 scripts/convert_json_to_csv.py 转换数据")
        return
    
    analyzer = AdvancedModelAnalyzer(csv_path)
    analyzer.generate_all_charts()

if __name__ == "__main__":
    main()