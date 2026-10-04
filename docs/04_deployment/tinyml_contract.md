# TinyML 部署约束与阶段计划

## 从本地资料得到的结论

已检查 `refs/TinyML/README.md`、`tools/tinyml_generator/README.md`、`1_3_EVSOC_tinyml用户手册_0416.pdf`（36 页）以及两份 TinyML 介绍 PDF。

- 用户手册 §3.4.2：TinyML Generator 导入 `.tflite`，配置加速器并生成硬件/软件模型文件。
- 用户手册 §3.4.3（PDF 第 32–36 页）：代表性样本、`TFLITE_BUILTINS_INT8`、INT8 输入输出。
- 本地 generator README：加速类型包含 Conv/Depthwise、Fully Connected、Add、Mul、Min/Max；可配置并行度、缓存和 AXI 宽度。
- 介绍资料展示 Ti60 示例，但这不能证明用户现有工程使用同型号/配置。等现有 FPGA 工程交付后再核定器件、DDR3、Sapphire SoC、时钟、DSP/BRAM 与可用资源。

原始厂商资料只在本地保存。公开框架入口：[Efinix TinyML](https://www.efinixinc.com/solutions-tinyml.html)、[Efinix-Inc/tinyml](https://github.com/Efinix-Inc/tinyml)。

## 量化路线（阶段 4 桌面验证完成，板端待验证）

v0.3 已完成下面第 1–6 项及本地厂商分析器检查，INT8 accuracy 95.43%，下降 0.27 个百分点，详见 [量化教程](int8_conversion.md) 与 [实测报告](../05_experiments/v0.3/README.md)。目标工程编译与板上静态对齐尚未执行，阶段勾选由用户确认。

1. 冻结训练模型、预处理、类别表和验证协议。
2. 在独立 TensorFlow 环境逐层重建等价网络。卷积权重从 PyTorch `OIHW` 转为 Keras `HWIO`。特别注意 Flatten：PyTorch 按 CHW 展开，Keras 默认按 HWC 展开，Dense 的输入权重必须重排；不能只转置矩阵。
3. 使用同一真实样本检查 PyTorch 与 Keras 浮点 logits，记录最大绝对误差与类别一致率；失败时禁止继续宣称转换正确。
4. 从训练集另抽 100–500 张代表性样本做校准，覆盖手势、亮度和背景；不能使用随机噪声代替真实校准，不能动用最终测试集校准。
5. 设置 `Optimize.DEFAULT`、`TFLITE_BUILTINS_INT8`、`inference_input_type=tf.int8`、`inference_output_type=tf.int8`。保存模型后检查算子、版本和张量类型，不能容许隐藏的 float fallback。
6. 对同一冻结测试集分别评估 FP32 与 INT8；输出 dtype 为 INT8 只是检查的一部分，bias/shape 等 INT32 张量是正常的。
7. 将模型导入用户实际版本的 TinyML Generator，核实全部算子是否被 TFLM resolver 支持、哪些层加速、哪些层软件执行，随后做板上静态输入 golden comparison。

参考：[Google 全整数量化说明](https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_integer_quant)。TFLite 可生成不代表兼容某个旧版板卡 TFLite Micro；还需要 schema、算子版本、tensor arena 与实际编译验证。

## 输入输出约定

FP32 输入 `x = grayscale_uint8 / 255`。TFLite INT8 输入必须读取模型中的 scale、zero_point，计算 `q = clip(round(x / scale) + zero_point, -128, 127)`；不能凭经验直接 `uint8-128`。反量化输出为 `scale * (q-zero_point)`。所有路径保持 paper、rock、scissors 的固定类别顺序。

板端需与 Python 对齐灰度定义、ROI、resize、像素方向、stride、量化舍入与饱和规则。AR0135 原始位深若超过 8 bit，需要明确黑电平/曝光及映射规则，不能未经核实就截断低位。

## 摄像头建议

首个模型继续使用现有黑白 AR0135：手势形状分类可先使用单通道，减少输入带宽，并复用已调通的链路。公开 RGB 图转灰度与实际传感器输出仍有域差异，所以仍要采集实拍。

后续识别依赖颜色区分的物品、复杂背景检测，才评估 OV5640 或 MIPI 彩色摄像头。1080p 分辨率本身不会让小模型更准确；输入通常仍需缩放到几十或一百多像素。选型取决于接口/IP、灰度/彩色要求、曝光和板上资源，当前不要求购买或更换摄像头。

## 与已有视频系统集成

原图采样分支 → 方形 ROI → 灰度/resize → 模型输入缓冲 → INT8 推理 → 类别和状态寄存器 → HDMI 叠加。Sobel 可继续作为独立显示分支；模型不用 Sobel 图训练或推理。分类结果显示类别/置信度与 ROI，不伪造检测框。

先静态图片，再单帧摄像头，再双缓冲连续采集。标记 frame_id、缓冲所有权和结果时间戳，避免采集覆盖推理输入或将旧结果错误对应到当前画面。摄像头帧率、HDMI 刷新率和推理 FPS 分别报告。

15 FPS 对应平均每次推理约 66.7 ms，但还需计入预处理、DDR 传输、CPU 后处理与帧同步。测量端到端吞吐、平均/p95 延迟、丢帧与资源占用。模型参数少不代表这些开销小，也不能把 PC CUDA 的性能当作 FPGA 性能。
