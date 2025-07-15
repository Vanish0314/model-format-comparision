#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D模型格式分析图表生成器
分析fbx、obj、gltf、glb格式的素材大小、压缩率等数据
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置图表样式
sns.set_style("whitegrid")
plt.style.use('seaborn-v0_8')

class ModelDataAnalyzer:
    def __init__(self, csv_path):
        """初始化分析器"""
        self.csv_path = csv_path
        self.data = None
        self.charts_dir = Path("../charts")
        self.charts_dir.mkdir(exist_ok=True)
        self.load_data()
    
    def load_data(self):
        """加载CSV数据"""
        self.data = pd.read_csv(self.csv_path)
        # 计算压缩率
        self.data['compression_ratio'] = (self.data['original_size_mb'] - self.data['compressed_size_mb']) / self.data['original_size_mb'] * 100
        # 计算纹理占比
        self.data['texture_percentage'] = self.data['texture_size_mb'] / self.data['original_size_mb'] * 100
    
    def create_size_comparison_chart(self):
        """创建素材大小对比图（压缩前后）"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        
        # 按模型分组
        models = self.data['model_name'].unique()
        formats = ['fbx', 'obj', 'gltf', 'glb']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        x = np.arange(len(models))
        width = 0.2
        
        # 压缩前大小对比
        for i, format_type in enumerate(formats):
            format_data = self.data[self.data['format'] == format_type]
            sizes = [format_data[format_data['model_name'] == model]['original_size_mb'].iloc[0] 
                    for model in models]
            ax1.bar(x + i * width, sizes, width, label=format_type.upper(), 
                   color=colors[i], alpha=0.8)
        
        ax1.set_xlabel('模型名称')
        ax1.set_ylabel('压缩前大小 (MB)')
        ax1.set_title('各格式压缩前大小对比')
        ax1.set_xticks(x + width * 1.5)
        ax1.set_xticklabels([model.split('_')[0] for model in models], rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 压缩后大小对比
        for i, format_type in enumerate(formats):
            format_data = self.data[self.data['format'] == format_type]
            sizes = [format_data[format_data['model_name'] == model]['compressed_size_mb'].iloc[0] 
                    for model in models]
            ax2.bar(x + i * width, sizes, width, label=format_type.upper(), 
                   color=colors[i], alpha=0.8)
        
        ax2.set_xlabel('模型名称')
        ax2.set_ylabel('压缩后大小 (MB)')
        ax2.set_title('各格式压缩后大小对比')
        ax2.set_xticks(x + width * 1.5)
        ax2.set_xticklabels([model.split('_')[0] for model in models], rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.charts_dir / 'size_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_compression_ratio_chart(self):
        """创建压缩率对比图"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 按格式分组计算平均压缩率
        compression_data = self.data.groupby('format')['compression_ratio'].mean().reset_index()
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        bars = ax.bar(compression_data['format'].str.upper(), 
                     compression_data['compression_ratio'], 
                     color=colors, alpha=0.8)
        
        # 添加数值标签
        for bar, ratio in zip(bars, compression_data['compression_ratio']):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{ratio:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax.set_xlabel('文件格式')
        ax.set_ylabel('平均压缩率 (%)')
        ax.set_title('各格式平均压缩率对比')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.charts_dir / 'compression_ratio.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_texture_percentage_chart(self):
        """创建纹理占比图"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 按格式分组计算平均纹理占比
        texture_data = self.data.groupby('format')['texture_percentage'].mean().reset_index()
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        bars = ax.bar(texture_data['format'].str.upper(), 
                     texture_data['texture_percentage'], 
                     color=colors, alpha=0.8)
        
        # 添加数值标签
        for bar, percentage in zip(bars, texture_data['texture_percentage']):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{percentage:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax.set_xlabel('文件格式')
        ax.set_ylabel('纹理占模型大小百分比 (%)')
        ax.set_title('各格式纹理占比对比')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.charts_dir / 'texture_percentage.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_detailed_analysis_chart(self):
        """创建详细分析图（包含面数信息）"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        models = self.data['model_name'].unique()
        formats = ['fbx', 'obj', 'gltf', 'glb']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        # 1. 面数与文件大小关系
        for i, format_type in enumerate(formats):
            format_data = self.data[self.data['format'] == format_type]
            ax1.scatter(format_data['face_count'] / 1000, format_data['original_size_mb'], 
                       label=format_type.upper(), color=colors[i], s=100, alpha=0.7)
        
        ax1.set_xlabel('面数 (千)')
        ax1.set_ylabel('原始大小 (MB)')
        ax1.set_title('面数与文件大小关系')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 压缩率与面数关系
        for i, format_type in enumerate(formats):
            format_data = self.data[self.data['format'] == format_type]
            ax2.scatter(format_data['face_count'] / 1000, format_data['compression_ratio'], 
                       label=format_type.upper(), color=colors[i], s=100, alpha=0.7)
        
        ax2.set_xlabel('面数 (千)')
        ax2.set_ylabel('压缩率 (%)')
        ax2.set_title('面数与压缩率关系')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 纹理数量与纹理占比关系
        for i, format_type in enumerate(formats):
            format_data = self.data[self.data['format'] == format_type]
            ax3.scatter(format_data['texture_count'], format_data['texture_percentage'], 
                       label=format_type.upper(), color=colors[i], s=100, alpha=0.7)
        
        ax3.set_xlabel('纹理数量')
        ax3.set_ylabel('纹理占比 (%)')
        ax3.set_title('纹理数量与纹理占比关系')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 各格式在不同模型上的表现
        x = np.arange(len(models))
        width = 0.2
        
        for i, format_type in enumerate(formats):
            format_data = self.data[self.data['format'] == format_type]
            compression_ratios = [format_data[format_data['model_name'] == model]['compression_ratio'].iloc[0] 
                                for model in models]
            ax4.bar(x + i * width, compression_ratios, width, label=format_type.upper(), 
                   color=colors[i], alpha=0.8)
        
        ax4.set_xlabel('模型名称')
        ax4.set_ylabel('压缩率 (%)')
        ax4.set_title('各格式在不同模型上的压缩率表现')
        ax4.set_xticks(x + width * 1.5)
        ax4.set_xticklabels([model.split('_')[0] for model in models], rotation=45)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.charts_dir / 'detailed_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_summary_table(self):
        """创建汇总表格"""
        summary = self.data.groupby('format').agg({
            'original_size_mb': ['mean', 'std'],
            'compressed_size_mb': ['mean', 'std'],
            'compression_ratio': ['mean', 'std'],
            'texture_percentage': ['mean', 'std']
        }).round(2)
        
        # 保存汇总数据
        summary.to_csv(self.charts_dir / 'summary_statistics.csv')
        
        # 创建可视化表格
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('tight')
        ax.axis('off')
        
        # 准备表格数据
        table_data = []
        headers = ['格式', '平均原始大小(MB)', '平均压缩后大小(MB)', '平均压缩率(%)', '平均纹理占比(%)']
        
        for format_type in ['fbx', 'obj', 'gltf', 'glb']:
            format_data = self.data[self.data['format'] == format_type]
            row = [
                format_type.upper(),
                f"{format_data['original_size_mb'].mean():.1f}",
                f"{format_data['compressed_size_mb'].mean():.1f}",
                f"{format_data['compression_ratio'].mean():.1f}",
                f"{format_data['texture_percentage'].mean():.1f}"
            ]
            table_data.append(row)
        
        table = ax.table(cellText=table_data, colLabels=headers, 
                        cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.5)
        
        plt.title('各格式性能汇总表', fontsize=16, fontweight='bold', pad=20)
        plt.savefig(self.charts_dir / 'summary_table.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_all_charts(self):
        """生成所有图表"""
        print("正在生成图表...")
        
        self.create_size_comparison_chart()
        print("✓ 素材大小对比图已生成")
        
        self.create_compression_ratio_chart()
        print("✓ 压缩率对比图已生成")
        
        self.create_texture_percentage_chart()
        print("✓ 纹理占比图已生成")
        
        self.create_detailed_analysis_chart()
        print("✓ 详细分析图已生成")
        
        self.create_summary_table()
        print("✓ 汇总表格已生成")
        
        print(f"\n所有图表已保存到 {self.charts_dir} 目录")

def main():
    """主函数"""
    csv_path = Path("../data/model_data.csv")
    
    if not csv_path.exists():
        print(f"错误：找不到数据文件 {csv_path}")
        return
    
    analyzer = ModelDataAnalyzer(csv_path)
    analyzer.generate_all_charts()

if __name__ == "__main__":
    main()