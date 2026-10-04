# 从 Efinity IP 生成到 RISC-V 应用：本板 TinyML 工作流

2026-10-04，依据用户指定的官方 2026.1 示例、`README_NEW.md`、EVSoC User Guide v7.0、Sapphire User Guide v8.2 和 Data Sheet v6.1。先生成硬件对应的 IP/BSP，再编译应用，是本项目后续的执行顺序。

## 四个示例各自用来参考什么

| 官方目录（`refs/TinyML/upstream-2026.1/` 内） | 软件应用 | 本项目借鉴内容 |
|---|---|---|
| `tinyml_hello_world/Ti60F225_tinyml_hello_world` | `tinyml_imgc` 等静态应用 | Sapphire、TinyML、模型加载、静态输入与输出验证 |
| `tinyml_vision/Ti60F225_mobilenetv1_person_detect_demo` | `evsoc_tinyml_pdti8` | 96×96 灰度输入、摄像头 DMA、预处理、分类结果显示 |
| `tinyml_vision/Ti60F225_yolo_person_detect_demo` | `evsoc_tinyml_ypd` | 96×96 RGB、检测框后处理与叠加 |
| `tinyml_vision/Ti60F225_mediapipe_face_landmark_demo` | `evsoc_tinyml_fl` | 192×192 RGB、多输出结果及图像坐标映射 |

四个 Ti60 示例的设置都包含 HyperRAM IP；视觉示例还有 CSI-2 摄像头、DSI 显示和相应 FIFO。它们面向官方开发板，不能直接替代我们的 DDR3、并行 AR0135 和 HDMI 接口。本项目复用其初始化、DMA/推理/后处理组织方式，外围继续按自己的板卡工程适配。

第一个模型保持 64×64 灰度三分类。官方视觉预处理使用最近邻，而训练使用 Pillow bilinear；不能直接换算法后沿用此前精度结论。第二个模型仍放在当前模型部署验证之后。

## 1. 创建独立硬件工程

所有 FPGA 改动位于 `C:/Users/SteLl1a/Desktop/CNN-Tutorial-FPGA`，原 `fpga-w.-codex` 不修改。厂商源码和生成结果位于副本 ignored `artifacts/`，Git 保存适配脚本、配置差异和说明。

当前 `tools/prepare_cnn_hardware.py` 以本地 DDR3 示例的板级连接为起点，使用官方固定提交 `96886fa0c73e25e6218db7d0863f84677cf65138` 的 Sapphire 设置。候选工程改为 C4、CPU/外设各 100 MHz；同步修改 CPU PLL 输出分频与 SDC。它是静态验证候选，仍需完整综合/布局布线/时序核验。

DDR 控制器需要独立 AW/AR 通道，故明确设置 `DDR_AXI4=1`。直接照搬官方 HyperRAM 示例的 `DDR_AXI4=0` 会生成 `io_ddrA_arw_*` 合并地址端口，与本地 DDR3 顶层接口不匹配。接口错误应在生成模板对照阶段发现，不能等下载后才排查。

## 2. 在 Efinity 生成 IP

GUI 操作：打开候选工程 XML → Project 中 IP 节点 → Generate All。调整 Sapphire 参数时进入 Configure，再 Generate。EVSoC 指南第 37 页和 Sapphire 指南第 12–14 页分别说明此步骤和生成文件。

本项目也提供调用相同已安装 IP Manager API 的脚本 `tools/generate_cnn_sapphire.py`，供可复现运行。它调用 `create_ip`、`config_ip`、`validate_ip`、`generate_ip`，然后核对 RTL、实例模板与 `soc.h` 文件确实存在。API 用法参考 Efinity 安装目录自带 `project/example_scripts/ipm/example_fifo.py`。

生成目录应包含：

```text
<hardware-project>/
  ip/SapphireSoc/
    SapphireSoc.v
    SapphireSoc_tmpl.v
    SapphireSoc_define.vh
    settings.json
  embedded_sw/SapphireSoc/
    bsp/efinix/EfxSapphireSoc/
      openocd/             # 本次 2026.1 实际生成的调试配置
    software/standalone/
    tool/
    cpu0.yaml
```

