import json
import os
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path
import io
import base64
import matplotlib.image as mpimg
from matplotlib.figure import Figure
import glob

# Set font to avoid unicode minus issues
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

from data_loader import load_raw_data
from report_generators import (
    create_import_time_comparison,
    create_size_memory_comparison,
    create_compression_texture_ratio,
    create_gltf_glb_comparison,
    create_model_format_compression_ratio_chart,
    create_summary_report,
    create_per_format_stats,
    create_all_format_size_before,
    create_all_format_size_after,
    create_all_format_size_before_after,
    create_peak_memory_usage,
    create_combined_report
)

def get_standardized_model_name(model_name, face_count_k, texture_count):
    """Convert model name to standardized format: ModelName(face_countk/texture_count)"""
    # Extract the base name (remove suffixes like _2832k_405tex)
    base_name = model_name.split('_')[0]
    return f"{base_name}({face_count_k}k/{texture_count})"

def filter_models_by_nonempty(models_data, data_by_format, models, face_counts):
    """
    Filters out models where all values for a given format are empty (None or 0).
    Returns the filtered lists and the indices of models to keep.
    """
    keep_indices = []
    for i, model_name in enumerate(models):
        model_data = models_data[model_name]
        has_data = False
        for fmt in data_by_format:
            if fmt in model_data['formats']:
                if data_by_format[fmt][i] is not None and data_by_format[fmt][i] > 0:
                    has_data = True
                    break
        if has_data:
            keep_indices.append(i)
    return [models[i] for i in keep_indices], [face_counts[i] for i in keep_indices], [model_data['texture_count'] for i, model_name in enumerate(models) if i in keep_indices], keep_indices

def create_import_time_comparison(models_data):
    """Create import time comparison chart (log/linear scale + missing annotation)"""
    models = []
    formats = ['fbx', 'obj', 'glTF']
    data_by_format = {fmt: [] for fmt in formats}
    face_counts = []
    valid_indices = []
    for idx, (model_name, model_data) in enumerate(models_data.items()):
        has_data = any(
            fmt in model_data['formats'] and 'import_time_ms' in model_data['formats'][fmt]
            for fmt in formats
        )
        if has_data:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
            valid_indices.append(idx)
    for fmt in formats:
        for idx in valid_indices:
            model_name = list(models_data.keys())[idx]
            model_data = models_data[model_name]
            if fmt in model_data['formats'] and 'import_time_ms' in model_data['formats'][fmt]:
                data_by_format[fmt].append(model_data['formats'][fmt]['import_time_ms'] / 1000)
            else:
                data_by_format[fmt].append(None)
    # Filter out models where all bars are empty
    models, face_counts, _, keep_indices = filter_models_by_nonempty(models_data, data_by_format, models, face_counts)
    for fmt in formats:
        data_by_format[fmt] = [data_by_format[fmt][i] for i in keep_indices]
    fig, ax = plt.subplots(figsize=(max(24, len(models)*1.2), 8))
    x = np.arange(len(models))
    width = 0.12
    all_values = []
    for fmt in formats:
        all_values += [v for v in data_by_format[fmt] if v is not None and v > 0]
    use_log = should_use_log_scale(all_values)
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = data_by_format[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            elif v > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f} s', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    ax.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel = 'Import Time (seconds, log scale)' if use_log else 'Import Time (seconds, linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Import Time Comparison: FBX vs OBJ vs glTF', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [get_standardized_model_name(model, face, models_data[model]["texture_count"]) for model, face in zip(models, face_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/import_time_comparison.html', 'Import Time Comparison', 'Comparison of import times across different 3D file formats (log/linear scale, missing data marked)')

