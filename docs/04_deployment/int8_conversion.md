# 阶段 4：从 PyTorch 权重到全整数 TFLite

本章使用阶段 3 已冻结的 26,371 参数模型，不重新训练或用测试集选配置。教程入口为 [Notebook 04](../../notebooks/04_int8_quantization.ipynb)，真实结果集中放在 [v0.3 实验记录](../05_experiments/v0.3/README.md)。FPGA 部署约束见 [TinyML 约定](tinyml_contract.md)。

## 1. 两个环境，各自承担一个任务

`CNN-Tutorial` 保留 PyTorch CUDA 训练环境；`CNN-Tutorial-Quant` 使用 Python 3.11、TensorFlow 2.15.1 和 NumPy 1.26.4，在 CPU 上转换。先在 Anaconda Prompt 中执行：

```bat
conda create -n CNN-Tutorial-Quant python=3.11
conda activate CNN-Tutorial-Quant
python -m pip install -r requirements-quant.txt
```

环境已经存在时跳过创建命令。不要把量化依赖装到训练环境。本机已安装的完整依赖快照保存在实验目录，`requirements-quant.txt` 只固定核心依赖。

## 2. 冻结输入，分开校准与评估

在训练环境运行 `python scripts/prepare_conversion.py`。脚本读取 refit checkpoint，并核对类别顺序和训练 manifest 的 SHA-256；输出无 pickle 的 NPZ 交换文件：

| 文件 | 用途 |
|---|---|
| `weights.npz` | 冻结的卷积与分类头权重 |
| `calibration.npz` | 训练池内每类 100 张，共 300 张，用于估计激活范围 |
| `evaluation.npz` | 官方测试集 372 张与 PyTorch logits，用于回归比较 |
| `manifest.json` | 输入文件哈希、checkpoint 哈希、类别与预处理约定 |

校准和评估分别走不同文件，内容哈希交叉检查在准备阶段执行。当前校准图仍是合成手势，不能代表真实相机的光照与背景；后续接相机时应补充训练侧代表性实拍图，另留实拍测试集。

## 3. 为什么必须重排权重

PyTorch 卷积权重是 `[out, in, h, w]`，Keras 是 `[h, w, in, out]`，使用 `transpose(2, 3, 1, 0)`。两者的池化输出布局也不同：PyTorch Flatten 展开 CHW，而 Keras 展开 HWC。仅对全连接矩阵转置会把每个权重连到错误的像素/通道。

`cnn_tutorial/quantization.py` 的 `dense_chw_to_hwc` 先恢复 `[类别, C, H, W]`，再按 HWC 顺序展开，最后得到 Keras 的 `[输入特征, 类别]` 矩阵。非正方形特征的单元测试检查这个变换保持线性函数不变；转换时进一步对全部 372 张图检查 FP32 logits，容差 `rtol=1e-4, atol=1e-4`，并要求预测类别完全相同。

## 4. 全整数转换与验收

在量化环境运行：

```bat
python scripts/convert_int8.py
python scripts/verify_golden.py
```

输出默认放入 `artifacts/v0.3-int8/`，已有目录会被拒绝覆盖。重跑时通过 `--output-dir artifacts/你的新目录` 指定新位置。

转换器设置 `Optimize.DEFAULT`、真实代表性数据生成器、`TFLITE_BUILTINS_INT8`，同时指定 INT8 输入和输出。这个组合防止浮点算子回退；用法依据 [TensorFlow 全整数转换说明](https://www.tensorflow.org/lite/performance/post_training_quantization)。

`tflite_audit.py` 直接解析 FlatBuffer，保存 schema、算子版本、张量类型和形状；仅允许本模型所需的五类内置算子，拒绝自定义算子和浮点张量。INT32 偏置和 reshape 的形状常量是预期内容，全整数不意味着每个张量都是 INT8。量化权重/激活的约束依据 [TFLite 8 位量化规范](https://www.tensorflow.org/lite/performance/quantization_spec)。

精度验收使用预先约定的“相同测试集相对 FP32 下降不超过 2 个百分点”。若报告里的 `acceptance_drop_at_most_2pp` 为 false，保留失败结果做诊断，不宣称通过。当前公开测试集已经在前序阶段被观察过，所以这些数字属于回顾性基准，不能替代新采集的实拍验收集。

## 5. 板端必须遵守的输入输出约定

输入为单张 `[1,64,64,1]` NHWC 灰度图。先按训练约定取得方形 ROI、转灰度、双线性缩放，再做 `x = gray / 255`，最后执行：

```text
q = clip(round_to_nearest_even(x / input_scale) + input_zero_point, -128, 127)
logit = (q_out - output_zero_point) * output_scale
```

使用模型报告里的实际 scale/zero point，不把 uint8 图像直接强制转换为 int8。Python 使用 `np.rint`（恰好半整数时取偶数）再饱和截断。板上缩放的采样坐标、舍入和 AR0135 位深转换需用单独图像对齐实验确定；摄像头高位深数据的黑电平与曝光不在本阶段猜定。

输出是三个 logits，索引顺序固定 `paper, rock, scissors`。可直接 argmax；相同最大值取最小索引。图中不包含 softmax，也没有无手背景类。`golden/` 提供每类一份确定性的测试输入和期望 INT8 输出，各文件有 SHA-256，可先脱离摄像头回放。桌面回放要求逐字节一致；目标内核若有舍入差异，先记录最大字节误差和类别是否一致，再判断原因，不能只检查“能运行”。

## 6. 接入 TinyML 的边界

本地厂商 Generator 自带 `bin/tflite.exe`，GUI 传参为 `模型路径 输入并行度 输出并行度`；可先用它做静态分析。其输出只代表随工具附带的分析器，不代表实际板卡固件。Conv/FC 有硬件加速选项；池化、reshape 的执行路径和算子注册要在目标工程核对。

模型文件大小不等于 tensor arena。最终 arena、AXI 宽度、并行度和时钟必须根据用户提供的器件、DDR/总线与已用资源选择。阶段 5 先完成静态向量对齐，再接 ROI，最后阶段 6 测连续视频和叠加显示；15 FPS 对应端到端每帧约 66.7 ms，需要包括采集、缩放、搬运、推理和叠加。
