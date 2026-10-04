# Sapphire 自定义指令与 TinyML 接入约定

对应阶段 5；2026-10-04 根据用户指定资料和实际源码核对。此文描述已核实的接口与后续设计约束，不表示加速器已接入视频工程。

## 资料与版本

| 本地文件 | 阅读位置 | 用途 |
|---|---|---|
| `refs/Board/2、RISCV Custom Instruction.pdf` | 第 3–6 页 | CI 架构、软件调用和握手示例 |
| `refs/Board/riscv-sapphire-ds-v6.1.pdf` | 第 13–14、25 页，表 44、图 6 | 缓存一致性、BSP 地址和接口定义 |
| `refs/TinyML/4、TinyML 框架介绍.pdf` | 第 2–9 页 | 软件分层、初始化/推理循环与加速回退 |

PDF 中的图表已渲染核对；原始文件仅保留本地 refs。演示资料日期为 2025.6，当前 runtime 则固定为官方 `efinity-v2026.1.132`、提交 `96886fa0c73e25e6218db7d0863f84677cf65138`。示例目录和函数布局有版本差异，以实际匹配的 IP/BSP/runtime 为准。

## 一条自定义指令如何经过 CPU 和 RTL

软件用 BSP 的 `opcode_R(opcode, func3, func7, rs1, rs2)` 描述 R-type 指令。Sapphire 将两个寄存器值交给外部逻辑，外部逻辑完成运算后返回一个结果。10 位 `function_id` 可区分 1,024 个功能；具体 ID 必须与所采用 TinyML RTL/库对应，不能自行占用厂商 ID。

| 信号 | 相对 CPU 的方向 | 含义 |
|---|---|---|
| `cmd_valid` / `cmd_ready` | 输出 / 输入 | CPU 提交命令；逻辑允许接收 |
| `function_id[9:0]` | 输出 | 功能选择 |
| `inputs_0[31:0]`、`inputs_1[31:0]` | 输出 | rs1、rs2 |
| `rsp_valid` / `rsp_ready` | 输入 / 输出 | 结果可用；CPU 允许接收 |
| `outputs_0[31:0]` | 输入 | 返回的 32 位结果 |

命令在时钟沿上 `cmd_valid && cmd_ready` 时接收，结果在 `rsp_valid && rsp_ready` 时消费。结果计算完成与 CPU 取走结果是两个事件：自己的接口封装应保持待接收结果，直到握手完成。仿真需覆盖输入等待、输出反压、复位和连续事务，避免同一条指令重复执行。

教学幻灯片第 6 页是简化模板，未提供完整运算和所有状态转移，不作为可直接综合的生产模块。这里的保持/反压要求是本项目的实现约束，应通过仿真验证。

## TinyML 分层对我们的意义

应用负责模型、输入、输出和 tensor arena；TFLite Micro 注册并调用算子；厂商算子驱动选择软件或 CI/RTL 运算；BSP 提供 UART、计时、地址等平台信息。初始化时分配张量并检查模型契约，循环中填输入、`Invoke()`、读输出。

第一步固定模型与三组 golden 输入，使用禁用加速配置的静态固件建立目标 CPU 基准；之后保持输入、模型和判定规则不变，启用匹配的 TinyML 加速器比较输出和周期。当前固件不调用 `init_accel()`，因为它会探测硬件自定义指令；厂商 `hw_accel_setting[0]` 保持零初始化。链接库仍含加速路径，因此“未启用加速配置”不等于 ELF 中完全不含自定义指令代码，实际运行还需验证。

本模型主要计算来自 Conv2D，另有 MaxPool、AveragePool、Reshape、FullyConnected。资料中 Add 算子的性能例子不能推算本 CNN 的加速比或 FPS；最终按本模型逐层耗时、端到端时间与资源/时序报告选配置。

## DDR 与缓存不能只靠接线解决

数据手册第 13 页描述 write-through cache，同时明确 DMA/AXI slave 与 CPU cache 不自动一致。DMA 更新内存后，CPU 再读取相关缓存地址前需要匹配 BSP 的 invalidate 操作；还要用完成握手与内存屏障保证先后顺序。仅添加 `volatile` 不能替代缓存一致性维护。

本工程视频已保留低 48 MiB。当前交叉编译用的厂商静态 BSP 从 `0x1000` 链接，**与视频帧槽冲突**，只能作为独立静态验证固件的构建依据。集成版必须同时设计视频槽、CPU 代码/栈/堆、arena、输入双缓冲及 AXI 仲裁；改变 IP 地址后重新生成对应 BSP，不能只手改 `soc.h`。

摄像头 PCLK 与 SoC/DDR 时钟不同。先在取帧边界转移缓冲所有权，并携带 `frame_id`，推理完成后释放；不能让 CPU 读取正在被摄像头覆盖的输入。最终 HDMI 标签与对应帧对齐属于阶段 6 验收。

## 当前验证边界

已完成文档核对、RAW8 接口仿真、静态固件交叉编译。尚未完成新的 Sapphire 硬件生成、视频系统地址重映射、CI 连线、目标 golden 回放、arena 实测或 15 FPS。构建和源码解释见 [静态固件教程](riscv_static_firmware.md)。