def create_size_memory_comparison(models_data):
    """Create material size and memory usage comparison chart (log/linear scale + missing annotation)"""
    models = []
    formats = ['fbx', 'obj', 'glTF']
    size_before_data = {fmt: [] for fmt in formats}
    size_after_data = {fmt: [] for fmt in formats}
    memory_data = {fmt: [] for fmt in formats}
    face_counts = []
    valid_indices = []
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
    # Filter out models where all bars are empty
    models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(models_data, size_before_data, models, face_counts)
    for fmt in formats:
        size_before_data[fmt] = [size_before_data[fmt][i] for i in keep_indices]
        size_after_data[fmt] = [size_after_data[fmt][i] for i in keep_indices]
        memory_data[fmt] = [memory_data[fmt][i] for i in keep_indices]

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(max(24, len(models)*1.2), 16))
    x = np.arange(len(models))
    width = 0.12
    # 1. Size before compression
    all_values1 = []
    for fmt in formats:
        all_values1 += [v for v in size_before_data[fmt] if v is not None and v > 0]
    use_log1 = should_use_log_scale(all_values1)
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = size_before_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax1.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax1.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            elif v > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f} MB', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    ylabel1 = 'Size (MB, log scale)' if use_log1 else 'Size (MB, linear scale)'
    ax1.set_ylabel(ylabel1, fontsize=12)
    ax1.set_title('File Size Before Compression', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([get_standardized_model_name(model, face, models_data[model]["texture_count"]) for model, face in zip(models, face_counts)], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log1:
        ax1.set_yscale('log')
    # 2. Size after compression
    all_values2 = []
    for fmt in formats:
        all_values2 += [v for v in size_after_data[fmt] if v is not None and v > 0]
    use_log2 = should_use_log_scale(all_values2)
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = size_after_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax2.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax2.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            elif v > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f} MB', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    ylabel2 = 'Size (MB, log scale)' if use_log2 else 'Size (MB, linear scale)'
    ax2.set_ylabel(ylabel2, fontsize=12)
    ax2.set_title('File Size After Compression', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([get_standardized_model_name(model, face, models_data[model]["texture_count"]) for model, face in zip(models, face_counts)], rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log2:
        ax2.set_yscale('log')
    # 3. Peak memory usage
    all_values3 = []
    for fmt in formats:
        all_values3 += [v for v in memory_data[fmt] if v is not None and v > 0]
    use_log3 = should_use_log_scale(all_values3)
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = memory_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax3.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax3.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            elif v is not None and v > 0:
                ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f} MB', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    ax3.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel3 = 'Memory (MB, log scale)' if use_log3 else 'Memory (MB, linear scale)'
    ax3.set_ylabel(ylabel3, fontsize=12)
    ax3.set_title('Peak Memory Usage', fontsize=14, fontweight='bold')
    ax3.set_xticks(x)
    labels = [get_standardized_model_name(model, face, models_data[model]["texture_count"]) for model, face in zip(models, face_counts)]
    ax3.set_xticklabels(labels, rotation=45, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log3:
        ax3.set_yscale('log')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/size_memory_comparison.html', 'File Size and Memory Usage Comparison', 'Comparison of file sizes (before/after compression) and peak memory usage (log/linear scale, missing data marked)')

def create_compression_texture_ratio(models_data):
    """Create combined compression ratio and texture size proportion chart (log scale + missing annotation)"""
    models = []
    formats = ['fbx', 'obj', 'glTF']
    compression_ratio_data = {fmt: [] for fmt in formats}
    texture_ratio_data = {fmt: [] for fmt in formats}
    face_counts = []
    valid_indices = []
    # Only keep models that have at least one format with size_before_mb and size_after_mb
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
                # Calculate compression ratio
                if size_before not in [None, 0] and size_after not in [None, 0]:
                    compression_ratio = (1 - size_after / size_before) * 100
                else:
                    compression_ratio = None
                compression_ratio_data[fmt].append(compression_ratio)
                # Calculate texture ratio - only treat as missing when texture_size is None or field doesn't exist
                if size_before not in [None, 0] and texture_size is not None:
                    texture_ratio = (texture_size / size_before) * 100
                else:
                    texture_ratio = None
                texture_ratio_data[fmt].append(texture_ratio)
            else:
                compression_ratio_data[fmt].append(None)
                texture_ratio_data[fmt].append(None)
    # Filter out models where all bars are empty
    models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(models_data, compression_ratio_data, models, face_counts)
    for fmt in formats:
        compression_ratio_data[fmt] = [compression_ratio_data[fmt][i] for i in keep_indices]
        texture_ratio_data[fmt] = [texture_ratio_data[fmt][i] for i in keep_indices]

    fig, ax = plt.subplots(figsize=(max(24, len(models)*1.2), 12))
    x = np.arange(len(models))
    width = 0.12
    # Combined chart with compression ratio and texture size proportion
    all_values = []
    for fmt in formats:
        all_values += [v for v in compression_ratio_data[fmt] if v is not None and v > 0]
        all_values += [v for v in texture_ratio_data[fmt] if v is not None and v > 0]
    use_log = should_use_log_scale(all_values)
    
    # Plot compression ratio bars
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = compression_ratio_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=f'{fmt} Compression', zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            elif v > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}%', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    
    # Plot texture ratio bars with different pattern
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width + width * 2
        values = texture_ratio_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=f'{fmt} Texture', zorder=2, alpha=0.7)
        for bar, v in zip(bars, values):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            elif v > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}%', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    
    ylabel = 'Ratio (%) (log scale)' if use_log else 'Ratio (%) (linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_xlabel('Model (Face Count)', fontsize=12)
    ax.set_title('Compression Ratio and Texture Size Analysis', fontsize=16, fontweight='bold')
    ax.set_xticks(x + width)
    labels = [get_standardized_model_name(model, face, models_data[model]["texture_count"]) for model, face in zip(models, face_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    ax.set_ylim(bottom=0.1)
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/compression_texture_ratio.html', 'Compression Ratio and Texture Size Analysis', 'Analysis of compression efficiency and texture size proportion (log scale, missing data marked)')

def create_gltf_glb_comparison(models_data):
    """Create glTF vs GLB load time and memory comparison chart (log scale + missing annotation)"""
    models = []
    formats = ['glTF', 'glb']
    load_time_data = {fmt: [] for fmt in formats}
    load_memory_data = {fmt: [] for fmt in formats}
    face_counts = []
    valid_indices = []
    # Only keep models that have at least one format with load_time_ms/load_memory_mb
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
    # Filter out models where all bars are empty
    models, face_counts, _, keep_indices = filter_models_by_nonempty(models_data, load_time_data, models, face_counts)
    for fmt in formats:
        load_time_data[fmt] = [load_time_data[fmt][i] for i in keep_indices]
        load_memory_data[fmt] = [load_memory_data[fmt][i] for i in keep_indices]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(max(24, len(models)*1.2), 8))
    x = np.arange(len(models))
    width = 0.12
    # Figure 1: Load time comparison
    all_values1 = []
    for fmt in formats:
        all_values1 += [v for v in load_time_data[fmt] if v is not None and v > 0]
    use_log1 = should_use_log_scale(all_values1)
    for i, fmt in enumerate(formats):
        offset = (i - 0.5) * width
        values = load_time_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax1.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax1.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=10, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}s', ha='center', va='bottom', fontsize=10, zorder=3)
    ax1.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel1 = 'Load Time (seconds, log scale)' if use_log1 else 'Load Time (seconds, linear scale)'
    ax1.set_ylabel(ylabel1, fontsize=12)
    ax1.set_title('glTF vs GLB: Load Time Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    labels = [get_standardized_model_name(model, face, models_data[model]["texture_count"]) for model, face in zip(models, face_counts)]
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log1:
        ax1.set_yscale('log')
    # Figure 2: Memory usage comparison
    all_values2 = []
    for fmt in formats:
        all_values2 += [v for v in load_memory_data[fmt] if v is not None and v > 0]
    use_log2 = should_use_log_scale(all_values2)
    for i, fmt in enumerate(formats):
        offset = (i - 0.5) * width
        values = load_memory_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax2.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax2.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=10, color='red', rotation=90, zorder=3)
            elif v is not None and v > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f}MB', ha='center', va='bottom', fontsize=10, zorder=3)
    ax2.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel2 = 'Memory Usage (MB, log scale)' if use_log2 else 'Memory Usage (MB, linear scale)'
    ax2.set_ylabel(ylabel2, fontsize=12)
    ax2.set_title('glTF vs GLB: Memory Usage Comparison', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log2:
        ax2.set_yscale('log')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/gltf_glb_comparison.html', 'glTF vs GLB Performance Comparison', 'Comparison of load time and memory usage between glTF and GLB formats (log scale, missing data marked)')

def save_plot_as_html(fig, filepath, title, description):
    """Save matplotlib chart as an HTML file"""
    
    # Save chart as base64 encoded image
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)
    
    # Create HTML content
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
    
    # Ensure Charts directory exists
    os.makedirs('Charts', exist_ok=True)
    
    # Save HTML file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Report generated: {filepath}")

