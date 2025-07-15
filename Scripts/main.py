import json
import os
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

def load_raw_data():
    """加载RawData目录下的所有模型数据"""
    with open('RawData/all_models_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_import_time_comparison(models_data):
    """创建导入时间对比图表（对数坐标+缺失标注）"""
    models = []
    formats = ['fbx', 'obj', 'glTF', 'glb']
    data_by_format = {fmt: [] for fmt in formats}
    face_counts = []
    valid_indices = []
    # 先筛选出至少有一个格式有import_time_ms的模型
    for idx, (model_name, model_data) in enumerate(models_data.items()):
        has_data = any(
            fmt in model_data['formats'] and 'import_time_ms' in model_data['formats'][fmt]
            for fmt in formats
        )
        if has_data:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
            valid_indices.append(idx)
    # 按照筛选后的模型收集数据
    for fmt in formats:
        for idx in valid_indices:
            model_name = list(models_data.keys())[idx]
            model_data = models_data[model_name]
            if fmt in model_data['formats'] and 'import_time_ms' in model_data['formats'][fmt]:
                data_by_format[fmt].append(model_data['formats'][fmt]['import_time_ms'] / 1000)
            else:
                data_by_format[fmt].append(None)  # 用None标记缺失
    fig, ax = plt.subplots(figsize=(12, 8))
    x = np.arange(len(models))
    width = 0.2
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = data_by_format[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for j, (bar, v) in enumerate(zip(bars, values)):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}s', ha='center', va='bottom', fontsize=8, zorder=3)
    ax.set_xlabel('Model (Face Count)', fontsize=12)
    ax.set_ylabel('Import Time (seconds, log scale)', fontsize=12)
    ax.set_title('Import Time Comparison: FBX vs OBJ vs glTF vs GLB', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [f'{model.split("_")[0]}\n({face}k faces)' for model, face in zip(models, face_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    ax.set_yscale('log')
    ax.annotate('注：y轴为对数坐标，缺失数据以红字标注', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/import_time_comparison.html', 'Import Time Comparison', 'Comparison of import times across different 3D file formats (log scale, missing data marked)')

def create_size_memory_comparison(models_data):
    """创建素材大小和内存占用对比图表（对数坐标+缺失标注）"""
    models = []
    formats = ['fbx', 'obj', 'glTF', 'glb']
    size_before_data = {fmt: [] for fmt in formats}
    size_after_data = {fmt: [] for fmt in formats}
    memory_data = {fmt: [] for fmt in formats}
    face_counts = []
    valid_indices = []
    # 只保留至少有一个格式有size_before_mb/size_after_mb/peak_memory_mb的模型
    for idx, (model_name, model_data) in enumerate(models_data.items()):
        has_data = False
        for fmt in formats:
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                if any(fmt_data.get(k, None) not in [None, 0] for k in ['size_before_mb', 'size_after_mb', 'peak_memory_mb']):
                    has_data = True
        if has_data:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
            valid_indices.append(idx)
    for fmt in formats:
        for idx in valid_indices:
            model_name = list(models_data.keys())[idx]
            model_data = models_data[model_name]
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                size_before_data[fmt].append(fmt_data.get('size_before_mb', None))
                size_after_data[fmt].append(fmt_data.get('size_after_mb', None))
                memory_data[fmt].append(fmt_data.get('peak_memory_mb', None))
            else:
                size_before_data[fmt].append(None)
                size_after_data[fmt].append(None)
                memory_data[fmt].append(None)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 16))
    x = np.arange(len(models))
    width = 0.2
    # 图1：压缩前大小对比
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = size_before_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax1.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax1.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f}', ha='center', va='bottom', fontsize=8, zorder=3)
    ax1.set_ylabel('Size (MB, log scale)', fontsize=12)
    ax1.set_title('File Size Before Compression', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([model.split('_')[0] for model in models], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, which='both', zorder=1)
    ax1.set_yscale('log')
    # 图2：压缩后大小对比
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = size_after_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax2.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax2.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f}', ha='center', va='bottom', fontsize=8, zorder=3)
    ax2.set_ylabel('Size (MB, log scale)', fontsize=12)
    ax2.set_title('File Size After Compression', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([model.split('_')[0] for model in models], rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, which='both', zorder=1)
    ax2.set_yscale('log')
    # 图3：峰值内存占用对比
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = memory_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax3.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax3.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v is not None and v > 0:
                ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f}', ha='center', va='bottom', fontsize=8, zorder=3)
    ax3.set_xlabel('Model (Face Count)', fontsize=12)
    ax3.set_ylabel('Memory (MB, log scale)', fontsize=12)
    ax3.set_title('Peak Memory Usage', fontsize=14, fontweight='bold')
    ax3.set_xticks(x)
    labels = [f'{model.split("_")[0]}\n({face}k faces)' for model, face in zip(models, face_counts)]
    ax3.set_xticklabels(labels, rotation=45, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3, which='both', zorder=1)
    ax3.set_yscale('log')
    ax3.annotate('注：y轴为对数坐标，缺失数据以红字标注', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/size_memory_comparison.html', 'File Size and Memory Usage Comparison', 'Comparison of file sizes (before/after compression) and peak memory usage (log scale, missing data marked)')

def create_compression_texture_ratio(models_data):
    """创建压缩率和纹理占比图表（对数坐标+缺失标注）"""
    models = []
    formats = ['fbx', 'obj', 'glTF', 'glb']
    compression_ratio_data = {fmt: [] for fmt in formats}
    texture_ratio_data = {fmt: [] for fmt in formats}
    face_counts = []
    valid_indices = []
    # 只保留至少有一个格式有size_before_mb和size_after_mb的模型
    for idx, (model_name, model_data) in enumerate(models_data.items()):
        has_data = False
        for fmt in formats:
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                if fmt_data.get('size_before_mb', None) not in [None, 0] and fmt_data.get('size_after_mb', None) not in [None, 0]:
                    has_data = True
        if has_data:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
            valid_indices.append(idx)
    for fmt in formats:
        for idx in valid_indices:
            model_name = list(models_data.keys())[idx]
            model_data = models_data[model_name]
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                size_before = fmt_data.get('size_before_mb', None)
                size_after = fmt_data.get('size_after_mb', None)
                texture_size = fmt_data.get('texture_size_mb', None)
                # 计算压缩率
                if size_before not in [None, 0] and size_after not in [None, 0]:
                    compression_ratio = (1 - size_after / size_before) * 100
                else:
                    compression_ratio = None
                compression_ratio_data[fmt].append(compression_ratio)
                # 计算纹理占比
                if size_before not in [None, 0] and texture_size not in [None, 0]:
                    texture_ratio = (texture_size / size_before) * 100
                else:
                    texture_ratio = None
                texture_ratio_data[fmt].append(texture_ratio)
            else:
                compression_ratio_data[fmt].append(None)
                texture_ratio_data[fmt].append(None)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    x = np.arange(len(models))
    width = 0.2
    # 图1：压缩率对比
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = compression_ratio_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax1.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax1.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}%', ha='center', va='bottom', fontsize=8, zorder=3)
    ax1.set_ylabel('Compression Ratio (%) (log scale)', fontsize=12)
    ax1.set_title('Compression Ratio Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([model.split('_')[0] for model in models], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, which='both', zorder=1)
    ax1.set_yscale('log')
    ax1.set_ylim(bottom=0.1)
    # 图2：纹理占比对比
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = texture_ratio_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax2.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax2.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}%', ha='center', va='bottom', fontsize=8, zorder=3)
    ax2.set_xlabel('Model (Face Count)', fontsize=12)
    ax2.set_ylabel('Texture Size Ratio (%) (log scale)', fontsize=12)
    ax2.set_title('Texture Size as Percentage of Total File Size', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    labels = [f'{model.split("_")[0]}\n({face}k faces)' for model, face in zip(models, face_counts)]
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, which='both', zorder=1)
    ax2.set_yscale('log')
    ax2.set_ylim(bottom=0.1)
    ax2.annotate('注：y轴为对数坐标，缺失数据以红字标注', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/compression_texture_ratio.html', 'Compression Ratio and Texture Size Analysis', 'Analysis of compression efficiency and texture size proportion (log scale, missing data marked)')

def create_gltf_glb_comparison(models_data):
    """创建glTF vs GLB加载时间和内存对比图表（对数坐标+缺失标注）"""
    models = []
    formats = ['glTF', 'glb']
    load_time_data = {fmt: [] for fmt in formats}
    load_memory_data = {fmt: [] for fmt in formats}
    face_counts = []
    valid_indices = []
    # 只保留至少有一个格式有load_time_ms/load_memory_mb的模型
    for idx, (model_name, model_data) in enumerate(models_data.items()):
        has_data = False
        for fmt in formats:
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                if fmt_data.get('load_time_ms', None) not in [None, 0] or fmt_data.get('load_memory_mb', None) not in [None, 0]:
                    has_data = True
        if has_data:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
            valid_indices.append(idx)
    for fmt in formats:
        for idx in valid_indices:
            model_name = list(models_data.keys())[idx]
            model_data = models_data[model_name]
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                load_time = fmt_data.get('load_time_ms', None)
                load_memory = fmt_data.get('load_memory_mb', None)
                load_time_data[fmt].append(load_time / 1000 if load_time not in [None, 0] else None)
                load_memory_data[fmt].append(load_memory if load_memory not in [None, 0] else None)
            else:
                load_time_data[fmt].append(None)
                load_memory_data[fmt].append(None)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    x = np.arange(len(models))
    width = 0.35
    # 图1：加载时间对比
    for i, fmt in enumerate(formats):
        offset = (i - 0.5) * width
        values = load_time_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax1.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax1.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=10, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}s', ha='center', va='bottom', fontsize=10, zorder=3)
    ax1.set_xlabel('Model (Face Count)', fontsize=12)
    ax1.set_ylabel('Load Time (seconds, log scale)', fontsize=12)
    ax1.set_title('glTF vs GLB: Load Time Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    labels = [f'{model.split("_")[0]}\n({face}k)' for model, face in zip(models, face_counts)]
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, which='both', zorder=1)
    ax1.set_yscale('log')
    ax1.annotate('注：y轴为对数坐标，缺失数据以红字标注', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    # 图2：内存占用对比
    for i, fmt in enumerate(formats):
        offset = (i - 0.5) * width
        values = load_memory_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax2.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax2.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=10, color='red', rotation=90, zorder=3)
            elif v is not None and v > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f}MB', ha='center', va='bottom', fontsize=10, zorder=3)
    ax2.set_xlabel('Model (Face Count)', fontsize=12)
    ax2.set_ylabel('Memory Usage (MB, log scale)', fontsize=12)
    ax2.set_title('glTF vs GLB: Memory Usage Comparison', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, which='both', zorder=1)
    ax2.set_yscale('log')
    ax2.annotate('注：y轴为对数坐标，缺失数据以红字标注', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/gltf_glb_comparison.html', 'glTF vs GLB Performance Comparison', 'Comparison of load time and memory usage between glTF and GLB formats (log scale, missing data marked)')

def save_plot_as_html(fig, filepath, title, description):
    """将matplotlib图表保存为HTML文件"""
    from io import BytesIO
    import base64
    
    # 保存图表为base64编码的图片
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)
    
    # 创建HTML内容
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
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
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }}
        .description {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        .chart-container {{
            text-align: center;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p class="description">{description}</p>
        <div class="chart-container">
            <img src="data:image/png;base64,{image_base64}" alt="{title}">
        </div>
        <div class="footer">
            Generated by Model Format Analysis Tool
        </div>
    </div>
</body>
</html>
"""
    
    # 确保Charts目录存在
    os.makedirs('Charts', exist_ok=True)
    
    # 保存HTML文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"已生成报告: {filepath}")

def create_summary_report(models_data):
    """创建汇总报告"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Model Format Analysis - Summary Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
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
        .report-links {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .report-card {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .report-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .report-card h3 {
            color: #495057;
            margin-top: 0;
        }
        .report-card p {
            color: #6c757d;
            margin-bottom: 15px;
        }
        .report-card a {
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background-color 0.2s;
        }
        .report-card a:hover {
            background-color: #0056b3;
        }
        .summary-table {
            margin-top: 30px;
            width: 100%;
            border-collapse: collapse;
        }
        .summary-table th, .summary-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .summary-table th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #495057;
        }
        .summary-table tr:hover {
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>3D Model Format Analysis - Summary Report</h1>
        
        <h2>Model Information</h2>
        <table class="summary-table">
            <thead>
                <tr>
                    <th>Model Name</th>
                    <th>Face Count</th>
                    <th>Texture Count</th>
                    <th>Formats Analyzed</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # 添加模型信息
    for model_name, model_data in models_data.items():
        formats = ', '.join(model_data['formats'].keys())
        html_content += f"""
                <tr>
                    <td>{model_name}</td>
                    <td>{model_data['face_count_k']}k</td>
                    <td>{model_data['texture_count']}</td>
                    <td>{formats}</td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
        
        <h2>Analysis Reports</h2>
        <div class="report-links">
            <div class="report-card">
                <h3>Import Time Comparison</h3>
                <p>Compare import times across FBX, OBJ, glTF, and GLB formats for different models.</p>
                <a href="import_time_comparison.html">View Report</a>
            </div>
            
            <div class="report-card">
                <h3>Size & Memory Analysis</h3>
                <p>Analyze file sizes (before/after compression) and peak memory usage for each format.</p>
                <a href="size_memory_comparison.html">View Report</a>
            </div>
            
            <div class="report-card">
                <h3>Compression & Texture Analysis</h3>
                <p>Examine compression ratios and texture size proportions across different formats.</p>
                <a href="compression_texture_ratio.html">View Report</a>
            </div>
            
            <div class="report-card">
                <h3>glTF vs GLB Performance</h3>
                <p>Direct comparison of load times and memory usage between glTF and GLB formats.</p>
                <a href="gltf_glb_comparison.html">View Report</a>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    # 保存汇总报告
    with open('Charts/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("已生成汇总报告: Charts/index.html")

# 新增：每格式一张，横轴为模型，柱子为压缩前大小、压缩后大小、压缩比、纹理占比
def create_per_format_stats(models_data):
    formats = ['fbx', 'obj', 'glTF', 'glb']
    for fmt in formats:
        models = []
        face_counts = []
        texture_counts = []
        size_before = []
        size_after = []
        compression_ratio = []
        texture_ratio = []
        for model_name, model_data in models_data.items():
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                sb = fmt_data.get('size_before_mb', None)
                sa = fmt_data.get('size_after_mb', None)
                tc = fmt_data.get('texture_size_mb', None)
                if sb is not None or sa is not None or tc is not None:
                    models.append(model_name)
                    face_counts.append(model_data['face_count_k'])
                    texture_counts.append(model_data['texture_count'])
                    size_before.append(sb)
                    size_after.append(sa)
                    if sb not in [None, 0] and sa not in [None, 0]:
                        compression_ratio.append((1 - sa / sb) * 100)
                    else:
                        compression_ratio.append(None)
                    if sb not in [None, 0] and tc not in [None, 0]:
                        texture_ratio.append(tc / sb * 100)
                    else:
                        texture_ratio.append(None)
        x = np.arange(len(models))
        width = 0.18
        fig, ax = plt.subplots(figsize=(max(10, len(models)*0.7), 8))
        bars1 = ax.bar(x - 1.5*width, [v if v not in [None, 0] else 0 for v in size_before], width, label='压缩前(MB)', zorder=2)
        bars2 = ax.bar(x - 0.5*width, [v if v not in [None, 0] else 0 for v in size_after], width, label='压缩后(MB)', zorder=2)
        bars3 = ax.bar(x + 0.5*width, [v if v not in [None, 0] else 0 for v in compression_ratio], width, label='压缩率(%)', zorder=2)
        bars4 = ax.bar(x + 1.5*width, [v if v not in [None, 0] else 0 for v in texture_ratio], width, label='纹理占比(%)', zorder=2)
        for bars, values in zip([bars1, bars2, bars3, bars4], [size_before, size_after, compression_ratio, texture_ratio]):
            for bar, v in zip(bars, values):
                if v is None:
                    ax.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
                elif v not in [None, 0]:
                    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}', ha='center', va='bottom', fontsize=8, zorder=3)
        ax.set_xlabel('模型 (面数/纹理数)', fontsize=12)
        ax.set_ylabel('数值 (对数坐标)', fontsize=12)
        ax.set_title(f'{fmt.upper()} 各项统计', fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        labels = [f'{m.split("_")[0]}\n({f}k/{t})' for m, f, t in zip(models, face_counts, texture_counts)]
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, which='both', zorder=1)
        ax.set_yscale('log')
        ax.annotate('注：y轴为对数坐标，缺失数据以红字标注', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
        plt.tight_layout()
        save_plot_as_html(fig, f'Charts/per_format_{fmt}.html', f'{fmt.upper()} 各项统计', f'每个模型的压缩前/后大小、压缩率、纹理占比（对数坐标，缺失标注）')

# 新增：横轴为模型，柱子为各格式压缩前大小
def create_all_format_size_before(models_data):
    formats = ['fbx', 'obj', 'glTF', 'glb']
    models = []
    face_counts = []
    texture_counts = []
    data = {fmt: [] for fmt in formats}
    for model_name, model_data in models_data.items():
        has_data = any(fmt in model_data['formats'] and model_data['formats'][fmt].get('size_before_mb', None) not in [None, 0] for fmt in formats)
        if has_data:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
            texture_counts.append(model_data['texture_count'])
            for fmt in formats:
                if fmt in model_data['formats']:
                    v = model_data['formats'][fmt].get('size_before_mb', None)
                    data[fmt].append(v)
                else:
                    data[fmt].append(None)
    x = np.arange(len(models))
    width = 0.18
    fig, ax = plt.subplots(figsize=(max(10, len(models)*0.7), 8))
    for i, fmt in enumerate(formats):
        offset = (i - 1.5) * width
        values = data[fmt]
        bar_vals = [v if v not in [None, 0] else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v not in [None, 0]:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}', ha='center', va='bottom', fontsize=8, zorder=3)
    ax.set_xlabel('模型 (面数/纹理数)', fontsize=12)
    ax.set_ylabel('压缩前大小 (MB, 对数坐标)', fontsize=12)
    ax.set_title('各格式压缩前大小对比', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [f'{m.split("_")[0]}\n({f}k/{t})' for m, f, t in zip(models, face_counts, texture_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    ax.set_yscale('log')
    ax.annotate('注：y轴为对数坐标，缺失数据以红字标注', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/all_format_size_before.html', '各格式压缩前大小对比', '各格式压缩前大小对比（对数坐标，缺失标注）')

# 新增：横轴为模型，柱子为各格式压缩后大小
def create_all_format_size_after(models_data):
    formats = ['fbx', 'obj', 'glTF', 'glb']
    models = []
    face_counts = []
    texture_counts = []
    data = {fmt: [] for fmt in formats}
    for model_name, model_data in models_data.items():
        has_data = any(fmt in model_data['formats'] and model_data['formats'][fmt].get('size_after_mb', None) not in [None, 0] for fmt in formats)
        if has_data:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
            texture_counts.append(model_data['texture_count'])
            for fmt in formats:
                if fmt in model_data['formats']:
                    v = model_data['formats'][fmt].get('size_after_mb', None)
                    data[fmt].append(v)
                else:
                    data[fmt].append(None)
    x = np.arange(len(models))
    width = 0.18
    fig, ax = plt.subplots(figsize=(max(10, len(models)*0.7), 8))
    for i, fmt in enumerate(formats):
        offset = (i - 1.5) * width
        values = data[fmt]
        bar_vals = [v if v not in [None, 0] else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, '缺失', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v not in [None, 0]:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}', ha='center', va='bottom', fontsize=8, zorder=3)
    ax.set_xlabel('模型 (面数/纹理数)', fontsize=12)
    ax.set_ylabel('压缩后大小 (MB, 对数坐标)', fontsize=12)
    ax.set_title('各格式压缩后大小对比', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [f'{m.split("_")[0]}\n({f}k/{t})' for m, f, t in zip(models, face_counts, texture_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    ax.set_yscale('log')
    ax.annotate('注：y轴为对数坐标，缺失数据以红字标注', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/all_format_size_after.html', '各格式压缩后大小对比', '各格式压缩后大小对比（对数坐标，缺失标注）')

def main():
    """主函数"""
    print("开始生成统计报告...")
    
    # 加载原始数据
    models_data = load_raw_data()
    print(f"已加载 {len(models_data)} 个模型的数据")
    
    # 生成各种报告
    print("\n生成导入时间对比报告...")
    create_import_time_comparison(models_data)
    
    print("\n生成大小和内存对比报告...")
    create_size_memory_comparison(models_data)
    
    print("\n生成压缩率和纹理占比报告...")
    create_compression_texture_ratio(models_data)
    
    print("\n生成glTF vs GLB对比报告...")
    create_gltf_glb_comparison(models_data)
    
    print("\n生成每格式统计报告...")
    create_per_format_stats(models_data)
    
    print("\n生成各格式压缩前大小对比报告...")
    create_all_format_size_before(models_data)
    
    print("\n生成各格式压缩后大小对比报告...")
    create_all_format_size_after(models_data)
    
    print("\n生成汇总报告...")
    create_summary_report(models_data)
    
    print("\n所有报告已生成完成！请查看 Charts 目录下的 HTML 文件。")
    print("打开 Charts/index.html 查看汇总报告。")

if __name__ == '__main__':
    main()