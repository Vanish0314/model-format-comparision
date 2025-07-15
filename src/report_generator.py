#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成器模块
负责生成各种格式的分析报告
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, analyzer, memory_analyzer=None):
        """
        初始化报告生成器
        
        Args:
            analyzer: 模型分析器实例
            memory_analyzer: 内存分析器实例（可选）
        """
        self.analyzer = analyzer
        self.memory_analyzer = memory_analyzer
        self.charts_dir = Path("charts")
        self.charts_dir.mkdir(exist_ok=True)
    
    def generate_text_report(self) -> str:
        """生成详细的文本报告"""
        report_lines = [
            "=== 3D模型格式性能分析报告 ===",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "报告概述:",
            f"  分析模型数量: {len(self.analyzer.get_models())}",
            f"  支持格式数量: {len(self.analyzer.get_formats())}",
            f"  数据记录总数: {len(self.analyzer.data)}",
            ""
        ]
        
        # 各格式性能汇总
        report_lines.extend([
            "=== 各格式性能汇总 ===",
            ""
        ])
        
        format_analyses = self.analyzer.analyze_all_formats()
        for format_type, stats in format_analyses.items():
            report_lines.extend([
                f"{format_type.upper()} 格式:",
                f"  样本数量: {stats['count']}",
                f"  平均原始大小: {stats['avg_original_size']:.1f} MB",
                f"  平均压缩后大小: {stats['avg_compressed_size']:.1f} MB",
                f"  平均压缩率: {stats['avg_compression_ratio']:.1f}%",
                f"  平均纹理占比: {stats['avg_texture_percentage']:.1f}%",
            ])
            
            if stats['avg_peak_memory']:
                report_lines.append(f"  平均峰值内存: {stats['avg_peak_memory']:.1f} MB")
            else:
                report_lines.append("  平均峰值内存: N/A")
            
            report_lines.extend([
                f"  大小范围: {stats['min_original_size']:.1f} - {stats['max_original_size']:.1f} MB",
                ""
            ])
        
        # 最佳格式推荐
        report_lines.extend([
            "=== 最佳格式推荐 ===",
            ""
        ])
        
        criteria_list = [
            ('compression', '压缩率'),
            ('size', '文件大小'),
            ('memory', '内存占用'),
            ('texture', '纹理效率')
        ]
        
        for criteria, description in criteria_list:
            try:
                best_format, stats = self.analyzer.find_best_format(criteria)
                report_lines.append(f"最佳{description}格式: {best_format.upper()}")
                if criteria == 'memory' and stats['avg_peak_memory']:
                    report_lines.append(f"  平均内存占用: {stats['avg_peak_memory']:.1f} MB")
                elif criteria == 'compression':
                    report_lines.append(f"  平均压缩率: {stats['avg_compression_ratio']:.1f}%")
                elif criteria == 'size':
                    report_lines.append(f"  平均压缩后大小: {stats['avg_compressed_size']:.1f} MB")
                elif criteria == 'texture':
                    report_lines.append(f"  平均纹理占比: {stats['avg_texture_percentage']:.1f}%")
                report_lines.append("")
            except Exception as e:
                report_lines.append(f"无法确定最佳{description}格式: {e}")
                report_lines.append("")
        
        # 详细模型数据
        report_lines.extend([
            "=== 详细模型数据 ===",
            ""
        ])
        
        models = self.analyzer.get_models()
        for model in models:
            model_data = self.analyzer.get_model_data(model)
            if model_data:
                report_lines.append(f"模型: {model}")
                report_lines.append(f"  面数: {model_data[0]['face_count']:,}")
                report_lines.append(f"  纹理数量: {model_data[0]['texture_count']}")
                
                for row in model_data:
                    format_info = f"  {row['format'].upper()}:"
                    format_info += f" 原始{row['original_size_mb']:.1f}MB"
                    format_info += f", 压缩{row['compressed_size_mb']:.1f}MB"
                    format_info += f", 压缩率{row['compression_ratio']:.1f}%"
                    
                    if row['peak_memory_mb']:
                        format_info += f", 内存{row['peak_memory_mb']:.1f}MB"
                    else:
                        format_info += ", 内存N/A"
                    
                    report_lines.append(format_info)
                report_lines.append("")
        
        # 内存分析（如果有内存分析器）
        if self.memory_analyzer:
            report_lines.extend([
                "=== 内存占用分析 ===",
                ""
            ])
            
            memory_stats = self.memory_analyzer.get_memory_statistics()
            if 'error' not in memory_stats:
                report_lines.extend([
                    "总体内存统计:",
                    f"  有内存数据的模型: {memory_stats['total_count']}",
                    f"  平均内存占用: {memory_stats['mean']:.1f} MB",
                    f"  中位数内存占用: {memory_stats['median']:.1f} MB",
                    f"  内存范围: {memory_stats['min']:.1f} - {memory_stats['max']:.1f} MB",
                    ""
                ])
                
                # 内存效率排名
                efficient_formats = self.memory_analyzer.find_memory_efficient_formats()
                report_lines.extend([
                    "内存效率排名 (从低到高):",
                    ""
                ])
                
                for i, (format_type, avg_memory) in enumerate(efficient_formats, 1):
                    report_lines.append(f"{i}. {format_type.upper()}: {avg_memory:.1f} MB")
                report_lines.append("")
        
        # 保存报告
        report_path = self.charts_dir / 'analysis_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        return str(report_path)
    
    def generate_html_report(self) -> str:
        """生成HTML格式的报告"""
        html_content = self._generate_html_header()
        
        # 添加概述部分
        html_content += self._generate_overview_section()
        
        # 添加性能对比部分
        html_content += self._generate_performance_comparison_section()
        
        # 添加内存分析部分
        if self.memory_analyzer:
            html_content += self._generate_memory_analysis_section()
        
        # 添加详细数据部分
        html_content += self._generate_detailed_data_section()
        
        # 添加结论部分
        html_content += self._generate_conclusion_section()
        
        html_content += self._generate_html_footer()
        
        # 保存HTML文件
        html_path = self.charts_dir / 'analysis_report.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(html_path)
    
    def _generate_html_header(self) -> str:
        """生成HTML头部"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D模型格式性能分析报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 25px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h4 {{
            margin: 0 0 10px 0;
            font-size: 1.1em;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .format-comparison {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .format-card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            background-color: #fafafa;
        }}
        .format-card h4 {{
            color: #2c3e50;
            margin-top: 0;
            text-align: center;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            font-weight: 500;
            color: #555;
        }}
        .metric-value {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .memory-section {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .ranking {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .ranking ol {{
            margin: 0;
            padding-left: 20px;
        }}
        .ranking li {{
            margin: 5px 0;
            font-weight: 500;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .data-table th, .data-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        .data-table th {{
            background-color: #3498db;
            color: white;
        }}
        .data-table tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .conclusion {{
            background-color: #e8f5e8;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #27ae60;
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            font-style: italic;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>3D模型格式性能分析报告</h1>
        <div class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
"""
    
    def _generate_overview_section(self) -> str:
        """生成概述部分"""
        models = self.analyzer.get_models()
        formats = self.analyzer.get_formats()
        
        return f"""
        <h2>报告概述</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <h4>分析模型数量</h4>
                <div class="stat-value">{len(models)}</div>
            </div>
            <div class="stat-card">
                <h4>支持格式数量</h4>
                <div class="stat-value">{len(formats)}</div>
            </div>
            <div class="stat-card">
                <h4>数据记录总数</h4>
                <div class="stat-value">{len(self.analyzer.data)}</div>
            </div>
            <div class="stat-card">
                <h4>支持格式</h4>
                <div class="stat-value">{', '.join(formats).upper()}</div>
            </div>
        </div>
"""
    
    def _generate_performance_comparison_section(self) -> str:
        """生成性能对比部分"""
        format_analyses = self.analyzer.analyze_all_formats()
        
        html = """
        <h2>各格式性能对比</h2>
        <div class="format-comparison">
"""
        
        for format_type, stats in format_analyses.items():
            html += f"""
            <div class="format-card">
                <h4>{format_type.upper()} 格式</h4>
                <div class="metric">
                    <span class="metric-label">样本数量:</span>
                    <span class="metric-value">{stats['count']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">平均原始大小:</span>
                    <span class="metric-value">{stats['avg_original_size']:.1f} MB</span>
                </div>
                <div class="metric">
                    <span class="metric-label">平均压缩后大小:</span>
                    <span class="metric-value">{stats['avg_compressed_size']:.1f} MB</span>
                </div>
                <div class="metric">
                    <span class="metric-label">平均压缩率:</span>
                    <span class="metric-value">{stats['avg_compression_ratio']:.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">平均纹理占比:</span>
                    <span class="metric-value">{stats['avg_texture_percentage']:.1f}%</span>
                </div>
"""
            
            if stats['avg_peak_memory']:
                html += f"""
                <div class="metric">
                    <span class="metric-label">平均峰值内存:</span>
                    <span class="metric-value">{stats['avg_peak_memory']:.1f} MB</span>
                </div>
"""
            else:
                html += """
                <div class="metric">
                    <span class="metric-label">平均峰值内存:</span>
                    <span class="metric-value">N/A</span>
                </div>
"""
            
            html += """
            </div>
"""
        
        html += """
        </div>
"""
        
        return html
    
    def _generate_memory_analysis_section(self) -> str:
        """生成内存分析部分"""
        memory_stats = self.memory_analyzer.get_memory_statistics()
        
        if 'error' in memory_stats:
            return """
        <h2>内存占用分析</h2>
        <div class="memory-section">
            <p>没有可用的内存数据进行分析。</p>
        </div>
"""
        
        efficient_formats = self.memory_analyzer.find_memory_efficient_formats()
        
        html = """
        <h2>内存占用分析</h2>
        <div class="memory-section">
            <h3>总体内存统计</h3>
            <div class="stats-grid">
"""
        
        html += f"""
                <div class="stat-card">
                    <h4>有内存数据的模型</h4>
                    <div class="stat-value">{memory_stats['total_count']}</div>
                </div>
                <div class="stat-card">
                    <h4>平均内存占用</h4>
                    <div class="stat-value">{memory_stats['mean']:.1f} MB</div>
                </div>
                <div class="stat-card">
                    <h4>中位数内存占用</h4>
                    <div class="stat-value">{memory_stats['median']:.1f} MB</div>
                </div>
                <div class="stat-card">
                    <h4>内存范围</h4>
                    <div class="stat-value">{memory_stats['min']:.1f} - {memory_stats['max']:.1f} MB</div>
                </div>
            </div>
            
            <h3>内存效率排名</h3>
            <div class="ranking">
                <ol>
"""
        
        for format_type, avg_memory in efficient_formats:
            html += f"""
                    <li>{format_type.upper()}: {avg_memory:.1f} MB</li>
"""
        
        html += """
                </ol>
            </div>
        </div>
"""
        
        return html
    
    def _generate_detailed_data_section(self) -> str:
        """生成详细数据部分"""
        models = self.analyzer.get_models()
        
        html = """
        <h2>详细模型数据</h2>
        <table class="data-table">
            <thead>
                <tr>
                    <th>模型名称</th>
                    <th>面数</th>
                    <th>纹理数量</th>
                    <th>格式</th>
                    <th>原始大小(MB)</th>
                    <th>压缩后大小(MB)</th>
                    <th>压缩率(%)</th>
                    <th>峰值内存(MB)</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for model in models:
            model_data = self.analyzer.get_model_data(model)
            if model_data:
                for row in model_data:
                    memory_value = f"{row['peak_memory_mb']:.1f}" if row['peak_memory_mb'] else "N/A"
                    html += f"""
                <tr>
                    <td>{row['model_name']}</td>
                    <td>{row['face_count']:,}</td>
                    <td>{row['texture_count']}</td>
                    <td>{row['format'].upper()}</td>
                    <td>{row['original_size_mb']:.1f}</td>
                    <td>{row['compressed_size_mb']:.1f}</td>
                    <td>{row['compression_ratio']:.1f}</td>
                    <td>{memory_value}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