def create_model_format_compression_ratio_chart(models_data):
    """Create a chart showing compression ratio for each model and each format."""
    formats = ['fbx', 'obj', 'glTF']
    models = []
    face_counts = []
    data_by_format = {fmt: [] for fmt in formats}
    # Collect compression ratio for each model and format
    for model_name, model_data in models_data.items():
        has_any = False
        row = []
        for fmt in formats:
            if fmt in model_data['formats']:
                fmt_data = model_data['formats'][fmt]
                sb = fmt_data.get('size_before_mb', None)
                sa = fmt_data.get('size_after_mb', None)
                if sb not in [None, 0] and sa not in [None, 0]:
                    ratio = (1 - sa / sb) * 100
                    data_by_format[fmt].append(ratio)
                    has_any = True
                else:
                    data_by_format[fmt].append(None)
            else:
                data_by_format[fmt].append(None)
        if has_any:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
    # Filter out models where all bars are empty
    models, face_counts, _, keep_indices = filter_models_by_nonempty(models_data, data_by_format, models, face_counts)
    for fmt in formats:
        data_by_format[fmt] = [data_by_format[fmt][i] for i in keep_indices]
    fig, ax = plt.subplots(figsize=(max(24, len(models)*1.2), 8))
    x = np.arange(len(models))
    width = 0.12
    all_values = []
    for fmt in formats:
        all_values += [v for v in data_by_format[fmt] if v is not None]
    use_log = should_use_log_scale(all_values)
    for i, fmt in enumerate(formats):
        offset = (i - 1.5) * width
        values = data_by_format[fmt]
        bar_vals = [v if v is not None else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            else:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f} %', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    ax.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel = 'Compression Ratio (%) (log scale)' if use_log else 'Compression Ratio (%) (linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Compression Ratio by Model and Format', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [get_standardized_model_name(model, face, models_data[model]["texture_count"]) for model, face in zip(models, face_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/model_format_compression_ratio.html', 'Compression Ratio by Model and Format', 'Compression ratio for each model and each format (log/linear scale, missing data marked)')

