.PHONY: help install test clean run analyze all

# 默认目标
help:
	@echo "3D模型格式性能分析工具"
	@echo ""
	@echo "可用命令:"
	@echo "  install    - 安装依赖包"
	@echo "  test       - 运行测试"
	@echo "  run        - 运行分析"
	@echo "  analyze    - 运行完整分析"
	@echo "  clean      - 清理生成的文件"
	@echo "  all        - 安装依赖并运行完整分析"
	@echo "  help       - 显示此帮助信息"

# 安装依赖
install:
	@echo "正在安装依赖包..."
	python3 -m pip install -r requirements.txt

# 运行测试
test:
	@echo "正在运行测试..."
	python3 tests/test_analyzer.py

# 运行基本分析
run:
	@echo "正在运行基本分析..."
	python3 run_analysis.py

# 运行完整分析
analyze:
	@echo "正在运行完整分析..."
	python3 run_all_analysis.py

# 清理生成的文件
clean:
	@echo "正在清理生成的文件..."
	rm -rf charts/*
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# 完整流程：安装依赖并运行分析
all: install analyze

# 开发环境设置
dev-setup:
	@echo "正在设置开发环境..."
	python3 -m pip install -r requirements.txt
	python3 -m pip install pytest black flake8

# 代码格式化
format:
	@echo "正在格式化代码..."
	black src/ tests/ *.py

# 代码检查
lint:
	@echo "正在检查代码..."
	flake8 src/ tests/ *.py

# 运行所有检查
check: format lint test
	@echo "所有检查完成！"