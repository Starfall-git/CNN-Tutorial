# 数据、训练与可信评估

## 教学数据

使用 Laurence Moroney 的 Rock Paper Scissors 数据，官方下载地址由 [TensorFlow Datasets 目录](https://www.tensorflow.org/datasets/catalog/rock_paper_scissors) 和其 builder 源码提供。官方训练集 2,520 张，测试集 372 张，原图 300×300 RGB。本工程转换为 64×64 灰度。

这是受控的合成手势教学数据。高分不代表对 AR0135、复杂背景、真实光照、不同人或无手场景也有相同性能。[原作者页面](https://laurencemoroney.com/datasets.html) 说明采用 CGI 生成、白色背景，许可为 CC BY 2.0；使用时保留 Laurence Moroney 署名和来源。原始数据不提交到仓库。

注意：本工程固定类别为 `paper=0, rock=1, scissors=2`；TFDS builder 原生顺序不同，不能直接混用 TFDS 的整数标签。

运行：

```bat
python scripts/prepare_data.py
```

脚本保存 ZIP SHA-256、样本路径与内容哈希。ZIP CRC 用于检查传输完整性，本地记录的 SHA-256 用于后续复现，不能冒充事先从发布方核实的摘要。读取官方训练集后按类别、固定种子 42 划分为 2,016 训练 / 504 验证；官方测试集始终保留 372 张。划分写入 `data/rps/manifest.json`，检查完全相同文件的重复。

当前验证划分按图片随机抽取，可能含同一渲染序列或近似姿态，因此只能用于教学优化。完全相同文件检查不能排除近重复或同人的泄漏。真实验收集必须按人、采集会话和背景分组划分，连续帧放在同一组。

## 训练过程

训练集使用小角度旋转、左右翻转和亮度扰动；验证与测试不做随机增强。仅使用与左右手无关的类别时才适合镜像增强。

默认 Adam，初始学习率 0.001，weight decay 0.0001，batch 64，25 epochs，余弦学习率调度。每轮记录损失与准确率。最佳权重由验证准确率选择；相同时选择验证损失更低的一轮。测试集不参与调参和权重选择。

```bat
python scripts/train.py --epochs 25 --run rps-baseline --test
```

已有同名 run 会报错，防止覆盖实验。Notebook 02 自动生成时间戳目录。训练会保存 `best.pt`、`history.json`、`summary.json`；显式最终测试生成 `test_metrics.json`。

训练后可对一张已经裁剪好的正方形 ROI 运行 `python scripts/predict.py artifacts/<run>/best.pt path/to/roi.png`。脚本只做闭集分类，没有定位或背景拒识功能。

## 评估与验收提案

报告 accuracy、macro-F1、各类 precision/recall、混淆矩阵（行是真实类，列是预测类），同时记录参数量、MACs、数据和权重哈希。

拟定目标：公开测试集 accuracy ≥95%、macro-F1 ≥0.95；真实独立摄像头测试集另定门槛；INT8 相对 FP32 accuracy 下降不超过 2 个百分点。上述门槛是候选标准，需要用户阶段确认，不是预先宣称已经达成。

不要根据测试集逐次调参。优化候选仅比较验证集，模型冻结后再测试；若已反复观察测试错误，后续改动必须额外保留新的最终验收数据。

## 云端训练选择

本机 8 GB GPU 足以训练这个小模型。需要云端时可将源码和 notebooks 上传到自己的 Colab/Kaggle Notebook，安装依赖、使用同一 manifest 与种子，并保存实验报告。避免在 notebook 中保存访问令牌。

[Ultralytics Platform](https://docs.ultralytics.com/platform/) 可用于后续 YOLO 数据管理、训练与导出工作流参考。当前自定义 `GrayGestureCNN` 并不是 Ultralytics YOLO 模型，不能直接拿它的 checkpoint 交给 YOLO 训练命令。第二模型再根据板卡资源和 TFLite 算子审计选择检测架构；不要默认 YOLOv3 或带 nano 名称的模型必然能在板上达到 15 FPS。