def create_summary_report(models_data):
    """Create summary report"""
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
    # Add model information
    for model_name, model_data in models_data.items():
        formats = ', '.join(model_data['formats'].keys())
        face_count_k = model_data.get('face_count_k', 'N/A')
        html_content += f"""
                <tr>
                    <td>{model_name}</td>
                    <td>{face_count_k}k</td>
                    <td>{model_data.get('texture_count', 'N/A')}</td>
                    <td>{formats}</td>
                </tr>
"""
    html_content += """
            </tbody>
        </table>
        
        <h2>Analysis Reports</h2>
        <div class="report-links">
            <div class="report-card">
                <h3>Combined Model Format Analysis</h3>
                <p>All key statistics and comparisons in one page: Per-Format Statistics, All-Format Size Before/After Compression, Model-Format Compression Ratio, Compression Ratio and Texture Size Analysis, File Size and Memory Usage Comparison.</p>
                <a href="combined_report.html">View Combined Report</a>
            </div>
            <div class="report-card">
                <h3>Import Time Comparison</h3>
                <p>Compare import times across FBX, OBJ, glTF, and GLB formats for different models.</p>
                <a href="import_time_comparison.html">View Report</a>
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
    # Save summary report
    with open('Charts/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Summary report generated: Charts/index.html")

# New: One chart per format, horizontal axis is model, bars are size before compression, size after compression, compression ratio, texture ratio
def create_per_format_stats(models_data):
    formats = ['fbx', 'obj', 'glTF']
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
                cr = (1 - sa / sb) * 100 if sb not in [None, 0] and sa not in [None, 0] else None
                tr = (tc / sb) * 100 if sb not in [None, 0] and tc not in [None, 0] else None
                # 只要四项之一有数据就保留
                if any(x not in [None, 0] for x in [sb, sa, cr, tr]):
                    models.append(model_name)
                    face_counts.append(model_data['face_count_k'])
                    texture_counts.append(model_data['texture_count'])
                    size_before.append(sb)
                    size_after.append(sa)
                    compression_ratio.append(cr)
                    texture_ratio.append(tr)
        # 过滤掉所有四项都 missing 的模型
        keep_indices = [i for i in range(len(models)) if any(arr[i] not in [None, 0] for arr in [size_before, size_after, compression_ratio, texture_ratio])]
        models = [models[i] for i in keep_indices]
        face_counts = [face_counts[i] for i in keep_indices]
        texture_counts = [texture_counts[i] for i in keep_indices]
        size_before = [size_before[i] for i in keep_indices]
        size_after = [size_after[i] for i in keep_indices]
        compression_ratio = [compression_ratio[i] for i in keep_indices]
        texture_ratio = [texture_ratio[i] for i in keep_indices]

        x = np.arange(len(models))
        width = 0.12
        fig, ax1 = plt.subplots(figsize=(max(24, len(models)*1.2), 8))
        # MB类数据主y轴，%类数据副y轴
        all_mb = [v for v in size_before+size_after if v not in [None, 0]]
        all_pct = [v for v in compression_ratio+texture_ratio if v not in [None, 0]]
        use_log_mb = should_use_log_scale(all_mb)
        use_log_pct = should_use_log_scale(all_pct)
        bars1 = ax1.bar(x - width, [v if v not in [None, 0] else 0 for v in size_before], width, label='Size Before (MB)', color='#1f77b4', zorder=2)
        bars2 = ax1.bar(x, [v if v not in [None, 0] else 0 for v in size_after], width, label='Size After (MB)', color='#aec7e8', zorder=2)
        ax2 = ax1.twinx()
        bars3 = ax2.bar(x + width, [v if v not in [None, 0] else 0 for v in compression_ratio], width, label='Compression Ratio (%)', color='#ff7f0e', zorder=2, alpha=0.7)
        bars4 = ax2.bar(x + 2*width, [v if v not in [None, 0] else 0 for v in texture_ratio], width, label='Texture Ratio (%)', color='#ffbb78', zorder=2, alpha=0.7)
        for bars, values, unit, axx in zip([bars1, bars2, bars3, bars4], [size_before, size_after, compression_ratio, texture_ratio], ['MB', 'MB', '%', '%'], [ax1, ax1, ax2, ax2]):
            for bar, v in zip(bars, values):
                if v is None:
                    axx.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
                elif v not in [None, 0]:
                    axx.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f} {unit}', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
        ax1.set_xlabel('Model (Face Count/Texture Count)', fontsize=12)
        ylabel1 = 'File Size (MB, log scale)' if use_log_mb else 'File Size (MB, linear scale)'
        ax1.set_ylabel(ylabel1, fontsize=12)
        ylabel2 = 'Ratio (%) (log scale)' if use_log_pct else 'Ratio (%) (linear scale)'
        ax2.set_ylabel(ylabel2, fontsize=12)
        ax1.set_title(f'{fmt.upper()} Stats', fontsize=16, fontweight='bold')
        ax1.set_xticks(x)
        labels = [f'{m.split("_")[0]}\n({f}k/{t})' for m, f, t in zip(models, face_counts, texture_counts)]
        ax1.set_xticklabels(labels, rotation=45, ha='right')
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
        ax1.grid(True, alpha=0.3, which='both', zorder=1)
        if use_log_mb:
            ax1.set_yscale('log')
        if use_log_pct:
            ax2.set_yscale('log')
        plt.tight_layout()
        save_plot_as_html(fig, f'Charts/{fmt}_stats.html', f'{fmt.upper()} Stats', f'Size before/after compression, compression ratio, and texture ratio for {fmt} (log/linear scale, missing data marked)')

# New: Horizontal axis is model, bars are size before compression for all formats
def create_all_format_size_before(models_data):
    formats = ['fbx', 'obj', 'glTF']
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
    # Filter out models where all bars are empty
    models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(models_data, data, models, face_counts)
    for fmt in formats:
        data[fmt] = [data[fmt][i] for i in keep_indices]

    x = np.arange(len(models))
    width = 0.12
    fig, ax = plt.subplots(figsize=(max(24, len(models)*1.2), 8))
    all_values = []
    for fmt in formats:
        all_values += [v for v in data[fmt] if v not in [None, 0]]
    use_log = should_use_log_scale(all_values)
    for i, fmt in enumerate(formats):
        offset = (i - 1.5) * width
        values = data[fmt]
        bar_vals = [v if v not in [None, 0] else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            elif v not in [None, 0]:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    ax.set_xlabel('Model (Face Count/Texture Count)', fontsize=12)
    ylabel = 'Size Before Compression (MB, log scale)' if use_log else 'Size Before Compression (MB, linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Size Before Compression Comparison Across Formats', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [get_standardized_model_name(m, f, t) for m, f, t in zip(models, face_counts, texture_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/all_format_size_before.html', 'Size Before Compression Comparison Across Formats', 'Size before compression comparison across different formats (log scale, missing data marked)')

# New: Horizontal axis is model, bars are size after compression for all formats
def create_all_format_size_after(models_data):
    formats = ['fbx', 'obj', 'glTF']
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
    # Filter out models where all bars are empty
    models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(models_data, data, models, face_counts)
    for fmt in formats:
        data[fmt] = [data[fmt][i] for i in keep_indices]

    x = np.arange(len(models))
    width = 0.12
    fig, ax = plt.subplots(figsize=(max(24, len(models)*1.2), 8))
    all_values = []
    for fmt in formats:
        all_values += [v for v in data[fmt] if v not in [None, 0]]
    use_log = should_use_log_scale(all_values)
    for i, fmt in enumerate(formats):
        offset = (i - 1.5) * width
        values = data[fmt]
        bar_vals = [v if v not in [None, 0] else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            elif v not in [None, 0]:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    ax.set_xlabel('Model (Face Count/Texture Count)', fontsize=12)
    ylabel = 'Size After Compression (MB, log scale)' if use_log else 'Size After Compression (MB, linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Size After Compression Comparison Across Formats', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [get_standardized_model_name(m, f, t) for m, f, t in zip(models, face_counts, texture_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/all_format_size_after.html', 'Size After Compression Comparison Across Formats', 'Size after compression comparison across different formats (log scale, missing data marked)')

# Utility function to determine if log scale is needed
def should_use_log_scale(values):
    # Filter out None and non-positive values
    filtered = [v for v in values if v is not None and v > 0]
    if not filtered or len(filtered) < 2:
        return False
    min_v = min(filtered)
    max_v = max(filtered)
    return max_v / min_v >= 100

def create_combined_report(models_data):
    """生成合并后的综合报告，直接嵌入图片，不用iframe，不显示summary和导航，不显示Per-Format Statistics。"""
    # 生成所有需要的图表
    print("Generating individual charts for combined report...")
    create_per_format_stats(models_data)
    create_all_format_size_before_after(models_data)
    create_peak_memory_usage(models_data)
    create_import_time_comparison(models_data)
    create_compression_texture_ratio(models_data)
    create_model_format_compression_ratio_chart(models_data)

    # 图表文件名及标题
    chart_files = [
        ("Charts/all_format_size_before_after.png", "All-Format Size Before/After Compression"),
        ("Charts/model_format_compression_ratio.png", "Model-Format Compression Ratio"),
        ("Charts/compression_texture_ratio.png", "Compression Ratio and Texture Size Analysis"),
        ("Charts/size_memory_comparison.png", "File Size and Memory Usage Comparison"),
        ("Charts/peak_memory_usage.png", "Peak Memory Usage"),
        ("Charts/import_time_comparison.png", "Import Time Comparison"),
    ]
    # 直接嵌入图片
    chart_imgs = ""
    for file, title in chart_files:
        if not os.path.exists(file):
            continue
        with open(file, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        chart_imgs += f'''
        <div class="section">
            <h2>{title}</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{img_b64}" alt="{title}" style="width:100%;height:auto;">
            </div>
        </div>
        '''

    html_content = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Combined Model Format Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            width: 100vw;
            max-width: none;
            margin: 0;
            background-color: white;
            padding: 0 0 30px 0;
            border-radius: 0;
            box-shadow: none;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
            font-size: 2.5em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
        }}
        .section {{
            margin: 0 0 40px 0;
            padding: 20px 40px;
            border: none;
            border-radius: 0;
            background-color: #fafafa;
        }}
        .section h2 {{
            color: #34495e;
            margin-top: 0;
            font-size: 1.8em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
        }}
        img {{
            width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }}
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>Combined Model Format Analysis Report</h1>
        {chart_imgs}
    </div>
</body>
</html>
    """
    with open('Charts/combined_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Combined report generated: Charts/combined_report.html")

def create_all_format_size_before_after(models_data):
    """合并Size Before/After Compression为一张分组柱状图"""
    formats = ['fbx', 'obj', 'glTF']
    models = []
    face_counts = []
    texture_counts = []
    data_before = {fmt: [] for fmt in formats}
    data_after = {fmt: [] for fmt in formats}
    for model_name, model_data in models_data.items():
        has_data = any(fmt in model_data['formats'] and (
            model_data['formats'][fmt].get('size_before_mb', None) not in [None, 0] or
            model_data['formats'][fmt].get('size_after_mb', None) not in [None, 0]) for fmt in formats)
        if has_data:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
            texture_counts.append(model_data['texture_count'])
            for fmt in formats:
                if fmt in model_data['formats']:
                    data_before[fmt].append(model_data['formats'][fmt].get('size_before_mb', None))
                    data_after[fmt].append(model_data['formats'][fmt].get('size_after_mb', None))
                else:
                    data_before[fmt].append(None)
                    data_after[fmt].append(None)
    # 过滤无数据模型
    models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(models_data, data_before, models, face_counts)
    for fmt in formats:
        data_before[fmt] = [data_before[fmt][i] for i in keep_indices]
        data_after[fmt] = [data_after[fmt][i] for i in keep_indices]
    x = np.arange(len(models))
    width = 0.12
    fig, ax = plt.subplots(figsize=(max(24, len(models)*1.2), 8))
    # 色系定义
    base_colors = plt.get_cmap('tab10').colors
    for i, fmt in enumerate(formats):
        offset = (i - 1.5) * width * 2
        before_vals = [v if v not in [None, 0] else 0 for v in data_before[fmt]]
        after_vals = [v if v not in [None, 0] else 0 for v in data_after[fmt]]
        # 新增：获取纹理数据
        texture_before = [
            model_data['formats'][fmt].get('textureSizeBeforeZipMB', 0) if fmt in model_data['formats'] else 0
            for model_name, model_data in zip(models, [models_data[m] for m in models])
        ]
        texture_after = [
            model_data['formats'][fmt].get('textureSizeAfterZipMB', 0) if fmt in model_data['formats'] else 0
            for model_name, model_data in zip(models, [models_data[m] for m in models])
        ]
        # before: 主色，after: 明度降低
        color_before = base_colors[i]
        color_after = tuple(np.clip(np.array(base_colors[i]) + 0.3, 0, 1))
        color_before_texture = tuple(np.clip(np.array(base_colors[i]) * 0.7, 0, 1))
        color_after_texture = tuple(np.clip(np.array(base_colors[i]) * 0.7 + 0.3, 0, 1))
        # 堆叠柱状图：先画非纹理部分，再画纹理部分
        non_texture_before = [max(0, v-t) for v, t in zip(before_vals, texture_before)]
        bars1 = ax.bar(x + offset, non_texture_before, width, label=f'{fmt} Before (Non-Texture)', color=color_before, zorder=2)
        bars1_texture = ax.bar(x + offset, texture_before, width, bottom=non_texture_before, label=f'{fmt} Before (Texture)', color=color_before_texture, zorder=3)
        non_texture_after = [max(0, v-t) for v, t in zip(after_vals, texture_after)]
        bars2 = ax.bar(x + offset + width, non_texture_after, width, label=f'{fmt} After (Non-Texture)', color=color_after, zorder=2)
        bars2_texture = ax.bar(x + offset + width, texture_after, width, bottom=non_texture_after, label=f'{fmt} After (Texture)', color=color_after_texture, zorder=3)
        # 标注
        for idx, (bar, v, t) in enumerate(zip(bars1, before_vals, texture_before)):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=4)
            elif v not in [None, 0]:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}', ha='center', va='bottom', fontsize=7, rotation=60, zorder=4)
                # 纹理占比
                if t > 0 and v > 0:
                    percent = t / v * 100
                    txt = f'{percent:.0f}%\n{t:.1f}'
                    if t > v * 0.18:  # 足够空间
                        ax.text(bar.get_x() + bar.get_width()/2., bar.get_y() + bar.get_height(), txt, ha='center', va='center', fontsize=7, color='white', zorder=5)
                    else:
                        # 用线连到外部
                        ax.plot([bar.get_x() + bar.get_width()/2., bar.get_x() + bar.get_width()/2. + 0.05], [bar.get_y() + bar.get_height(), bar.get_y() + bar.get_height() + max(v*0.08, 2)], color='black', lw=0.7, zorder=6)
                        ax.text(bar.get_x() + bar.get_width()/2. + 0.08, bar.get_y() + bar.get_height() + max(v*0.08, 2), txt, ha='left', va='bottom', fontsize=7, color='black', zorder=6)
        for idx, (bar, v, t) in enumerate(zip(bars2, after_vals, texture_after)):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=4)
            elif v not in [None, 0]:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}', ha='center', va='bottom', fontsize=7, rotation=60, zorder=4)
                if t > 0 and v > 0:
                    percent = t / v * 100
                    txt = f'{percent:.0f}%\n{t:.1f}'
                    if t > v * 0.18:
                        ax.text(bar.get_x() + bar.get_width()/2., bar.get_y() + bar.get_height(), txt, ha='center', va='center', fontsize=7, color='white', zorder=5)
                    else:
                        ax.plot([bar.get_x() + bar.get_width()/2., bar.get_x() + bar.get_width()/2. + 0.05], [bar.get_y() + bar.get_height(), bar.get_y() + bar.get_height() + max(v*0.08, 2)], color='black', lw=0.7, zorder=6)
                        ax.text(bar.get_x() + bar.get_width()/2. + 0.08, bar.get_y() + bar.get_height() + max(v*0.08, 2), txt, ha='left', va='bottom', fontsize=7, color='black', zorder=6)
    all_values = []
    for fmt in formats:
        all_values += [v for v in data_before[fmt] if v not in [None, 0]]
        all_values += [v for v in data_after[fmt] if v not in [None, 0]]
    use_log = should_use_log_scale(all_values)
    ax.set_xlabel('Model (Face Count/Texture Count)', fontsize=12)
    ylabel = 'File Size (MB, log scale)' if use_log else 'File Size (MB, linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Size Before/After Compression Comparison Across Formats', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [get_standardized_model_name(m, f, t) for m, f, t in zip(models, face_counts, texture_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/all_format_size_before_after.html', 'Size Before/After Compression Comparison Across Formats', 'Comparison of file size before/after compression for each format (log scale, missing data marked)')
    fig.savefig('Charts/all_format_size_before_after.png', dpi=150, bbox_inches='tight')

# 2. 单独输出Peak Memory Usage

def create_peak_memory_usage(models_data):
    """只输出Peak Memory Usage，剔除无数据格式"""
    formats = ['fbx', 'obj', 'glTF']
    models = []
    face_counts = []
    memory_data = {fmt: [] for fmt in formats}
    for model_name, model_data in models_data.items():
        has_data = any(fmt in model_data['formats'] and model_data['formats'][fmt].get('peak_memory_mb', None) not in [None, 0] for fmt in formats)
        if has_data:
            models.append(model_name)
            face_counts.append(model_data['face_count_k'])
            for fmt in formats:
                if fmt in model_data['formats']:
                    memory_data[fmt].append(model_data['formats'][fmt].get('peak_memory_mb', None))
                else:
                    memory_data[fmt].append(None)
    # 剔除全为None/0的格式
    valid_formats = [fmt for fmt in formats if any(v not in [None, 0] for v in memory_data[fmt])]
    memory_data = {fmt: memory_data[fmt] for fmt in valid_formats}
    x = np.arange(len(models))
    width = 0.8 / len(valid_formats) if valid_formats else 0.2
    fig, ax = plt.subplots(figsize=(max(24, len(models)*1.2), 12))
    base_colors = plt.get_cmap('tab10').colors
    for i, fmt in enumerate(valid_formats):
        offset = (i - (len(valid_formats)-1)/2) * width
        values = memory_data[fmt]
        bar_vals = [v if v not in [None, 0] else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=fmt, color=base_colors[i], zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
            elif v not in [None, 0]:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f}', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
    all_values = []
    for fmt in valid_formats:
        all_values += [v for v in memory_data[fmt] if v not in [None, 0]]
    use_log = should_use_log_scale(all_values)
    ax.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel = 'Peak Memory Usage (MB, log scale)' if use_log else 'Peak Memory Usage (MB, linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Peak Memory Usage', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [get_standardized_model_name(model, face, models_data[model]["texture_count"]) for model, face in zip(models, face_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/peak_memory_usage.html', 'Peak Memory Usage', 'Peak memory usage for each model and format (log scale, missing data marked)')
    fig.savefig('Charts/peak_memory_usage.png', dpi=150, bbox_inches='tight')

# 3. 修改Per-Format Stats等有MB和%单位的图表为双y轴
# 以create_per_format_stats为例，其他类似图表可仿照修改

def create_per_format_stats(models_data):
    formats = ['fbx', 'obj', 'glTF']
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
                cr = (1 - sa / sb) * 100 if sb not in [None, 0] and sa not in [None, 0] else None
                tr = (tc / sb) * 100 if sb not in [None, 0] and tc not in [None, 0] else None
                if any(x not in [None, 0] for x in [sb, sa, cr, tr]):
                    models.append(model_name)
                    face_counts.append(model_data['face_count_k'])
                    texture_counts.append(model_data['texture_count'])
                    size_before.append(sb)
                    size_after.append(sa)
                    compression_ratio.append(cr)
                    texture_ratio.append(tr)
        keep_indices = [i for i in range(len(models)) if any(arr[i] not in [None, 0] for arr in [size_before, size_after, compression_ratio, texture_ratio])]
        models = [models[i] for i in keep_indices]
        face_counts = [face_counts[i] for i in keep_indices]
        texture_counts = [texture_counts[i] for i in keep_indices]
        size_before = [size_before[i] for i in keep_indices]
        size_after = [size_after[i] for i in keep_indices]
        compression_ratio = [compression_ratio[i] for i in keep_indices]
        texture_ratio = [texture_ratio[i] for i in keep_indices]
        x = np.arange(len(models))
        width = 0.12
        fig, ax1 = plt.subplots(figsize=(max(24, len(models)*1.2), 8))
        # MB类数据主y轴，%类数据副y轴
        all_mb = [v for v in size_before+size_after if v not in [None, 0]]
        all_pct = [v for v in compression_ratio+texture_ratio if v not in [None, 0]]
        use_log_mb = should_use_log_scale(all_mb)
        use_log_pct = should_use_log_scale(all_pct)
        bars1 = ax1.bar(x - width, [v if v not in [None, 0] else 0 for v in size_before], width, label='Size Before (MB)', color='#1f77b4', zorder=2)
        bars2 = ax1.bar(x, [v if v not in [None, 0] else 0 for v in size_after], width, label='Size After (MB)', color='#aec7e8', zorder=2)
        ax2 = ax1.twinx()
        bars3 = ax2.bar(x + width, [v if v not in [None, 0] else 0 for v in compression_ratio], width, label='Compression Ratio (%)', color='#ff7f0e', zorder=2, alpha=0.7)
        bars4 = ax2.bar(x + 2*width, [v if v not in [None, 0] else 0 for v in texture_ratio], width, label='Texture Ratio (%)', color='#ffbb78', zorder=2, alpha=0.7)
        for bars, values, unit, axx in zip([bars1, bars2, bars3, bars4], [size_before, size_after, compression_ratio, texture_ratio], ['MB', 'MB', '%', '%'], [ax1, ax1, ax2, ax2]):
            for bar, v in zip(bars, values):
                if v is None:
                    axx.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=7, color='red', rotation=60, zorder=3)
                elif v not in [None, 0]:
                    axx.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f} {unit}', ha='center', va='bottom', fontsize=7, rotation=60, zorder=3)
        ax1.set_xlabel('Model (Face Count/Texture Count)', fontsize=12)
        ylabel1 = 'File Size (MB, log scale)' if use_log_mb else 'File Size (MB, linear scale)'
        ax1.set_ylabel(ylabel1, fontsize=12)
        ylabel2 = 'Ratio (%) (log scale)' if use_log_pct else 'Ratio (%) (linear scale)'
        ax2.set_ylabel(ylabel2, fontsize=12)
        ax1.set_title(f'{fmt.upper()} Stats', fontsize=16, fontweight='bold')
        ax1.set_xticks(x)
        labels = [f'{m.split("_")[0]}\n({f}k/{t})' for m, f, t in zip(models, face_counts, texture_counts)]
        ax1.set_xticklabels(labels, rotation=45, ha='right')
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
        ax1.grid(True, alpha=0.3, which='both', zorder=1)
        if use_log_mb:
            ax1.set_yscale('log')
        if use_log_pct:
            ax2.set_yscale('log')
        plt.tight_layout()
        save_plot_as_html(fig, f'Charts/{fmt}_stats.html', f'{fmt.upper()} Stats', f'Size before/after compression, compression ratio, and texture ratio for {fmt} (log/linear scale, missing data marked)')

def main():
    print("Starting to generate statistical reports...")
    models_data = load_raw_data()
    print(f"Loaded data for {len(models_data)} models")
    print("\nGenerating import time comparison report...")
    create_import_time_comparison(models_data)
    print("\nGenerating size and memory comparison report...")
    create_size_memory_comparison(models_data)
    print("\nGenerating compression and texture ratio report...")
    create_compression_texture_ratio(models_data)
    print("\nGenerating glTF vs GLB comparison report...")
    create_gltf_glb_comparison(models_data)
    print("\nGenerating per-format stats report...")
    create_per_format_stats(models_data)
    print("\nGenerating model-format compression ratio chart...")
    create_model_format_compression_ratio_chart(models_data)
    print("\nGenerating all-format size before comparison report...")
    create_all_format_size_before(models_data)
    print("\nGenerating all-format size after comparison report...")
    create_all_format_size_after(models_data)
    print("\nGenerating all-format size before/after comparison report...")
    create_all_format_size_before_after(models_data)
    print("\nGenerating peak memory usage report...")
    create_peak_memory_usage(models_data)
    print("\nGenerating summary report...")
    create_summary_report(models_data)
    print("\nGenerating combined report...")
    create_combined_report(models_data)
    print("\nAll reports generated! Please check the HTML files in the Charts directory.")
    print("Open Charts/index.html to view the summary report.")

if __name__ == '__main__':
    main()