# v0.3.0 · 阶段 4：INT8 转换与精度回归

2026-10-04 实测完成。沿用 v0.2 最终 refit 模型，只执行一次 PTQ 配置，没有根据测试结果重选校准集或训练参数。转换与教学步骤见 [量化文档](../../04_deployment/int8_conversion.md) 和 [Notebook 04](../../../notebooks/04_int8_quantization.ipynb)。

## 结果

| 指标 | FP32 | 全整数 INT8 |
|---|---:|---:|
| 参数量 | 26,371 | 26,371 |
| Conv + Linear MACs | 10,030,080 | 相同网络计算结构 |
| 官方基准正确数 / 总数 | 356 / 372 | 355 / 372 |
| Accuracy | 95.6989% | 95.4301% |
| Macro-F1 | 0.9563 | 0.9535 |
| paper recall | 87.0968% | 86.2903% |
| rock / scissors recall | 100% / 100% | 100% / 100% |
| 模型文件大小 | checkpoint 含额外训练元数据，不直接比较 | **33,240 B = 32.46 KiB** |

下降 **0.2688 个百分点**，通过预先约定的 ≤2 个百分点回归标准。FP32 PyTorch/Keras 的 logits 最大绝对误差为 `1.049041748046875e-05`，372 张图预测类别完全一致。INT8 的主要错误仍在 paper 类，混淆矩阵（行真值，列预测；paper/rock/scissors 顺序）为：

```text
107  12   5
  0 124   0
  0   0 124
```

这是已观察过的合成数据基准，不能推断真实相机准确率。当前模型没有无手背景类。

## 转换与审计证据

- [report.json](report.json)：精度、类别召回、文件大小、量化参数、模型哈希。
- [conversion_manifest.json](conversion_manifest.json)：冻结权重与交换文件哈希，300 张训练侧校准图清单；评估集 372 张未用于校准。
- [graph_audit.json](graph_audit.json)：FlatBuffer schema 3，单 subgraph，14 个 INT8 张量、5 个 INT32 张量，无浮点或自定义算子。
- 算子版本：Conv2D v3、MaxPool2D v2、AveragePool2D v2、Reshape v1、FullyConnected v4。ReLU 融合在卷积中。
- [golden_manifest.json](golden_manifest.json)：三类各一份固定输入/输出字节、哈希和类别；独立桌面 interpreter 逐字节回放通过。
- [厂商分析日志](vendor_analyzer.md) / [调用记录](vendor_analysis.json)：随 refs 提供的 `tflite.exe` 返回 0，识别 Conv/FC 加速选项；1/1 仅为分析探测参数，没有生成 RTL 配置。
- [环境快照](quant_environment.txt)：Python 3.11.16，TensorFlow 2.15.1，NumPy 1.26.4；`pip check` 通过。
- [所有本地产物哈希](artifact_sha256.json)：用于后续交接校验；二进制模型、交换数据、golden 字节按约定保留在本地 artifacts。

模型 SHA-256：`7891518a9b70ec6b3be8649123651780ce87ede1e69a9a49c394c17d203a0baa`。

Notebook 04 的默认报告回放和 `RUN_CONVERSION=True` 完整转换分支均在真实 Jupyter kernel 中通过。第二次导出的模型 SHA-256 与首轮相同。8 项 CPU 契约测试、5 本 notebook 格式与 Markdown 代码说明检查、文档相对链接检查均通过。

## 输入输出与性能边界

输入 `[1,64,64,1]`、signed INT8，scale `0.003921568859368563`，zero point `-128`。输出 `[1,3]`、signed INT8，scale `0.14151470363140106`，zero point `4`；输出是 logits，索引顺序为 paper、rock、scissors。

TensorFlow 转换日志的 MAC 估计约 10.147M，包含与项目 Conv+Linear 统计不同的运算口径，不能将两者混用。文件大小也不等于 arena 或 FPGA 资源占用。本地分析器通过并不证明目标工程算子注册、ABI 或加速核版本兼容。

**本次完成阶段 4 的桌面量化技术验证**；阶段清单仍由用户确认。阶段 5/6 尚未完成：缺实际板卡工程，未测 arena、端到端延迟、FPS、相机输入对齐和 HDMI 叠加。下一步先用 golden vectors 接入目标 TFLite Micro，再接实时 ROI。
