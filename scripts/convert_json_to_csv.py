#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将rawdata中的JSON数据转换为CSV格式
"""

import json
import csv
from pathlib import Path

def convert_json_to_csv():
    """将JSON数据转换为CSV格式"""
    # 读取JSON数据
    json_path = Path("rawdata/model_data.json")
    csv_path = Path("data/model_data.csv")
    
    if not json_path.exists():
        print(f"错误：找不到JSON数据文件 {json_path}")
        return False
    
    # 确保data目录存在
    csv_path.parent.mkdir(exist_ok=True)
    
    # 读取JSON数据
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 转换为CSV格式
    csv_data = []
    formats = ['fbx', 'obj', 'gltf', 'glb']
    
    for model in data:
        model_name = model['model_name']
        face_count = model['face_count']
        texture_count = model['texture_count']
        
        for format_type in formats:
            if format_type in model['formats']:
                format_data = model['formats'][format_type]
                csv_data.append({
                    'model_name': model_name,
                    'face_count': face_count,
                    'texture_count': texture_count,
                    'format': format_type,
                    'original_size_mb': format_data['original_size_mb'],
                    'compressed_size_mb': format_data['compressed_size_mb'],
                    'texture_size_mb': format_data['texture_size_mb']
                })
    
    # 写入CSV文件
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if csv_data:
            fieldnames = csv_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
    
    print(f"✓ JSON数据已转换为CSV格式: {csv_path}")
    print(f"  共处理 {len(csv_data)} 条记录")
    return True

def main():
    """主函数"""
    print("正在转换JSON数据为CSV格式...")
    if convert_json_to_csv():
        print("数据转换完成！")
    else:
        print("数据转换失败！")

if __name__ == "__main__":
    main()