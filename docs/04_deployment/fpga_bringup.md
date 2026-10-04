# 阶段 5：Ti60 工程接入记录

## 工作副本与保护边界

用户在 2026-10-04 提供工程，并明确禁止修改 `C:/Users/SteLl1a/Desktop/fpga-w.-codex`。该目录只读核对，不在其中运行会产生文件的编译或仿真。

已从 `https://github.com/Starfall-git/fpga-w.-codex.git` 新克隆到桌面 `CNN-Tutorial-FPGA`。基线为 `main` 的 `51f7e55f8ce8614f2801f93e5af9bd7bc2c91c01`，工作分支 `feat/cnn-tinyml-bringup`。原目录的未提交改动没有复制或覆盖。

## 已核实的工程事实

| 项目 | 证据与含义 |
|---|---|
| FPGA 工程入口 | `Ti60_AR0135.xml`；器件 Ti60F225，配置 timing model C4，Efinity 2026.1.132.3.9 |
| 摄像头 | AR0135，1280×720；DOUT[11:4] 作为 RAW8，过滤前两行元数据和尾部统计行 |
| 视频存储 | RAW8 转 RGB565 写 DDR；绿色仅保留高 6 位，不能无损还原原 RAW8 |
| 总线 | `axi4_ctrl` 默认 128-bit AXI 数据，32-bit 地址；已有视频访问路径，需要扩展仲裁才能接 SoC/加速器 |
| DDR 槽位 | 12×4 MiB 槽步长，预留低 48 MiB；最多 8 个保存槽，4 个用于直播调度。新增 arena 不可直接占用这段空间 |
| 时钟约束 | SDC：系统约 96 MHz，DDR core 约 192 MHz，像素约 74.4 MHz；摄像头 PCLK 约 74.25 MHz，异步域需要握手/缓冲 |
| 现有处理 | DDR 读出后支持几何、灰度/中值/高斯/Sobel/Scharr/Canny，再进入 HDMI |
| 推理基础设施 | 活跃 RTL/IP 工程未包含 Sapphire、TinyML accelerator 或嵌入式推理固件 |

仓库内资源报告记录约 18,233 XLR、109 memory blocks、18 DSP；报告生成于 2026-09-30，这只是历史构建数据，不作为本轮新综合结果。后续接 SoC 必须重做资源和时序评估。

## 本轮完成的子步骤

**5.1：独立工作副本与工程差异核对。** 已完成，保留正式视频工程接口，不用官方 DevKit 引脚表覆盖现有外围配置。

**5.2：无损 RAW8 输入接口。** `ar0135_capture` 新增 `gray8`，与原有 `pixel_valid`、`rgb565` 同拍；顶层引出 `cnn_raw_gray8`。它仍在摄像头时钟域，目前没有下游消费者，综合可能优化掉该信号。未宣称已完成输入缓冲或推理。

在独立副本运行修改前后的 ModelSim 回归：两帧 720p、共 1,843,200 个像素；新接口全 8 位逐像素匹配参考数据，原 RGB565、元数据过滤、I2C ACK/重试、运行时曝光控制同时通过。`tools/check_video_config.py` 检查通过。没有执行下载或烧写。

**5.3：静态模型测试包。** 训练项目的 `python scripts/export_board_bundle.py` 从已验证模型导出 `artifacts/v0.3-board-bundle/`：模型与 golden bytes、C++11 数组/头文件、scale/zero point 和文件哈希。生成数组中的有符号字节已做往返检查。C++ 目标编译和目标运行尚未完成。

## 工具与参考实现

- Efinity 本机路径：`C:/Users/SteLl1a/Desktop/Work/FPGA Contest/env/Efinity IDE/2026.1`。实际存在，尚未运行本轮完整 FPGA 编译。
- 可用 ModelSim：`D:/WORK/modelsim/win64`。Intel FPGA Edition 的另一安装许可证检查失败，改用此正常安装后仿真通过。
- 厂商本地静态示例：`Work/FPGA Contest/demo/tinyml-main/tinyml_hello_world/Ti60F225_tinyml_helloworld`；包含 DDR3、Sapphire 与软件 BSP，工程记录版本 2025.1.110.1.5、timing model I3。必须逐项核对，不能把其引脚/速度等级或 BSP 直接当作当前工程配置。
- 官方 [Efinix TinyML v2026.1.132](https://github.com/Efinix-Inc/tinyml/releases/tag/efinity-v2026.1.132) 已克隆至本地 `refs/TinyML/upstream-2026.1`，固定提交 `96886fa0c73e25e6218db7d0863f84677cf65138`。仅展开 Ti60 静态/视觉示例与工具；供源码与接口核对，不提交到项目仓库。
- 用户提供的 Elitestek 路径为上述 Efinity 的 `bin`。已核对该目录，未找到 RISC-V GCC、G++、Eclipse 或 OpenOCD，仅有 GCC 运行库 DLL；RISC-V IDE/交叉编译器位置仍待核实。旧示例中保存的 `D:/Elitestek/...` 是原始作者路径，不能当成本机安装位置。

## 下一步及验收顺序

1. 核对本地 DDR3 TinyML 示例的 Sapphire、custom instruction、AXI 和 BSP；确定可用 RISC-V 工具链，避免混合不匹配的 IP 与软件版本。
2. 先在独立静态工程上装载同一模型和三组 golden vectors，核实算子版本、arena、输出字节/argmax、CPU/加速器耗时。此步骤不接摄像头。
3. 设计 SoC/加速器与现有视频 DDR 的仲裁、地址分区、cache flush/invalidate 和读帧所有权。参考示例的内存映射需显式转换，不能猜定空闲地址。
4. 接入方形 ROI 和双线性缩放。训练使用 Pillow bilinear，不能直接换成现有几何读出器的最近邻而不验证精度；先软件逐像素对齐，再实现硬件版本。
5. 阶段 6 才加入结果寄存器、frame_id、HDMI 叠加和持续运行测量。15 FPS 仍需端到端实测；原图输入与 Sobel 显示分支独立。

此记录表示阶段 5 的准备与一个输入接口子步骤完成；阶段 5 整体、阶段 6 和第二模型仍未完成。阶段勾选由用户确认。
