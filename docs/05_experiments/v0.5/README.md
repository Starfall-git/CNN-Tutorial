# 官方 EVSoC 路线：生成和编译证据

2026-10-04；属于阶段 5 的中间子步骤，不代表双链路系统完成。

## 官方工具生成

`scripts/generate_official_tinyml.py` 调用固定官方 2026.1 的原始生成器方法，Efinity Python/PyQt6 执行。首次试用 offscreen 插件未生成文件，本机只有 windows 插件；改为隐藏的 Windows Qt widgets 后实际生成成功。脚本以产物存在及模型数组字节比对确认结果，不能只看 python3.bat 的退出码。

输出目录 `artifacts/v0.5-official-generator-r2/output/gesture_int8_core0`：

- `tinyml_core0_define.v`：AXI 128、STANDARD 卷积 4×4、FC STANDARD、RESHAPE STANDARD、cache 1024；不用的 ADD/LR/MUL/MIN_MAX 禁用。
- `gesture_int8_model_data.cc/.h`：与冻结 TFLite 的 33,240 字节完全一致。
- 详细参数与哈希：[official_generation.json](official_generation.json)。并行度是待硬件测量的候选，不是 FPS 结论。

## 官方源代码与 Makefile

FPGA 副本脚本顺序：`prepare_evsoc_gesture.py` → `adapt_evsoc_static.py` → `build_evsoc_application.py`。

工作目录 `artifacts/evsoc-gesture-r1` 来自用户指定的官方 YOLO demo。原 `main.cc`、两个顶层和项目文件保留快照；派生主程序沿用 TinyML 初始化/Invoke/CLINT 流程，输入换成三组已冻结 golden，输出检查 [1,3] INT8、量化参数、逐字节误差。当前只运行静态验证入口，不执行 PiCam/DSI 初始化。

新版运行时从硬件查询加速参数；旧 `src/model/define.cc` 与 `accel_settings.cc` 重复定义 `layer_mode`。仅从新应用 Makefile 的 SRCS 排除旧定义和旧 YOLO 模型数组，保留参考文件。加入链接未引用节回收，未手工替换编译工具链或绕过官方 Makefile。

最终 make 返回 0，ELF SHA-256 `b7889b9da8efb41862dd6faacde94fb8331f9b4e14ef60e9f30efd3900f67b5f`。

| 区域 | 字节 |
|---|---:|
| text | 780,396 |
| data | 77,078 |
| bss（含默认 2 MiB 栈） | 2,365,704 |
| tensor arena 预分配上限 | 262,144 |
| 应用动态 scratch 容量 | 500,000 |

`AllOpsResolver` 仍沿用官方示例，固件大小不是模型参数量；后续可依据五种算子精简 resolver。arena 实际用量尚未在板上测得。

完整证据：[official_build.json](official_build.json)、[integration_manifest.json](integration_manifest.json)。当前 BSP 仍来自官方 HyperRAM 示例，尚未匹配最终 DDR3 顶层；不得将此 ELF 直接加载进现有视频 bitstream。

## 尚未完成

双链路顶层、共享 DDR 有界仲裁与地址分区、RAW8 crop/resize 一致性、CDC 缓冲、UART AI 控制、Overlay 和真实 FPS 都待实现/验证。旧静态候选 r3 的 PNR 因 `jtag_inst2_TDI` 缺失失败，未进行下载。
