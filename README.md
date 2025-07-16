# 项目结构

- Charts: 存放最终的html统计报告
- RawData: 存放用于分析的原始数据,数据是json 格式,是从 model_data.md 中手动转换而来.
- Scripts: 存放python脚本
    - main.py: 主入口，调度所有报告生成
    - data_loader.py: 数据加载与校验
    - chart_utils.py: 通用绘图与工具函数
    - report_generators.py: 所有报告生成函数
- requirements.txt: 依赖包列表

## 依赖安装

```bash
pip install -r requirements.txt --break-system-packages
```

## 一键生成报告

```bash
python3 Scripts/main.py
```

生成的所有报告在 Charts 目录下，主页面为 Charts/index.html。
