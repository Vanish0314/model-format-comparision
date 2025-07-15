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
    """创建导入时间对比图表"""
    models = []
    formats = ['fbx', 'obj', 'glTF', 'glb']
    data_by_format = {fmt: [] for fmt in formats}
    face_counts = []
    texture_counts = []
    for model_name, model_data in models_data.items():
        models.append(model_name)
        face_counts.append(model_data['face_count_k'])
        texture_counts.append(model_data.get('texture_count', 0))
        for fmt in formats:
            if fmt in model_data['formats'] and 'import_time_ms' in model_data['formats'][fmt]:
                data_by_format[fmt].append(model_data['formats'][fmt]['import_time_ms'] / 1000)
            else:
                data_by_format[fmt].append(0)
    fig, ax = plt.subplots(figsize=(12, 8))
    x = np.arange(len(models))
    width = 0.2
    base_colors = plt.get_cmap('tab10').colors
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        bars = ax.bar(x + offset, data_by_format[fmt], width, label=fmt, color=base_colors[i])
        for idx, bar in enumerate(bars):
            height = bar.get_height()
            if height > 0 and (idx % 2 == 0 or height == max(data_by_format[fmt]) or height == min([v for v in data_by_format[fmt] if v > 0])):
                ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:.1f}s', ha='center', va='bottom', fontsize=8, rotation=90)
    ax.set_xlabel('Model (Face Count / Texture Count)', fontsize=12)
    ax.set_ylabel('Import Time (seconds)', fontsize=12)
    ax.set_title('Import Time Comparison: FBX vs OBJ vs glTF vs GLB', fontsize=16, fontweight='bold')
    labels = [f'{model.split("_")[0]}\n({face}k/{tex})' for model, face, tex in zip(models, face_counts, texture_counts)]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/import_time_comparison.html', 
                      'Import Time Comparison', 
                      'Comparison of import times across different 3D file formats')

def create_size_memory_comparison(models_data):
    """创建素材大小和内存占用对比图表（压缩前后合并）"""
    models = []
    formats = ['fbx', 'obj', 'glTF', 'glb']
    # 准备数据
    size_before_data = {fmt: [] for fmt in formats}
    size_after_data = {fmt: [] for fmt in formats}
    memory_data = {fmt: [] for fmt in formats}
    face_counts = []
    texture_counts = []
    for model_name, model_data in models_data.items():
        models.append(model_name)
        face_counts.append(model_data['face_count_k'])
        texture_counts.append(model_data.get('texture_count', 0))
        for fmt in formats:
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                size_before_data[fmt].append(fmt_data.get('size_before_mb', 0) or 0)
                size_after_data[fmt].append(fmt_data.get('size_after_mb', 0) or 0)
                memory_data[fmt].append(fmt_data.get('peak_memory_mb', 0) or 0)
            else:
                size_before_data[fmt].append(0)
                size_after_data[fmt].append(0)
                memory_data[fmt].append(0)
    # 合并压缩前后大小为一张图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    x = np.arange(len(models))
    width = 0.15
    # 颜色方案：同色系不同明度
    base_colors = plt.get_cmap('tab10').colors
    before_colors = [matplotlib.colors.to_rgba(c, 0.7) for c in base_colors[:len(formats)]]
    after_colors = [matplotlib.colors.to_rgba(c, 1.0) for c in base_colors[:len(formats)]]
    # 压缩前后柱状图
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2) * (2*width)
        bars_before = ax1.bar(x + offset - width/2, size_before_data[fmt], width, label=f'{fmt.upper()} Before', color=before_colors[i])
        bars_after = ax1.bar(x + offset + width/2, size_after_data[fmt], width, label=f'{fmt.upper()} After', color=after_colors[i])
        # 避免重叠的数值标注
        for bar, value in zip(bars_before, size_before_data[fmt]):
            if value > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height()+max(ax1.get_ylim()[1]*0.01, 1), f'{value:.0f}', ha='center', va='bottom', fontsize=8, rotation=90)
        for bar, value in zip(bars_after, size_after_data[fmt]):
            if value > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height()+max(ax1.get_ylim()[1]*0.01, 1), f'{value:.0f}', ha='center', va='bottom', fontsize=8, rotation=90)
    ax1.set_ylabel('Size (MB)', fontsize=12)
    ax1.set_title('File Size Before/After Compression Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    # x轴标签统一格式
    labels = [f'{model.split("_")[0]}\n({face}k/{tex})' for model, face, tex in zip(models, face_counts, texture_counts)]
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.legend(ncol=2)
    ax1.grid(True, alpha=0.3)
    # 峰值内存占用对比
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width * 2
        bars = ax2.bar(x + offset, memory_data[fmt], width, label=fmt.upper(), color=base_colors[i])
        for bar, value in zip(bars, memory_data[fmt]):
            if value > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height()+max(ax2.get_ylim()[1]*0.01, 1), f'{value:.0f}', ha='center', va='bottom', fontsize=8, rotation=90)
    ax2.set_xlabel('Model (Face Count / Texture Count)', fontsize=12)
    ax2.set_ylabel('Memory (MB)', fontsize=12)
    ax2.set_title('Peak Memory Usage', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/size_memory_comparison.html',
                      'File Size and Memory Usage Comparison',
                      'Comparison of file sizes (before/after compression) and peak memory usage')

