#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存分析模块
专门用于分析3D模型格式的内存占用特性
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import statistics


class MemoryAnalyzer:
    """内存分析器"""
    
    def __init__(self, data: List[Dict]):
        """
        初始化内存分析器
        
        Args:
            data: 模型数据列表
        """
        self.data = data
        self.memory_data = [row for row in data if row.get('peak_memory_mb') is not None]
    
    def get_memory_statistics(self) -> Dict:
        """获取内存统计信息"""
        if not self.memory_data:
            return {'error': '没有可用的内存数据'}
        
        memory_values = [row['peak_memory_mb'] for row in self.memory_data]
        
        return {
            'total_count': len(self.memory_data),
            'mean': statistics.mean(memory_values),
            'median': statistics.median(memory_values),
            'min': min(memory_values),
            'max': max(memory_values),
            'std_dev': statistics.stdev(memory_values) if len(memory_values) > 1 else 0,
            'percentiles': {
                '25': statistics.quantiles(memory_values, n=4)[0],
                '75': statistics.quantiles(memory_values, n=4)[2]
            }
        }
    
    def analyze_memory_by_format(self) -> Dict[str, Dict]:
        """按格式分析内存占用"""
        format_memory = {}
        
        for row in self.memory_data:
            format_type = row['format']
            if format_type not in format_memory:
                format_memory[format_type] = []
            format_memory[format_type].append(row['peak_memory_mb'])
        
        analysis = {}
        for format_type, memory_values in format_memory.items():
            analysis[format_type] = {
                'count': len(memory_values),
                'mean': statistics.mean(memory_values),
                'median': statistics.median(memory_values),
                'min': min(memory_values),
                'max': max(memory_values),
                'std_dev': statistics.stdev(memory_values) if len(memory_values) > 1 else 0
            }
        
        return analysis
    
    def analyze_memory_by_model_size(self) -> Dict[str, Dict]:
        """按模型大小分析内存占用"""
        # 按面数分组
        small_models = [row for row in self.memory_data if row['face_count'] < 100000]
        medium_models = [row for row in self.memory_data if 100000 <= row['face_count'] < 1000000]
        large_models = [row for row in self.memory_data if row['face_count'] >= 1000000]
        
        analysis = {}
        
        if small_models:
            memory_values = [row['peak_memory_mb'] for row in small_models]
            analysis['small_models'] = {
                'face_count_range': '< 100k',
                'count': len(small_models),
                'mean_memory': statistics.mean(memory_values),
                'min_memory': min(memory_values),
                'max_memory': max(memory_values)
            }
        
        if medium_models:
            memory_values = [row['peak_memory_mb'] for row in medium_models]
            analysis['medium_models'] = {
                'face_count_range': '100k - 1M',
                'count': len(medium_models),
                'mean_memory': statistics.mean(memory_values),
                'min_memory': min(memory_values),
                'max_memory': max(memory_values)
            }
        
        if large_models:
            memory_values = [row['peak_memory_mb'] for row in large_models]
            analysis['large_models'] = {
                'face_count_range': '>= 1M',
                'count': len(large_models),
                'mean_memory': statistics.mean(memory_values),
                'min_memory': min(memory_values),
                'max_memory': max(memory_values)
            }
        
        return analysis
    
    def find_memory_efficient_formats(self) -> List[Tuple[str, float]]:
        """找到内存效率最高的格式"""
        format_analysis = self.analyze_memory_by_format()
        
        # 按平均内存占用排序
        sorted_formats = sorted(
            format_analysis.items(),
            key=lambda x: x[1]['mean']
        )
        
        return [(format_type, stats['mean']) for format_type, stats in sorted_formats]
    
    def get_memory_correlation_analysis(self) -> Dict:
        """分析内存占用与其他指标的相关性"""
        if not self.memory_data:
            return {'error': '没有可用的内存数据'}
        
        # 计算内存与面数的相关性
        face_memory_pairs = [(row['face_count'], row['peak_memory_mb']) for row in self.memory_data]
        
        # 计算内存与文件大小的相关性
        size_memory_pairs = [(row['original_size_mb'], row['peak_memory_mb']) for row in self.memory_data]
        
        # 计算内存与纹理数量的相关性
        texture_memory_pairs = [(row['texture_count'], row['peak_memory_mb']) for row in self.memory_data]
        
        return {
            'face_count_correlation': self._calculate_correlation(face_memory_pairs),
            'file_size_correlation': self._calculate_correlation(size_memory_pairs),
            'texture_count_correlation': self._calculate_correlation(texture_memory_pairs)
        }
    
    def _calculate_correlation(self, pairs: List[Tuple[float, float]]) -> float:
        """计算皮尔逊相关系数"""
        if len(pairs) < 2:
            return 0.0
        
        x_values = [pair[0] for pair in pairs]
        y_values = [pair[1] for pair in pairs]
        
        n = len(pairs)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in pairs)
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def generate_memory_report(self, output_dir: Path) -> str:
        """生成内存分析报告"""
        output_dir.mkdir(exist_ok=True)
        
        report_lines = [
            "=== 3D模型格式内存占用分析报告 ===",
            "",
            f"分析时间: {len(self.memory_data)} 个模型有内存数据",
            ""
        ]
        
        # 总体统计
        overall_stats = self.get_memory_statistics()
        if 'error' not in overall_stats:
            report_lines.extend([
                "总体内存统计:",
                f"  平均内存占用: {overall_stats['mean']:.1f} MB",
                f"  中位数内存占用: {overall_stats['median']:.1f} MB",
                f"  最小内存占用: {overall_stats['min']:.1f} MB",
                f"  最大内存占用: {overall_stats['max']:.1f} MB",
                f"  标准差: {overall_stats['std_dev']:.1f} MB",
                ""
            ])
        
        # 按格式分析
        format_analysis = self.analyze_memory_by_format()
        report_lines.extend([
            "各格式内存占用分析:",
            ""
        ])
        
        for format_type, stats in format_analysis.items():
            report_lines.extend([
                f"{format_type.upper()} 格式:",
                f"  样本数量: {stats['count']}",
                f"  平均内存: {stats['mean']:.1f} MB",
                f"  中位数: {stats['median']:.1f} MB",
                f"  范围: {stats['min']:.1f} - {stats['max']:.1f} MB",
                ""
            ])
        
        # 内存效率排名
        efficient_formats = self.find_memory_efficient_formats()
        report_lines.extend([
            "内存效率排名 (从低到高):",
            ""
        ])
        
        for i, (format_type, avg_memory) in enumerate(efficient_formats, 1):
            report_lines.append(f"{i}. {format_type.upper()}: {avg_memory:.1f} MB")
        
        report_lines.append("")
        
        # 相关性分析
        correlation = self.get_memory_correlation_analysis()
        if 'error' not in correlation:
            report_lines.extend([
                "内存占用相关性分析:",
                f"  与面数的相关性: {correlation['face_count_correlation']:.3f}",
                f"  与文件大小的相关性: {correlation['file_size_correlation']:.3f}",
                f"  与纹理数量的相关性: {correlation['texture_count_correlation']:.3f}",
                ""
            ])
        
        # 按模型大小分析
        size_analysis = self.analyze_memory_by_model_size()
        if size_analysis:
            report_lines.extend([
                "按模型大小分组的内存分析:",
                ""
            ])
            
            for size_category, stats in size_analysis.items():
                report_lines.extend([
                    f"{stats['face_count_range']} 面数:",
                    f"  样本数量: {stats['count']}",
                    f"  平均内存: {stats['mean_memory']:.1f} MB",
                    f"  范围: {stats['min_memory']:.1f} - {stats['max_memory']:.1f} MB",
                    ""
                ])
        
        # 保存报告
        report_path = output_dir / 'memory_analysis_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        return str(report_path)
    
    def export_memory_data(self, output_dir: Path) -> Dict[str, str]:
        """导出内存分析数据"""
        output_dir.mkdir(exist_ok=True)
        generated_files = {}
        
        # 导出JSON格式的内存分析数据
        memory_analysis = {
            'overall_statistics': self.get_memory_statistics(),
            'format_analysis': self.analyze_memory_by_format(),
            'size_analysis': self.analyze_memory_by_model_size(),
            'correlation_analysis': self.get_memory_correlation_analysis(),
            'efficiency_ranking': [
                {'format': format_type, 'avg_memory': avg_memory}
                for format_type, avg_memory in self.find_memory_efficient_formats()
            ]
        }
        
        json_path = output_dir / 'detailed_memory_analysis.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(memory_analysis, f, indent=2, ensure_ascii=False)
        
        generated_files['json'] = str(json_path)
        
        # 生成文本报告
        report_path = self.generate_memory_report(output_dir)
        generated_files['report'] = report_path
        
        return generated_files