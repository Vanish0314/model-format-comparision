#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析器单元测试
"""

import sys
import unittest
from pathlib import Path
import tempfile
import csv

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.analyzer import ModelAnalyzer
from src.memory_analyzer import MemoryAnalyzer


class TestModelAnalyzer(unittest.TestCase):
    """测试模型分析器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时CSV文件
        self.temp_dir = tempfile.mkdtemp()
        self.csv_path = Path(self.temp_dir) / "test_data.csv"
        
        # 创建测试数据
        test_data = [
            ['model_name', 'face_count', 'texture_count', 'format', 'original_size_mb', 'compressed_size_mb', 'texture_size_mb', 'peak_memory_mb'],
            ['TestModel1', '1000', '2', 'fbx', '10.0', '8.0', '5.0', '20.0'],
            ['TestModel1', '1000', '2', 'obj', '12.0', '9.0', '5.0', '25.0'],
            ['TestModel2', '2000', '1', 'fbx', '15.0', '12.0', '3.0', '30.0'],
            ['TestModel2', '2000', '1', 'gltf', '14.0', '11.0', '3.0', '28.0'],
        ]
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(test_data)
        
        # 初始化分析器
        self.analyzer = ModelAnalyzer(str(self.csv_path))
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_data(self):
        """测试数据加载"""
        self.assertEqual(len(self.analyzer.data), 4)
        self.assertEqual(len(self.analyzer.get_formats()), 3)  # fbx, obj, gltf
        self.assertEqual(len(self.analyzer.get_models()), 2)   # TestModel1, TestModel2
    
    def test_compression_ratio_calculation(self):
        """测试压缩率计算"""
        fbx_data = self.analyzer.get_format_data('fbx')
        self.assertEqual(len(fbx_data), 2)
        
        # 检查压缩率计算
        for row in fbx_data:
            expected_ratio = (row['original_size_mb'] - row['compressed_size_mb']) / row['original_size_mb'] * 100
            self.assertAlmostEqual(row['compression_ratio'], expected_ratio, places=1)
    
    def test_texture_percentage_calculation(self):
        """测试纹理占比计算"""
        for row in self.analyzer.data:
            expected_percentage = row['texture_size_mb'] / row['original_size_mb'] * 100
            self.assertAlmostEqual(row['texture_percentage'], expected_percentage, places=1)
    
    def test_format_analysis(self):
        """测试格式分析"""
        format_analyses = self.analyzer.analyze_all_formats()
        
        self.assertIn('fbx', format_analyses)
        self.assertIn('obj', format_analyses)
        self.assertIn('gltf', format_analyses)
        
        fbx_stats = format_analyses['fbx']
        self.assertEqual(fbx_stats['count'], 2)
        self.assertAlmostEqual(fbx_stats['avg_original_size'], 12.5, places=1)
        self.assertAlmostEqual(fbx_stats['avg_compressed_size'], 10.0, places=1)
    
    def test_best_format_finding(self):
        """测试最佳格式查找"""
        best_compression, _ = self.analyzer.find_best_format('compression')
        best_size, _ = self.analyzer.find_best_format('size')
        
        # 根据测试数据，gltf应该有最好的压缩率
        self.assertIn(best_compression, ['fbx', 'obj', 'gltf'])
        self.assertIn(best_size, ['fbx', 'obj', 'gltf'])
    
    def test_memory_analysis(self):
        """测试内存分析"""
        memory_analyzer = MemoryAnalyzer(self.analyzer.data)
        
        # 检查内存统计
        memory_stats = memory_analyzer.get_memory_statistics()
        self.assertNotIn('error', memory_stats)
        self.assertEqual(memory_stats['total_count'], 4)
        
        # 检查格式内存分析
        format_memory = memory_analyzer.analyze_memory_by_format()
        self.assertIn('fbx', format_memory)
        self.assertIn('obj', format_memory)
        self.assertIn('gltf', format_memory)
        
        # 检查内存效率排名
        efficient_formats = memory_analyzer.find_memory_efficient_formats()
        self.assertEqual(len(efficient_formats), 3)
        
        # 检查相关性分析
        correlation = memory_analyzer.get_memory_correlation_analysis()
        self.assertIn('face_count_correlation', correlation)
        self.assertIn('file_size_correlation', correlation)
        self.assertIn('texture_count_correlation', correlation)


class TestMemoryAnalyzer(unittest.TestCase):
    """测试内存分析器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建测试数据
        self.test_data = [
            {
                'model_name': 'Test1',
                'face_count': 1000,
                'texture_count': 2,
                'format': 'fbx',
                'original_size_mb': 10.0,
                'compressed_size_mb': 8.0,
                'texture_size_mb': 5.0,
                'peak_memory_mb': 20.0,
                'compression_ratio': 20.0,
                'texture_percentage': 50.0
            },
            {
                'model_name': 'Test2',
                'face_count': 2000,
                'texture_count': 1,
                'format': 'obj',
                'original_size_mb': 15.0,
                'compressed_size_mb': 12.0,
                'texture_size_mb': 3.0,
                'peak_memory_mb': 30.0,
                'compression_ratio': 20.0,
                'texture_percentage': 20.0
            }
        ]
        
        self.memory_analyzer = MemoryAnalyzer(self.test_data)
    
    def test_memory_statistics(self):
        """测试内存统计"""
        stats = self.memory_analyzer.get_memory_statistics()
        
        self.assertEqual(stats['total_count'], 2)
        self.assertEqual(stats['mean'], 25.0)
        self.assertEqual(stats['min'], 20.0)
        self.assertEqual(stats['max'], 30.0)
    
    def test_format_memory_analysis(self):
        """测试格式内存分析"""
        format_analysis = self.memory_analyzer.analyze_memory_by_format()
        
        self.assertIn('fbx', format_analysis)
        self.assertIn('obj', format_analysis)
        
        fbx_stats = format_analysis['fbx']
        self.assertEqual(fbx_stats['count'], 1)
        self.assertEqual(fbx_stats['mean'], 20.0)
    
    def test_memory_efficiency_ranking(self):
        """测试内存效率排名"""
        ranking = self.memory_analyzer.find_memory_efficient_formats()
        
        self.assertEqual(len(ranking), 2)
        # fbx应该排在obj前面（内存更少）
        self.assertEqual(ranking[0][0], 'fbx')
        self.assertEqual(ranking[1][0], 'obj')
    
    def test_correlation_analysis(self):
        """测试相关性分析"""
        correlation = self.memory_analyzer.get_memory_correlation_analysis()
        
        self.assertIn('face_count_correlation', correlation)
        self.assertIn('file_size_correlation', correlation)
        self.assertIn('texture_count_correlation', correlation)
        
        # 相关性值应该在-1到1之间
        for value in correlation.values():
            self.assertGreaterEqual(value, -1.0)
            self.assertLessEqual(value, 1.0)


if __name__ == '__main__':
    unittest.main()