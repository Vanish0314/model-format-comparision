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
            data = json.load(f)
            # 1. data['face_count_k'] → data['faceCountK']
            # 2. data['texture_count'] → data['textureCount']
            # 3. data.get('size_before_mb', None) → data.get('sizeBeforeZipMB', None)
            # 4. data.get('size_after_mb', None) → data.get('sizeAfterZipMB', None)
            # 5. data.get('peak_memory_mb', None) → data.get('peakMemoryMB', None)
            # 6. data.get('texture_size_mb', None) → data.get('textureSizeBeforeZipMB', None)
            # 7. data.get('texture_size_after_mb', None) → data.get('textureSizeAfterZipMB', None)
            # 8. data.get('import_time_ms', None) → data.get('importTimeMs', None)
            # 9. data.get('load_time_ms', None) → data.get('loadTimeMs', None)
            # 10. data.get('load_memory_mb', None) → data.get('loadPeakMemoryMB', None)
            return data
    except FileNotFoundError:
        raise RuntimeError(f"Data file not found: {data_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON decode error in {data_path}: {e}")