核对 `SapphireSoc_tmpl.v` 与顶层实例所有命名端口，并核对 `soc.h` 的外设地址/时钟、`soc.mk` 的 ISA 选项、linker 的 RAM 区间。生成目录存在不代表地址、时钟和连接已经匹配。

不能把 IP 源再次手动重复加入 Design：IP Manager 的 IP 节点会管理该源码。其他 IP 也必须按同版工具完成生成和接口检查，不能把“仅 Sapphire 已生成”写成“全部 IP 已生成”。

## 编译硬件，再用匹配的 BSP 编译应用

硬件运行完整 Compile，并审阅资源、时序及未约束路径。通过后得到 JTAG `.bit` 或 SPI `.hex`；官方 quickstart 的预编译文件只适用于其对应开发板。本项目尚不直接使用它给 DDR3 板卡下载。

在 RISC-V IDE 中把 workspace 设置为候选工程的 `embedded_sw/SapphireSoc`，导入 `software/standalone` 下的应用。我们的模型自检应用源码来自 `firmware/cnn_static/main.cc`，模型数据由训练项目的 `scripts/export_board_bundle.py` 生成。

上一轮使用旧 BSP 的 ELF 只是工具链可行性证据。新 IP 生成后必须用**这个硬件工程的新 BSP**重新编译；不要混用不同 workspace 的 `soc.h`、linker 或 OpenOCD 设置。当前 linker 的静态布局仍与视频帧槽重叠，静态工程独立运行，视频集成另做内存分区。

## 下载与 OpenOCD 调试

先加载经过本板适配及验证的 FPGA bitstream，再启动匹配 BSP 的 OpenOCD 配置，最后下载 ELF 到 CPU 内存、启动程序并读取 UART。本次 Titanium hard TAP 生成 `openocd/ftdi_ti.cfg` 和 `debug_ti.cfg`。不能照搬旧版 `config/default_ti.launch` 路径。

实际下载器是 FT232H（0403:6014、单通道），而官方默认配置为 0403:6011、channel 1。除设备描述外，VID/PID 和 channel 也必须按枚举结果适配；未经核对不能启动默认调试配置。

EVSoC 指南第 19 页指出，Efinity Debugger 与 OpenOCD 默认共用 hard JTAG TAP，同时占用会冲突。初次调试只保留一个访问会话。若以后确需同时使用，再按指南配置 soft TAP 和独立连接。

设备枚举只用于识别，不是应用下载。实测 Efinity `ftdi_pgm.bat --list_usb` 找到 FT232H；随后 `jtag_chain_detect.py` 检测到一颗 Ti60，IDCODE `0x10660a79`。JTAG URL 包含 USB 总线位置，拔插后应重新枚举，不能硬编码成永久地址。UART CH340 当前为 COM8。此次未加载 bitstream 或 ELF。

## 按层验收

依次通过 UART/计时 → DDR 读写 → 三组静态 golden → TinyML 加速结果对齐 → 相机 ROI/缩放对齐 → 连续帧和 HDMI 标签叠加。静态 golden 必须保存原始日志和模型哈希；计时使用实际 CPU 频率换算，arena 使用解释器报告值。

阶段 6 的 15 FPS 验收需包含采集、缓冲等待、预处理、推理与输出更新，不能只用单个算子加速比或编译频率推算。板上无手背景与真实光照的识别质量需另采集数据验证。

## 本机工具路径更新

用户已将目录中的空格改为下划线，当前实际位置为：

- Efinity：`C:/Users/SteLl1a/Desktop/Work/FPGA_Contest/env/Efinity_IDE/2026.1`
- RISC-V SDK：`C:/Users/SteLl1a/Desktop/Work/FPGA_Contest/env/RISCV-IDE`
- 本地 DDR3 示例：`C:/Users/SteLl1a/Desktop/Work/FPGA_Contest/demo/tinyml-main/tinyml_hello_world/Ti60F225_tinyml_helloworld`

历史构建报告保留当时原路径以便追溯；重新构建应使用当前路径。另发现用户桌面 `tinyml-main` 官方示例正在被 Efinity 综合，本项目未停止或改动该运行。
