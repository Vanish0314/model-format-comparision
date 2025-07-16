import json
import os
from typing import Dict, Any

def load_raw_data() -> Dict[str, Any]:
    """Load all model data from RawData directory with error handling."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, '../RawData/all_models_data.json')
    data_path = os.path.normpath(data_path)
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Data file not found: {data_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON decode error in {data_path}: {e}")