# 项目结构

- Charts: 存放最终的html统计报告
- RawData: 存放用于分析的原始数据,数据是json 格式,是从 model_data.md 中手动转换而来.
- MiddleData: 用于存放分析时的中间数据
- Scripts: 存放python脚本
- main.py: 用于将rawdata转换为最终的统计报告

# 统计报告

- fbx obj gltf glb 导入时间对比，多个模型，标模型面数
- fbx obj gltf glb 素材大小（压缩前后）、峰值内存占用对比，多个模型，标模型面数
- fbx obj gltf glb 素材压缩率、纹理大小占比，多个模型，标模型面数
- gltf glb 加载完整模型时间,内存对比