def create_compression_texture_ratio(models_data):
    """创建压缩率和纹理占比图表（双y轴）"""
    models = []
    formats = ['fbx', 'obj', 'glTF', 'glb']
    compression_ratio_data = {fmt: [] for fmt in formats}
    texture_ratio_data = {fmt: [] for fmt in formats}
    size_before_data = {fmt: [] for fmt in formats}
    face_counts = []
    texture_counts = []
    for model_name, model_data in models_data.items():
        models.append(model_name)
        face_counts.append(model_data['face_count_k'])
        texture_counts.append(model_data.get('texture_count', 0))
        for fmt in formats:
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                size_before = fmt_data.get('size_before_mb', 0) or 0
                size_after = fmt_data.get('size_after_mb', 0) or 0
                texture_size = fmt_data.get('texture_size_mb', 0) or 0
                # 计算压缩率
                if size_before > 0:
                    compression_ratio = (1 - size_after / size_before) * 100
                else:
                    compression_ratio = 0
                compression_ratio_data[fmt].append(compression_ratio)
                # 计算纹理占比
                if size_before > 0:
                    texture_ratio = (texture_size / size_before) * 100
                else:
                    texture_ratio = 0
                texture_ratio_data[fmt].append(texture_ratio)
                size_before_data[fmt].append(size_before)
            else:
                compression_ratio_data[fmt].append(0)
                texture_ratio_data[fmt].append(0)
                size_before_data[fmt].append(0)
    x = np.arange(len(models))
    width = 0.15
    base_colors = plt.get_cmap('tab10').colors
    fig, ax1 = plt.subplots(figsize=(16, 8))
    ax2 = ax1.twinx()
    # 统计所有MB和%数据的最大最小值
    all_mb = [v for fmt in formats for v in size_before_data[fmt] if v > 0]
    all_pct = [v for fmt in formats for v in compression_ratio_data[fmt] if v > 0]
    # 判断是否用对数坐标
    if all_mb and (max(all_mb) / max(min(all_mb), 1e-6) > 100):
        ax1.set_yscale('log')
    if all_pct and (max(all_pct) / max(min(all_pct), 1e-6) > 100):
        ax2.set_yscale('log')
    # 柱状图：左轴MB，右轴%
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2) * (2*width)
        bars_mb = ax1.bar(x + offset - width/2, size_before_data[fmt], width, label=f'{fmt.upper()} Size (MB)', color=matplotlib.colors.to_rgba(base_colors[i], 0.7))
        bars_pct = ax2.bar(x + offset + width/2, compression_ratio_data[fmt], width, label=f'{fmt.upper()} Compression (%)', color=matplotlib.colors.to_rgba(base_colors[i], 1.0), alpha=0.5)
        # 避免重叠的数值标注（仅显示最大/最小/间隔）
        for idx, (bar, value) in enumerate(zip(bars_mb, size_before_data[fmt])):
            if value > 0 and (idx % 2 == 0 or value == max(size_before_data[fmt]) or value == min([v for v in size_before_data[fmt] if v > 0])):
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{value:.0f}', ha='center', va='bottom', fontsize=8, rotation=90)
        for idx, (bar, value) in enumerate(zip(bars_pct, compression_ratio_data[fmt])):
            if value > 0 and (idx % 2 == 1 or value == max(compression_ratio_data[fmt]) or value == min([v for v in compression_ratio_data[fmt] if v > 0])):
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{value:.1f}%', ha='center', va='bottom', fontsize=8, rotation=90, color=base_colors[i])
    # x轴标签统一格式
    labels = [f'{model.split("_")[0]}\n({face}k/{tex})' for model, face, tex in zip(models, face_counts, texture_counts)]
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.set_ylabel('Size (MB)', fontsize=12)
    ax2.set_ylabel('Compression Ratio (%)', fontsize=12)
    ax1.set_title('File Size (MB, left) & Compression Ratio (%, right) by Model and Format', fontsize=14, fontweight='bold')
    # 合并图例
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, ncol=2, loc='upper left')
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/compression_texture_ratio.html',
                      'File Size & Compression Ratio Analysis',
                      'Analysis of file size (MB, left) and compression ratio (%, right) across formats')

