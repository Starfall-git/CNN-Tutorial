# CNN-Tutorial

面向易灵思 FPGA TinyML 的小模型实战教程。首个模型是 **64×64 灰度静态手势分类 CNN**，按石头、剪刀、布建立可复现基线。

从 [MAIN.md](MAIN.md) 查看约束、阶段和版本记录，从 [环境与启动](docs/01_setup/environment.md) 开始操作。

学习顺序：

1. `notebooks/00_environment.ipynb`：检查 Python、PyTorch、GPU 与目录。
2. `notebooks/01_gray_gesture_cnn.ipynb`：输入张量、卷积、池化、分类头、梯度与模型规模。
3. `notebooks/02_train_validate.ipynb`：数据划分、训练、验证选择、最终测试与错误分析。

每段代码前都有 Markdown 解释；通用训练实现位于 `cnn_tutorial/`。模型与数据保留在本地的 `artifacts/`、`data/`，厂商原始资料放在 `refs/`。Git 仓库只保存可复现代码、教程与小体积实验报告。

当前教学模型不含无手背景类，不能作为实际摄像头手势系统直接上线。板上 15 FPS 是待测目标。
