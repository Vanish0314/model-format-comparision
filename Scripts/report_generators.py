from typing import Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt
from chart_utils import save_plot_as_html, should_use_log_scale

def filter_models_by_nonempty(models_data: Dict[str, Any], data_by_format: Dict[str, List[Any]], models: List[str], face_counts: List[Any]):
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

# 下面以 create_import_time_comparison 为例，其他 create_ 开头函数可依次迁移

def create_import_time_comparison(models_data: Dict[str, Any]):
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
    models, face_counts, _, keep_indices = filter_models_by_nonempty(models_data, data_by_format, models, face_counts)
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
    plt.tight_layout()
    save_plot_as_html(fig, 'Charts/import_time_comparison.html', 'Import Time Comparison', 'Comparison of import times across different 3D file formats (log/linear scale, missing data marked)')

# 继续迁移其余报告生成函数
# 这里只展示函数签名和调用 chart_utils 的方式，具体实现可参考 main.py 原有内容

def create_size_memory_comparison(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_compression_texture_ratio(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_gltf_glb_comparison(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_model_format_compression_ratio_chart(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_summary_report(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_per_format_stats(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_all_format_size_before(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_all_format_size_after(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_all_format_size_before_after(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_peak_memory_usage(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass

def create_combined_report(models_data: Dict[str, Any]):
    # ... 迁移 main.py 中的实现 ...
    pass