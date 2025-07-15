#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML报告生成器
使用Chart.js生成交互式图表
"""

import json
import csv
from pathlib import Path

class HTMLReportGenerator:
    def __init__(self, csv_path):
        """初始化报告生成器"""
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
    
    def generate_html_report(self):
        """生成HTML报告"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D模型格式分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .chart-container {
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #fafafa;
        }
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            font-size: 1.2em;
        }
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .data-table th, .data-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: center;
        }
        .data-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .data-table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>3D模型格式分析报告</h1>
        
        <div class="summary-stats">
            <div class="stat-card">
                <h3>FBX 平均压缩率</h3>
                <div class="value" id="fbx-compression">-</div>
            </div>
            <div class="stat-card">
                <h3>OBJ 平均压缩率</h3>
                <div class="value" id="obj-compression">-</div>
            </div>
            <div class="stat-card">
                <h3>GLTF 平均压缩率</h3>
                <div class="value" id="gltf-compression">-</div>
            </div>
            <div class="stat-card">
                <h3>GLB 平均压缩率</h3>
                <div class="value" id="glb-compression">-</div>
            </div>
        </div>

        <div class="chart-container">
            <h2>素材大小对比（压缩前后）</h2>
            <canvas id="sizeChart" width="400" height="200"></canvas>
        </div>

        <div class="chart-container">
            <h2>压缩率对比</h2>
            <canvas id="compressionChart" width="400" height="200"></canvas>
        </div>

        <div class="chart-container">
            <h2>纹理占比对比</h2>
            <canvas id="textureChart" width="400" height="200"></canvas>
        </div>

        <div class="chart-container">
            <h2>详细数据表格</h2>
            <table class="data-table" id="dataTable">
                <thead>
                    <tr>
                        <th>模型名称</th>
                        <th>面数</th>
                        <th>纹理数量</th>
                        <th>格式</th>
                        <th>原始大小(MB)</th>
                        <th>压缩后大小(MB)</th>
                        <th>压缩率(%)</th>
                        <th>纹理占比(%)</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // 数据
        const chartData = """ + json.dumps(self.prepare_chart_data()) + """;
        
        // 更新统计卡片
        function updateStats() {
            const formats = ['fbx', 'obj', 'gltf', 'glb'];
            formats.forEach(format => {
                const formatData = chartData.filter(item => item.format.toLowerCase() === format);
                if (formatData.length > 0) {
                    const avgCompression = formatData.reduce((sum, item) => sum + item.compression_ratio, 0) / formatData.length;
                    document.getElementById(format + '-compression').textContent = avgCompression.toFixed(1) + '%';
                }
            });
        }
        
        // 填充数据表格
        function populateTable() {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            
            chartData.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.model}</td>
                    <td>${item.face_count.toLocaleString()}</td>
                    <td>${item.texture_count}</td>
                    <td>${item.format}</td>
                    <td>${item.original_size.toFixed(1)}</td>
                    <td>${item.compressed_size.toFixed(1)}</td>
                    <td>${item.compression_ratio.toFixed(1)}</td>
                    <td>${item.texture_percentage.toFixed(1)}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        // 创建大小对比图
        function createSizeChart() {
            const ctx = document.getElementById('sizeChart').getContext('2d');
            
            const models = [...new Set(chartData.map(item => item.model))];
            const formats = ['FBX', 'OBJ', 'GLTF', 'GLB'];
            const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'];
            
            const datasets = formats.map((format, index) => {
                const originalData = models.map(model => {
                    const item = chartData.find(d => d.model === model && d.format === format);
                    return item ? item.original_size : 0;
                });
                
                const compressedData = models.map(model => {
                    const item = chartData.find(d => d.model === model && d.format === format);
                    return item ? item.compressed_size : 0;
                });
                
                return [
                    {
                        label: `${format} 原始大小`,
                        data: originalData,
                        backgroundColor: colors[index],
                        borderColor: colors[index],
                        borderWidth: 2
                    },
                    {
                        label: `${format} 压缩后大小`,
                        data: compressedData,
                        backgroundColor: colors[index] + '80',
                        borderColor: colors[index],
                        borderWidth: 2
                    }
                ];
            }).flat();
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: models,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '大小 (MB)'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: '各格式压缩前后大小对比'
                        }
                    }
                }
            });
        }
        
        // 创建压缩率对比图
        function createCompressionChart() {
            const ctx = document.getElementById('compressionChart').getContext('2d');
            
            const formats = ['FBX', 'OBJ', 'GLTF', 'GLB'];
            const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'];
            
            const avgCompression = formats.map(format => {
                const formatData = chartData.filter(item => item.format === format);
                return formatData.length > 0 ? 
                    formatData.reduce((sum, item) => sum + item.compression_ratio, 0) / formatData.length : 0;
            });
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: formats,
                    datasets: [{
                        label: '平均压缩率 (%)',
                        data: avgCompression,
                        backgroundColor: colors,
                        borderColor: colors,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '压缩率 (%)'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: '各格式平均压缩率对比'
                        }
                    }
                }
            });
        }
        
        // 创建纹理占比图
        function createTextureChart() {
            const ctx = document.getElementById('textureChart').getContext('2d');
            
            const formats = ['FBX', 'OBJ', 'GLTF', 'GLB'];
            const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'];
            
            const avgTexture = formats.map(format => {
                const formatData = chartData.filter(item => item.format === format);
                return formatData.length > 0 ? 
                    formatData.reduce((sum, item) => sum + item.texture_percentage, 0) / formatData.length : 0;
            });
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: formats,
                    datasets: [{
                        label: '平均纹理占比 (%)',
                        data: avgTexture,
                        backgroundColor: colors,
                        borderColor: colors,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: '纹理占比 (%)'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: '各格式平均纹理占比对比'
                        }
                    }
                }
            });
        }
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            updateStats();
            populateTable();
            createSizeChart();
            createCompressionChart();
            createTextureChart();
        });
    </script>
</body>
</html>
        """
        
        with open(self.charts_dir / 'analysis_report.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✓ HTML报告已生成")
    
    def prepare_chart_data(self):
        """准备图表数据"""
        chart_data = []
        
        for row in self.data:
            chart_data.append({
                'model': row['model_name'].split('_')[0],  # 简化模型名
                'face_count': row['face_count'],
                'texture_count': row['texture_count'],
                'format': row['format'].upper(),
                'original_size': row['original_size_mb'],
                'compressed_size': row['compressed_size_mb'],
                'compression_ratio': row['compression_ratio'],
                'texture_percentage': row['texture_percentage']
            })
        
        return chart_data
    
    def generate_all_reports(self):
        """生成所有报告"""
        print("正在生成HTML报告...")
        self.generate_html_report()
        print(f"\nHTML报告已保存到 {self.charts_dir}/analysis_report.html")

def main():
    """主函数"""
    csv_path = Path("data/model_data.csv")
    
    if not csv_path.exists():
        print(f"错误：找不到数据文件 {csv_path}")
        return
    
    generator = HTMLReportGenerator(csv_path)
    generator.generate_all_reports()

if __name__ == "__main__":
    main()