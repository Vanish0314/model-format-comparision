import json
import os
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path

# Set font to avoid unicode minus issues
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

def load_raw_data():
    """Load all model data from RawData directory"""
    with open('RawData/all_models_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_models_by_nonempty(data_by_format, models, face_counts):
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
    formats = ['fbx', 'obj', 'glTF', 'glb']
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
    models, face_counts, _, keep_indices = filter_models_by_nonempty(data_by_format, models, face_counts)
    for fmt in formats:
        data_by_format[fmt] = [data_by_format[fmt][i] for i in keep_indices]
    fig, ax = plt.subplots(figsize=(12, 8))
    x = np.arange(len(models))
    width = 0.2
    all_values = []
    for fmt in formats:
        all_values += [v for v in data_by_format[fmt] if v is not None and v > 0]
    use_log = should_use_log_scale(all_values)
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = data_by_format[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for j, (bar, v) in enumerate(zip(bars, values)):
            if v is None:
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f} s', ha='center', va='bottom', fontsize=8, zorder=3)
    ax.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel = 'Import Time (seconds, log scale)' if use_log else 'Import Time (seconds, linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Import Time Comparison: FBX vs OBJ vs glTF vs GLB', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [f'{model.split("_")[0]}\n({face}k faces)' for model, face in zip(models, face_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    ax.annotate(f'Note: y-axis is {"logarithmic" if use_log else "linear"} scale, missing data marked in red', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/import_time_comparison.html', 'Import Time Comparison', 'Comparison of import times across different 3D file formats (log/linear scale, missing data marked)')

def create_size_memory_comparison(models_data):
    """Create material size and memory usage comparison chart (log/linear scale + missing annotation)"""
    models = []
    formats = ['fbx', 'obj', 'glTF', 'glb']
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
    models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(size_before_data, models, face_counts)
    for fmt in formats:
        size_before_data[fmt] = [size_before_data[fmt][i] for i in keep_indices]
        size_after_data[fmt] = [size_after_data[fmt][i] for i in keep_indices]
        memory_data[fmt] = [memory_data[fmt][i] for i in keep_indices]

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 16))
    x = np.arange(len(models))
    width = 0.2
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
                ax1.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f} MB', ha='center', va='bottom', fontsize=8, zorder=3)
    ylabel1 = 'Size (MB, log scale)' if use_log1 else 'Size (MB, linear scale)'
    ax1.set_ylabel(ylabel1, fontsize=12)
    ax1.set_title('File Size Before Compression', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([model.split('_')[0] for model in models], rotation=45, ha='right')
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
                ax2.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f} MB', ha='center', va='bottom', fontsize=8, zorder=3)
    ylabel2 = 'Size (MB, log scale)' if use_log2 else 'Size (MB, linear scale)'
    ax2.set_ylabel(ylabel2, fontsize=12)
    ax2.set_title('File Size After Compression', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([model.split('_')[0] for model in models], rotation=45, ha='right')
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
                ax3.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v is not None and v > 0:
                ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.0f} MB', ha='center', va='bottom', fontsize=8, zorder=3)
    ax3.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel3 = 'Memory (MB, log scale)' if use_log3 else 'Memory (MB, linear scale)'
    ax3.set_ylabel(ylabel3, fontsize=12)
    ax3.set_title('Peak Memory Usage', fontsize=14, fontweight='bold')
    ax3.set_xticks(x)
    labels = [f'{model.split("_")[0]}\n({face}k faces)' for model, face in zip(models, face_counts)]
    ax3.set_xticklabels(labels, rotation=45, ha='right')
    ax3.legend()
    ax3.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log3:
        ax3.set_yscale('log')
    ax3.annotate(f'Note: y-axis is {"logarithmic" if use_log3 else "linear"} scale, missing data marked in red', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/size_memory_comparison.html', 'File Size and Memory Usage Comparison', 'Comparison of file sizes (before/after compression) and peak memory usage (log/linear scale, missing data marked)')

def create_compression_texture_ratio(models_data):
    """Create compression ratio and texture size proportion chart (log scale + missing annotation)"""
    models = []
    formats = ['fbx', 'obj', 'glTF', 'glb']
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
                # Calculate texture ratio
                if size_before not in [None, 0] and texture_size not in [None, 0]:
                    texture_ratio = (texture_size / size_before) * 100
                else:
                    texture_ratio = None
                texture_ratio_data[fmt].append(texture_ratio)
            else:
                compression_ratio_data[fmt].append(None)
                texture_ratio_data[fmt].append(None)
    # Filter out models where all bars are empty
    models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(compression_ratio_data, models, face_counts)
    for fmt in formats:
        compression_ratio_data[fmt] = [compression_ratio_data[fmt][i] for i in keep_indices]
        texture_ratio_data[fmt] = [texture_ratio_data[fmt][i] for i in keep_indices]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    x = np.arange(len(models))
    width = 0.2
    # Figure 1: Compression ratio comparison
    all_values1 = []
    for fmt in formats:
        all_values1 += [v for v in compression_ratio_data[fmt] if v is not None and v > 0]
    use_log1 = should_use_log_scale(all_values1)
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = compression_ratio_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax1.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax1.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}%', ha='center', va='bottom', fontsize=8, zorder=3)
    ylabel1 = 'Compression Ratio (%) (log scale)' if use_log1 else 'Compression Ratio (%) (linear scale)'
    ax1.set_ylabel(ylabel1, fontsize=12)
    ax1.set_title('Compression Ratio Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([model.split('_')[0] for model in models], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log1:
        ax1.set_yscale('log')
    ax1.set_ylim(bottom=0.1)
    # Figure 2: Texture size proportion comparison
    all_values2 = []
    for fmt in formats:
        all_values2 += [v for v in texture_ratio_data[fmt] if v is not None and v > 0]
    use_log2 = should_use_log_scale(all_values2)
    for i, fmt in enumerate(formats):
        offset = (i - len(formats)/2 + 0.5) * width
        values = texture_ratio_data[fmt]
        bar_vals = [v if v is not None and v > 0 else 0 for v in values]
        bars = ax2.bar(x + offset, bar_vals, width, label=fmt, zorder=2)
        for bar, v in zip(bars, values):
            if v is None:
                ax2.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}%', ha='center', va='bottom', fontsize=8, zorder=3)
    ax2.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel2 = 'Texture Size Ratio (%) (log scale)' if use_log2 else 'Texture Size Ratio (%) (linear scale)'
    ax2.set_ylabel(ylabel2, fontsize=12)
    ax2.set_title('Texture Size as Percentage of Total File Size', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    labels = [f'{model.split("_")[0]}\n({face}k faces)' for model, face in zip(models, face_counts)]
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log2:
        ax2.set_yscale('log')
    ax2.set_ylim(bottom=0.1)
    ax2.annotate('Note: y-axis is logarithmic scale, missing data marked in red', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
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
    models, face_counts, _, keep_indices = filter_models_by_nonempty(load_time_data, models, face_counts)
    for fmt in formats:
        load_time_data[fmt] = [load_time_data[fmt][i] for i in keep_indices]
        load_memory_data[fmt] = [load_memory_data[fmt][i] for i in keep_indices]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    x = np.arange(len(models))
    width = 0.35
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
    labels = [f'{model.split("_")[0]}\n({face}k)' for model, face in zip(models, face_counts)]
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log1:
        ax1.set_yscale('log')
    ax1.annotate('Note: y-axis is logarithmic scale, missing data marked in red', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
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
    ax2.annotate('Note: y-axis is logarithmic scale, missing data marked in red', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/gltf_glb_comparison.html', 'glTF vs GLB Performance Comparison', 'Comparison of load time and memory usage between glTF and GLB formats (log scale, missing data marked)')

def save_plot_as_html(fig, filepath, title, description):
    """Save matplotlib chart as an HTML file"""
    from io import BytesIO
    import base64
    
    # Save chart as base64 encoded image
    buffer = BytesIO()
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
    formats = ['fbx', 'obj', 'glTF', 'glb']
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
    models, face_counts, _, keep_indices = filter_models_by_nonempty(data_by_format, models, face_counts)
    for fmt in formats:
        data_by_format[fmt] = [data_by_format[fmt][i] for i in keep_indices]
    fig, ax = plt.subplots(figsize=(max(10, len(models)*0.7), 8))
    x = np.arange(len(models))
    width = 0.18
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
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            else:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f} %', ha='center', va='bottom', fontsize=8, zorder=3)
    ax.set_xlabel('Model (Face Count)', fontsize=12)
    ylabel = 'Compression Ratio (%) (log scale)' if use_log else 'Compression Ratio (%) (linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Compression Ratio by Model and Format', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [f'{model.split("_")[0]}\n({face}k faces)' for model, face in zip(models, face_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    ax.annotate(f'Note: y-axis is {"logarithmic" if use_log else "linear"} scale, missing data marked in red', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
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
            <div class="report-card">
                <h3>Per-Format Statistics</h3>
                <p>Detailed statistics for each format: size before/after compression, compression ratio, texture ratio.</p>
                <ul>
                    <li><a href="per_format_fbx.html">FBX Stats</a></li>
                    <li><a href="per_format_obj.html">OBJ Stats</a></li>
                    <li><a href="per_format_glTF.html">glTF Stats</a></li>
                    <li><a href="per_format_glb.html">GLB Stats</a></li>
                </ul>
            </div>
            <div class="report-card">
                <h3>All-Format Size Before Compression</h3>
                <p>Compare size before compression across all formats for each model.</p>
                <a href="all_format_size_before.html">View Report</a>
            </div>
            <div class="report-card">
                <h3>All-Format Size After Compression</h3>
                <p>Compare size after compression across all formats for each model.</p>
                <a href="all_format_size_after.html">View Report</a>
            </div>
            <div class="report-card">
                <h3>Model-Format Compression Ratio</h3>
                <p>Compression ratio for each model and each format.</p>
                <a href="model_format_compression_ratio.html">View Report</a>
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
        # Filter out models where all bars are empty
        models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(size_before, models, face_counts)
        for arr in [size_before, size_after, compression_ratio, texture_ratio]:
            arr[:] = [arr[i] for i in keep_indices]

        x = np.arange(len(models))
        width = 0.18
        fig, ax = plt.subplots(figsize=(max(10, len(models)*0.7), 8))
        all_values = []
        for arr in [size_before, size_after, compression_ratio, texture_ratio]:
            all_values += [v for v in arr if v not in [None, 0]]
        use_log = should_use_log_scale(all_values)
        bars1 = ax.bar(x - 1.5*width, [v if v not in [None, 0] else 0 for v in size_before], width, label='Size Before (MB)', zorder=2)
        bars2 = ax.bar(x - 0.5*width, [v if v not in [None, 0] else 0 for v in size_after], width, label='Size After (MB)', zorder=2)
        bars3 = ax.bar(x + 0.5*width, [v if v not in [None, 0] else 0 for v in compression_ratio], width, label='Compression Ratio (%)', zorder=2)
        bars4 = ax.bar(x + 1.5*width, [v if v not in [None, 0] else 0 for v in texture_ratio], width, label='Texture Ratio (%)', zorder=2)
        for bars, values, unit in zip([bars1, bars2, bars3, bars4], [size_before, size_after, compression_ratio, texture_ratio], ['MB', 'MB', '%', '%']):
            for bar, v in zip(bars, values):
                if v is None:
                    ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
                elif v not in [None, 0]:
                    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f} {unit}', ha='center', va='bottom', fontsize=8, zorder=3)
        ax.set_xlabel('Model (Face Count/Texture Count)', fontsize=12)
        ylabel = 'Value (log scale)' if use_log else 'Value (linear scale)'
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(f'{fmt.upper()} Stats', fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        labels = [f'{m.split("_")[0]}\n({f}k/{t})' for m, f, t in zip(models, face_counts, texture_counts)]
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, which='both', zorder=1)
        if use_log:
            ax.set_yscale('log')
        ax.annotate(f'Note: y-axis is {"logarithmic" if use_log else "linear"} scale, missing data marked in red', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
        plt.tight_layout()
        save_plot_as_html(fig, f'Charts/per_format_{fmt}.html', f'{fmt.upper()} Stats', f'Size before/after compression, compression ratio, and texture ratio for each model (log/linear scale, missing data marked)')

# New: Horizontal axis is model, bars are size before compression for all formats
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
    # Filter out models where all bars are empty
    models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(data, models, face_counts)
    for fmt in formats:
        data[fmt] = [data[fmt][i] for i in keep_indices]

    x = np.arange(len(models))
    width = 0.18
    fig, ax = plt.subplots(figsize=(max(10, len(models)*0.7), 8))
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
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v not in [None, 0]:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}', ha='center', va='bottom', fontsize=8, zorder=3)
    ax.set_xlabel('Model (Face Count/Texture Count)', fontsize=12)
    ylabel = 'Size Before Compression (MB, log scale)' if use_log else 'Size Before Compression (MB, linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Size Before Compression Comparison Across Formats', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [f'{m.split("_")[0]}\n({f}k/{t})' for m, f, t in zip(models, face_counts, texture_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    ax.annotate('Note: y-axis is logarithmic scale, missing data marked in red', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/all_format_size_before.html', 'Size Before Compression Comparison Across Formats', 'Size before compression comparison across different formats (log scale, missing data marked)')

# New: Horizontal axis is model, bars are size after compression for all formats
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
    # Filter out models where all bars are empty
    models, face_counts, texture_counts, keep_indices = filter_models_by_nonempty(data, models, face_counts)
    for fmt in formats:
        data[fmt] = [data[fmt][i] for i in keep_indices]

    x = np.arange(len(models))
    width = 0.18
    fig, ax = plt.subplots(figsize=(max(10, len(models)*0.7), 8))
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
                ax.text(bar.get_x() + bar.get_width()/2., 0.5, 'Missing', ha='center', va='bottom', fontsize=8, color='red', rotation=90, zorder=3)
            elif v not in [None, 0]:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(), f'{v:.1f}', ha='center', va='bottom', fontsize=8, zorder=3)
    ax.set_xlabel('Model (Face Count/Texture Count)', fontsize=12)
    ylabel = 'Size After Compression (MB, log scale)' if use_log else 'Size After Compression (MB, linear scale)'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title('Size After Compression Comparison Across Formats', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    labels = [f'{m.split("_")[0]}\n({f}k/{t})' for m, f, t in zip(models, face_counts, texture_counts)]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both', zorder=1)
    if use_log:
        ax.set_yscale('log')
    ax.annotate('Note: y-axis is logarithmic scale, missing data marked in red', xy=(1, 1), xycoords='axes fraction', fontsize=10, ha='right', va='bottom', color='gray')
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
    return max_v / min_v > 10

def main():
    """Main function"""
    print("Starting to generate statistical reports...")
    
    # Load raw data
    models_data = load_raw_data()
    print(f"Loaded data for {len(models_data)} models")
    
    # Generate various reports
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
    
    print("\nGenerating summary report...")
    create_summary_report(models_data)
    
    print("\nAll reports generated! Please check the HTML files in the Charts directory.")
    print("Open Charts/index.html to view the summary report.")

if __name__ == '__main__':
    main()