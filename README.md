# CNN-Tutorial

面向易灵思 FPGA TinyML 的小模型实战教程。首个模型是 **64×64 灰度静态手势分类 CNN**，按石头、剪刀、布建立可复现基线。

从 [MAIN.md](MAIN.md) 查看约束、阶段和版本记录，从 [环境与启动](docs/01_setup/environment.md) 开始操作。

学习顺序：

1. `notebooks/00_environment.ipynb`：检查 Python、PyTorch、GPU 与目录。
2. `notebooks/01_gray_gesture_cnn.ipynb`：输入张量、卷积、池化、分类头、梯度与模型规模。
3. `notebooks/02_train_validate.ipynb`：数据划分、训练、验证选择、最终测试与错误分析。
4. `notebooks/03_grouped_optimization.ipynb`：序列分组验证、有限候选比较、冻结配置与最终训练。
5. `notebooks/04_int8_quantization.ipynb`：权重布局转换、训练侧校准、全整数图审计、精度回归与静态回放。
6. `notebooks/05_riscv_static_bringup.ipynb`：RISC-V 固件构建证据、ELF 哈希和内存占用，默认回放真实报告。

最终模型使用 26,371 个参数，在官方合成手势基准上 FP32 accuracy 为 95.70%，INT8 为 95.43%，下降 0.27 个百分点。全整数 `.tflite` 为 33,240 字节；详细结果见 [v0.2 训练报告](docs/05_experiments/v0.2/README.md) 与 [v0.3 量化报告](docs/05_experiments/v0.3/README.md)。真实摄像头与板端性能仍待验证。

每段代码前都有 Markdown 解释；通用训练实现位于 `cnn_tutorial/`。模型与数据保留在本地的 `artifacts/`、`data/`，厂商原始资料放在 `refs/`。Git 仓库只保存可复现代码、教程与小体积实验报告。

当前教学模型不含无手背景类，不能作为实际摄像头手势系统直接上线。板上 15 FPS 是待测目标。

阶段 5.3 已完成静态固件交叉编译；[构建教程](docs/04_deployment/riscv_static_firmware.md) 和 [自定义指令/缓存约定](docs/04_deployment/riscv_custom_instruction.md) 说明下一步上板验证。实际 FPGA 修改在独立副本 `CNN-Tutorial-FPGA`；原 `fpga-w.-codex` 目录不修改。
