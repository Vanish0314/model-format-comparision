import os
import io
import base64
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Any, List

def save_plot_as_html(fig: Figure, filepath: str, title: str, description: str) -> None:
    """Save matplotlib chart as an HTML file with base64 image."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)
    html_content = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .description {{ text-align: center; color: #666; margin-bottom: 30px; }}
        .chart-container {{ text-align: center; }}
        img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
        .footer {{ margin-top: 30px; text-align: center; color: #999; }}
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>{title}</h1>
        <p class=\"description\">{description}</p>
        <div class=\"chart-container\">
            <img src=\"data:image/png;base64,{image_base64}\" alt=\"{title}\">
        </div>
        <div class=\"footer\">Generated by Model Format Analysis Tool</div>
    </div>
</body>
</html>
"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

def should_use_log_scale(values: List[Any]) -> bool:
    filtered = [v for v in values if v is not None and v > 0]
    if not filtered or len(filtered) < 2:
        return False
    min_v = min(filtered)
    max_v = max(filtered)
    return max_v / min_v >= 100