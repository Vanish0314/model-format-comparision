#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D模型格式性能分析器
核心分析功能模块
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import statistics


class ModelAnalyzer:
    """3D模型格式性能分析器"""
    
    def __init__(self, csv_path: str):
        """
        初始化分析器
        
        Args:
            csv_path: CSV数据文件路径
        """
        self.csv_path = Path(csv_path)
        self.data = []
        self.charts_dir = Path("charts")
        self.charts_dir.mkdir(exist_ok=True)
        self.load_data()
    
    def load_data(self):
        """加载CSV数据并预处理"""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.csv_path}")
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 转换数据类型
                processed_row = self._process_row(row)
                self.data.append(processed_row)
        
        print(f"✓ 已加载 {len(self.data)} 条数据记录")
    
    def _process_row(self, row: Dict) -> Dict:
        """
        处理单行数据
        
        Args:
            row: 原始行数据
            
        Returns:
            处理后的行数据
        """
        processed = row.copy()
        
        # 转换数值类型
        processed['face_count'] = int(row['face_count'])
        processed['texture_count'] = int(row['texture_count'])
        processed['original_size_mb'] = float(row['original_size_mb'])
        processed['compressed_size_mb'] = float(row['compressed_size_mb'])
        processed['texture_size_mb'] = float(row['texture_size_mb'])
        
        # 处理峰值内存占用（可能为N/A）
        peak_memory = row.get('peak_memory_mb', 'N/A')
        if peak_memory == 'N/A' or peak_memory == '':
            processed['peak_memory_mb'] = None
        else:
            processed['peak_memory_mb'] = float(peak_memory)
        
        # 计算衍生指标
        processed['compression_ratio'] = self._calculate_compression_ratio(
            processed['original_size_mb'], processed['compressed_size_mb'])
        processed['texture_percentage'] = self._calculate_texture_percentage(
            processed['original_size_mb'], processed['texture_size_mb'])
        
        return processed
    
    def _calculate_compression_ratio(self, original: float, compressed: float) -> float:
        """计算压缩率"""
        if original == 0:
            return 0.0
        return (original - compressed) / original * 100
    
    def _calculate_texture_percentage(self, original: float, texture: float) -> float:
        """计算纹理占比"""
        if original == 0:
            return 0.0
        return texture / original * 100
    
    def get_formats(self) -> List[str]:
        """获取所有支持的格式"""
        return sorted(list(set(row['format'] for row in self.data)))
    
    def get_models(self) -> List[str]:
        """获取所有模型名称"""
        return sorted(list(set(row['model_name'] for row in self.data)))
    
    def get_format_data(self, format_type: str) -> List[Dict]:
        """获取指定格式的所有数据"""
        return [row for row in self.data if row['format'] == format_type]
    
    def get_model_data(self, model_name: str) -> List[Dict]:
        """获取指定模型的所有数据"""
        return [row for row in self.data if row['model_name'] == model_name]
    
    def analyze_format_performance(self, format_type: str) -> Dict:
        """
        分析指定格式的性能
        
        Args:
            format_type: 格式类型
            
        Returns:
            格式性能分析结果
        """
        format_data = self.get_format_data(format_type)
        
        if not format_data:
            return {}
        
        # 基础统计
        original_sizes = [row['original_size_mb'] for row in format_data]
        compressed_sizes = [row['compressed_size_mb'] for row in format_data]
        compression_ratios = [row['compression_ratio'] for row in format_data]
        texture_percentages = [row['texture_percentage'] for row in format_data]
        
        # 内存统计（过滤掉None值）
        memory_data = [row['peak_memory_mb'] for row in format_data if row['peak_memory_mb'] is not None]
        
        analysis = {
            'format': format_type,
            'count': len(format_data),
            'avg_original_size': statistics.mean(original_sizes),
            'avg_compressed_size': statistics.mean(compressed_sizes),
            'avg_compression_ratio': statistics.mean(compression_ratios),
            'avg_texture_percentage': statistics.mean(texture_percentages),
            'min_original_size': min(original_sizes),
            'max_original_size': max(original_sizes),
            'min_compressed_size': min(compressed_sizes),
            'max_compressed_size': max(compressed_sizes),
        }
        
        # 添加内存统计（如果有数据）
        if memory_data:
            analysis.update({
                'avg_peak_memory': statistics.mean(memory_data),
                'min_peak_memory': min(memory_data),
                'max_peak_memory': max(memory_data),
                'memory_data_count': len(memory_data)
            })
        else:
            analysis.update({
                'avg_peak_memory': None,
                'min_peak_memory': None,
                'max_peak_memory': None,
                'memory_data_count': 0
            })
        
        return analysis
    
    def analyze_all_formats(self) -> Dict[str, Dict]:
        """分析所有格式的性能"""
        formats = self.get_formats()
        results = {}
        
        for format_type in formats:
            results[format_type] = self.analyze_format_performance(format_type)
        
        return results
    
    def find_best_format(self, criteria: str = 'compression') -> Tuple[str, Dict]:
        """
        根据指定标准找到最佳格式
        
        Args:
            criteria: 评估标准 ('compression', 'memory', 'size', 'texture')
            
        Returns:
            (最佳格式, 性能数据)
        """
        format_analyses = self.analyze_all_formats()
        
        if criteria == 'compression':
            # 压缩率最高
            best_format = max(format_analyses.keys(), 
                             key=lambda f: format_analyses[f]['avg_compression_ratio'])
        elif criteria == 'memory':
            # 内存占用最低
            best_format = min(format_analyses.keys(), 
                             key=lambda f: format_analyses[f]['avg_peak_memory'] or float('inf'))
        elif criteria == 'size':
            # 压缩后大小最小
            best_format = min(format_analyses.keys(), 
                             key=lambda f: format_analyses[f]['avg_compressed_size'])
        elif criteria == 'texture':
            # 纹理占比最低
            best_format = min(format_analyses.keys(), 
                             key=lambda f: format_analyses[f]['avg_texture_percentage'])
        else:
            raise ValueError(f"不支持的评估标准: {criteria}")
        
        return best_format, format_analyses[best_format]
    
    def generate_comparison_matrix(self) -> Dict:
        """生成格式对比矩阵"""
        formats = self.get_formats()
        models = self.get_models()
        
        matrix = {
            'formats': formats,
            'models': models,
            'comparisons': {}
        }
        
        for model in models:
            model_data = self.get_model_data(model)
            matrix['comparisons'][model] = {}
            
            for format_type in formats:
                format_row = next((row for row in model_data if row['format'] == format_type), None)
                if format_row:
                    matrix['comparisons'][model][format_type] = {
                        'original_size': format_row['original_size_mb'],
                        'compressed_size': format_row['compressed_size_mb'],
                        'compression_ratio': format_row['compression_ratio'],
                        'texture_percentage': format_row['texture_percentage'],
                        'peak_memory': format_row['peak_memory_mb']
                    }
        
        return matrix
    
    def get_memory_analysis(self) -> Dict:
        """获取内存分析结果"""
        memory_data = [row for row in self.data if row['peak_memory_mb'] is not None]
        
        if not memory_data:
            return {'error': '没有可用的内存数据'}
        
        # 按格式分组
        format_memory = {}
        for row in memory_data:
            format_type = row['format']
            if format_type not in format_memory:
                format_memory[format_type] = []
            format_memory[format_type].append(row['peak_memory_mb'])
        
        # 计算统计信息
        analysis = {
            'total_models_with_memory_data': len(memory_data),
            'formats': {}
        }
        
        for format_type, memory_values in format_memory.items():
            analysis['formats'][format_type] = {
                'count': len(memory_values),
                'avg_memory': statistics.mean(memory_values),
                'min_memory': min(memory_values),
                'max_memory': max(memory_values),
                'median_memory': statistics.median(memory_values)
            }
        
        return analysis
    
    def export_summary_data(self, output_dir: Path = None) -> Dict[str, str]:
        """
        导出汇总数据到文件
        
        Args:
            output_dir: 输出目录
            
        Returns:
            生成的文件路径字典
        """
        if output_dir is None:
            output_dir = self.charts_dir
        
        output_dir.mkdir(exist_ok=True)
        generated_files = {}
        
        # 1. 生成JSON格式的汇总数据
        summary_data = self.analyze_all_formats()
        json_path = output_dir / 'summary_report.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        generated_files['json'] = str(json_path)
        
        # 2. 生成CSV格式的汇总数据
        csv_path = output_dir / 'summary_statistics.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                '格式', '平均原始大小(MB)', '平均压缩后大小(MB)', 
                '平均压缩率(%)', '平均纹理占比(%)', '平均峰值内存(MB)', '样本数量'
            ])
            
            for format_type, stats in summary_data.items():
                writer.writerow([
                    format_type.upper(),
                    f"{stats['avg_original_size']:.1f}",
                    f"{stats['avg_compressed_size']:.1f}",
                    f"{stats['avg_compression_ratio']:.1f}",
                    f"{stats['avg_texture_percentage']:.1f}",
                    f"{stats['avg_peak_memory']:.1f}" if stats['avg_peak_memory'] else "N/A",
                    stats['count']
                ])
        generated_files['csv'] = str(csv_path)
        
        # 3. 生成模型对比数据
        comparison_data = self.generate_comparison_matrix()
        comparison_path = output_dir / 'model_comparison_data.json'
        with open(comparison_path, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2, ensure_ascii=False)
        generated_files['comparison'] = str(comparison_path)
        
        # 4. 生成内存分析数据
        memory_analysis = self.get_memory_analysis()
        memory_path = output_dir / 'memory_analysis.json'
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(memory_analysis, f, indent=2, ensure_ascii=False)
        generated_files['memory'] = str(memory_path)
        
        return generated_files