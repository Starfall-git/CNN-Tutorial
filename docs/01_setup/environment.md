# 环境检查与启动

## 已核实的训练环境

项目使用已有 `CNN-Tutorial` conda 环境。实测 Python 3.14.8、PyTorch 2.14.1+cu132、CUDA runtime 13.2，GPU 为 NVIDIA GeForce RTX 5060 Laptop GPU（8 GB）。版本以 notebook 的实际输出和 `docs/05_experiments/environment.json` 为准。

## Anaconda Prompt

```bat
conda activate CNN-Tutorial
cd /d C:\Users\SteLl1a\Desktop\CNN-Tutorial
python -m pip install -r requirements.txt
python -m ipykernel install --user --name CNN-Tutorial --display-name "Python (CNN-Tutorial)"
python -m notebook notebooks
```

也可双击项目中的 `scripts/start_notebook.cmd`。该脚本优先使用本机已存在的 Anaconda 路径；其他电脑需要修改路径或让 conda 可在命令行调用。选择内核 **Python (CNN-Tutorial)**，先运行 00，再运行 01、02。Python 路径必须指向这个环境。

安装 requirements 不会要求升级已有 PyTorch。不要为安装教程辅助库而重装 CUDA 或替换现有 torch。仓库 CI 使用独立 CPU 环境，只做小型契约测试；不等同于当前 GPU 训练环境。

## 网络与复现

下载需要访问官方 PyPI、Google 数据存储与 GitHub。若遇到 TLS EOF，先检查进程代理是否能连接目标站点；不应关闭证书验证。环境中已有的代理可能只对某些站点可用。

`requirements.txt` 是最低依赖声明，实际安装快照另存于实验目录。种子固定、cuDNN benchmark 关闭、启用确定性算法；不同 GPU、驱动与框架版本仍可能产生数值差异。

## 后续量化环境

本环境目前以 PyTorch GPU 训练为主。手册要求 TensorFlow Lite 全整数量化。v0.1 不在训练环境里强行混装旧版 TensorFlow；阶段 4 将建立独立、锁定版本的转换环境，并验证 PyTorch→Keras 浮点一致性，再导出 INT8。不能把 `.pt`、ONNX 或 PyTorch 的 INT8 文件直接当作板卡可用模型。