def create_gltf_glb_comparison(models_data):
    """创建glTF vs GLB加载时间和内存对比图表"""
    models = []
    formats = ['glTF', 'glb']
    load_time_data = {fmt: [] for fmt in formats}
    load_memory_data = {fmt: [] for fmt in formats}
    face_counts = []
    texture_counts = []
    for model_name, model_data in models_data.items():
        models.append(model_name)
        face_counts.append(model_data['face_count_k'])
        texture_counts.append(model_data.get('texture_count', 0))
        for fmt in formats:
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                load_time_data[fmt].append(fmt_data.get('load_time_ms', 0) / 1000 if 'load_time_ms' in fmt_data else 0)
                load_memory_data[fmt].append(fmt_data.get('load_memory_mb', 0) or 0)
            else:
                load_time_data[fmt].append(0)
                load_memory_data[fmt].append(0)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    x = np.arange(len(models))
    width = 0.35
    base_colors = plt.get_cmap('tab10').colors
    # 图1：加载时间对比
    for i, fmt in enumerate(formats):
        offset = (i - 0.5) * width
        bars = ax1.bar(x + offset, load_time_data[fmt], width, label=fmt, color=base_colors[i])
        for idx, (bar, value) in enumerate(zip(bars, load_time_data[fmt])):
            if value > 0 and (idx % 2 == 0 or value == max(load_time_data[fmt]) or value == min([v for v in load_time_data[fmt] if v > 0])):
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{value:.1f}s', ha='center', va='bottom', fontsize=10, rotation=90)
    ax1.set_xlabel('Model (Face Count / Texture Count)', fontsize=12)
    ax1.set_ylabel('Load Time (seconds)', fontsize=12)
    ax1.set_title('glTF vs GLB: Load Time Comparison', fontsize=14, fontweight='bold')
    labels = [f'{model.split("_")[0]}\n({face}k/{tex})' for model, face, tex in zip(models, face_counts, texture_counts)]
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    # 图2：内存占用对比
    for i, fmt in enumerate(formats):
        offset = (i - 0.5) * width
        bars = ax2.bar(x + offset, load_memory_data[fmt], width, label=fmt, color=base_colors[i])
        for idx, (bar, value) in enumerate(zip(bars, load_memory_data[fmt])):
            if value > 0 and (idx % 2 == 1 or value == max(load_memory_data[fmt]) or value == min([v for v in load_memory_data[fmt] if v > 0])):
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{value:.0f}MB', ha='center', va='bottom', fontsize=10, rotation=90)
    ax2.set_xlabel('Model (Face Count / Texture Count)', fontsize=12)
    ax2.set_ylabel('Memory Usage (MB)', fontsize=12)
    ax2.set_title('glTF vs GLB: Memory Usage Comparison', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/gltf_glb_comparison.html',
                      'glTF vs GLB Performance Comparison',
                      'Comparison of load time and memory usage between glTF and GLB formats')

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
    
    print("\n生成汇总报告...")
    create_summary_report(models_data)
    
    print("\n所有报告已生成完成！请查看 Charts 目录下的 HTML 文件。")
    print("打开 Charts/index.html 查看汇总报告。")

if __name__ == '__main__':
    main()