"""
        
        return html
    
    def _generate_conclusion_section(self) -> str:
        """生成结论部分"""
        try:
            best_compression, _ = self.analyzer.find_best_format('compression')
            best_size, _ = self.analyzer.find_best_format('size')
            best_memory, _ = self.analyzer.find_best_format('memory')
        except:
            best_compression = best_size = best_memory = "N/A"
        
        return f"""
        <h2>结论与建议</h2>
        <div class="conclusion">
            <h3>最佳格式推荐</h3>
            <ul>
                <li><strong>最佳压缩率格式:</strong> {best_compression.upper()}</li>
                <li><strong>最小文件大小格式:</strong> {best_size.upper()}</li>
                <li><strong>最低内存占用格式:</strong> {best_memory.upper()}</li>
            </ul>
            
            <h3>使用建议</h3>
            <ul>
                <li><strong>Web应用:</strong> 推荐使用GLTF/GLB格式，专为Web优化，加载速度快</li>
                <li><strong>游戏开发:</strong> 根据平台需求选择，移动端推荐GLB，PC端可考虑FBX</li>
                <li><strong>3D建模软件:</strong> FBX格式兼容性最好，支持复杂的材质和动画</li>
                <li><strong>开源项目:</strong> OBJ格式简单易用，但文件较大</li>
            </ul>
            
            <h3>注意事项</h3>
            <ul>
                <li>内存占用数据仅供参考，实际使用中可能因硬件和软件环境而异</li>
                <li>压缩率高的格式不一定在所有场景下都是最佳选择</li>
                <li>选择格式时应综合考虑文件大小、加载速度、内存占用和功能需求</li>
            </ul>
        </div>
"""
    
    def _generate_html_footer(self) -> str:
        """生成HTML尾部"""
        return """
    </div>
</body>
</html>
"""
    
    def generate_all_reports(self) -> Dict[str, str]:
        """生成所有类型的报告"""
        generated_files = {}
        
        # 生成文本报告
        text_report_path = self.generate_text_report()
        generated_files['text'] = text_report_path
        
        # 生成HTML报告
        html_report_path = self.generate_html_report()
        generated_files['html'] = html_report_path
        
        # 导出汇总数据
        summary_files = self.analyzer.export_summary_data()
        generated_files.update(summary_files)
        
        # 生成内存分析报告（如果有内存分析器）
        if self.memory_analyzer:
            memory_files = self.memory_analyzer.export_memory_data(self.charts_dir)
            generated_files.update(memory_files)
        
        return generated_files