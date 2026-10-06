# v0.5-ti60-debug-r1：Ti60 首次整机上板调试包

本次完成**阶段 6 子步骤：生成可下载的整机调试版本，并提供匹配的 JTAG 静态自检固件**。尚未完成阶段 6 的实时摄像头推理与叠加验收，阶段 7 也未开始。本包由用户明确要求在保留已知 JTAG 时序违例的情况下先行提供；不代表时序签核或板上测试通过。

## 文件和工程

- 本机解压目录：`C:\Users\SteLl1a\Desktop\CNN-Tutorial-FPGA\artifacts\releases\v0.5-ti60-debug-r1`。
- 可带走的压缩包：`C:\Users\SteLl1a\Desktop\CNN-Tutorial-FPGA\deliverables\v0.5-ti60-debug-r1.zip`。解压到路径较短、没有中文和空格的目录更便于官方工具使用。
- `hardware/Ti60_AR0135.bit`：本版 JTAG 下载文件。
- `hardware/Ti60_AR0135.hex`：同版硬件的 SPI 格式文件，仅归档；**本版没有配置完整的 Flash 软件启动链路，首次调试请选 JTAG `.bit`**。
- `firmware/evsoc_tinyml_gesture.elf`：与 96 MHz DDR3 Sapphire BSP 匹配的三组 INT8 静态自检，含调试符号及 `cnn_debug_status`。
- `manifest.json`：逐文件大小/SHA256、源提交、工具结果、已知限制。`evidence/` 保留 PGM、PNR 时序和软件构建证据。
- `source/main.cc`、`source/soc.h` 等是定位用快照；完整工程仍在 `C:\Users\SteLl1a\Desktop\CNN-Tutorial-FPGA\artifacts\evsoc-system-r1`。

注意候选工程与副本根目录是两个位置。副本根目录 `outflow` 的旧 `.bit` 不属于本版。原工程 `C:\Users\SteLl1a\Desktop\fpga-w.-codex` 没有被修改。

## 第一次：只下载硬件，检查视频

### 本次实际连接故障记录

用户截图选择的是 `SPI Active using JTAG Bridge` + `.hex`，启用自动配置桥接镜像，控制台显示到 Flash 擦除。上位机显示 COM8/115200，报未收到 FPGA 确认。只读探测也验证了 COM8 **打开成功，但 GET_STATUS 超时**；不是权限/端口占用错误。截图尚不能证明 Flash 操作最终完成、业务设计重新配置或 ELF 执行。先等待任何正在运行的 Flash 操作完成，再按下列步骤使用 JTAG `.bit`，不要在擦写中断电。

上位机入口已补齐：关闭旧 GUI 窗口，重新运行独立副本 `host/start_gui.bat`，在“图像”区、曝光按钮旁打开 **TinyML 手势**。请求值与实际值分别显示；静态固件显示“未就绪”是正常的。旧程序窗口不会自动加载新 Python 文件。

1. 解压调试包，在解压目录打开 PowerShell，运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\verify-package.ps1`。只有显示 PASS 才继续；它只校验文件。
2. 打开 Efinity/Elitestek Programmer，选择实际连接的下载器、**JTAG 模式**，选择本包 `hardware/Ti60_AR0135.bit`，执行下载。无需重新综合，也无需写 Flash。
3. 观察原 AR0135 → DDR3 → 图像处理 → HDMI 画面；用原上位机检查图像处理模式和串口控制。记录下载器提示、HDMI 是否出图、有无闪屏/花屏。此时尚未加载手势应用，不能期待出现手势标签。
4. 关闭 Programmer 的活动连接后再启动 OpenOCD，同一硬 JTAG 连接不能同时被两者占用。正常操作结束后不必断电；断电会丢失本次易失性 JTAG 配置。

## 第二次：加载软件，查看三组自检

本包沿用官方工具：Efinity 生成 bitstream，RISCV-IDE 内的 OpenOCD 和 GDB 加载 ELF。下面的脚本只是固定这些官方工具的参数，不含新的下载协议。**运行 `start-gdb.ps1` 会通过 JTAG 将 ELF 加载至目标 DDR 并启动应用**；准备包时没有代替用户执行这些操作。

1. 在解压目录第一个 PowerShell 窗口运行：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\start-openocd.ps1
   ```

   等待它报告 GDB 端口 3333 已监听且 CPU 能被 halt。包内 `debug/cnn_ft232h_ti.cfg` 从本候选 BSP 的官方 `ftdi_ti.cfg` 派生，仅适配本机已枚举的 FT232H（VID/PID `0403:6014`，channel 0）；`debug_ti.cfg` 保留官方 Titanium USER1/BSCAN 配置及 800 kHz 速率。设备枚举成功不等于 JTAG/CPU 已实测成功。

2. 第二个 PowerShell 窗口进入同一解压目录，运行：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\start-gdb.ps1
   ```

   脚本加载本包 ELF，从 `_start`（逻辑 `0x1000`）运行，在 `cnn_debug_done` 设置临时硬件断点，停止后自动打印 `cnn_debug_status`。请保留 GDB 与 OpenOCD 输出。再次从头试验时，先结束这两个调试会话，再重新下载本包 `.bit`，避免把上次 CPU/缓存状态带入新试验。

3. 安装目录不同可以给两个脚本分别加 `-Sdk '实际的RISCV-IDE目录'`。本机默认路径为 `C:\Users\SteLl1a\Desktop\Work\FPGA_Contest\env\RISCV-IDE`。

4. 使用 RISC-V IDE 图形调试也可以：应用位置是候选工程的 `embedded_sw/SapphireSoc/software/standalone/evsoc_tinyml_gesture`，导入其现有 Makefile 项目；调试时选择本包 ELF 和本候选的 FT232H/Titanium OpenOCD 配置，在 `cnn_debug_done` 设断点，并在 Expressions 中添加 `cnn_debug_status`。不要选旧 HyperRAM demo 的 BSP/ELF。上述命令行方法无需改动现有 IDE workspace。

**Build → Load → Run/Resume 是不同步骤**：Build 只在电脑上生成 ELF；配置好的 OpenOCD Debug/Run 会话才会将 ELF 加载到板上内存，再 Resume 才执行应用。截图里绿色 Run 按钮需先绑定正确的嵌入式调试配置，不能仅凭 Build Finished 判断已经烧录。当前板上原 UART 协议与视频电路应独立于这份 ELF；它们的握手超时不能单纯解释成“没有 Run”。

当前物理串口仍由原图像系统的命令控制器独占；SoC UART TX 未接出。因此**串口没有 TinyML printf 是本版预期行为**。静态自检也不设置 APB `firmware_ready`，UART 的推理可用状态保持未就绪，不会自动产生实时手势 Overlay。

## 如何判断结果

所有数值都来自目标实际运行后读取，包中只提供期望值，没有预填板上结果。

|字段|通过条件/含义|
|---|---|
|`magic`|`0x47444231`，调试结构 GDB1|
|`abi_version`|1|
|`stage` / `error`|9 / 0|
|`completed` / `passed`|3 / 3，逐个 INT8 输出精确比较|
|`actual[0]`|paper：`[11, 0, -2]`|
|`actual[1]`|rock：`[-1, 79, -60]`|
|`actual[2]`|scissors：`[1, -75, 63]`|
|`arena_used`|实际 TFLM arena 用量，应在预留 262144 字节以内|
|`clint_hz`|96000000|

每组 `ticks = ticks_hi × 2^32 + ticks_lo`，单次 Invoke 耗时为 `ticks / clint_hz` 秒。这个时间不含摄像头采集、预处理与显示，不能据此直接声称系统达到 15 FPS。调试状态发布采用与官方 EVSoC `flush_data_cache()` 相同的 D-cache 指令，避免只依靠 volatile 而读到未回写的数据；有额外调试开销。

如果没有到完成断点，可在 GDB 按 Ctrl+C，再运行：

```text
p cnn_debug_status
info registers pc mcause mepc mtval
bt
```

`stage`：1 BSP/中断初始化；2 scratch 分配；3 TFLM 模型/AllocateTensors；4 加速器初始化；5 tensor 契约检查；6 填充样本；7 Invoke；8 保存比较结果；9 全部通过；255 显式失败。`error`：1 hart 错误，2 scratch 分配失败，3 tensor 契约错误，4 Invoke 返回失败，5 至少一组输出不一致。官方初始化内部死循环或陷阱可能停在原 stage 而不到 `cnn_debug_done`；需要同时看 PC/异常寄存器。`sample` 为 0/1/2，初始化前为 `0xffffffff`。

## 保留的时序问题和本版边界

官方工具 map/interface/PNR/PGM 已成功。2×2 TinyML 配置占用 XLR 57695/60800；LUT4 35399，FF 26944，DSP48 53，RAM10 233。clk_sys 同域 setup 最差 +0.484 ns；已报告负裕量为 JTAG → clk_sys −1.307 ns、反向 −0.384 ns，约束中的跨域需求为 0.001 ns。需要继续对照官方 CDC 和时钟关系审计，**不能把它已经判定为无害违例**。本版按用户要求先允许实际调试，未用 blanket false-path 隐藏违例。官方 PGM 还输出 `cannot find correct IV value` 警告，PGM 和 bin 导出均 PASS，完整日志随包保存。

本版可用于检验“视频系统保持运行 + CPU/JTAG 可访问 + 三组静态加速器推理”的实际情况。RAW8 crop/resize、摄像头推理循环、实时结果叠加及整机 FPS 尚未接通/验收。请按以下格式记录结果，便于下一步定位：

```text
版本：v0.5-ti60-debug-r1
JTAG .bit 下载：成功 / 报错全文
未加载 ELF 时：HDMI、图像处理、原串口控制表现
OpenOCD：TAP ID / CPU halt / 报错全文
ELF 加载与运行：是否到 cnn_debug_done
cnn_debug_status：完整输出
运行 ELF 时：HDMI 有无新增闪屏/花屏/停顿
```

## 与官方流程的对应

已按本地《EVSOC_tinyml 用户手册》§3.4 使用官方 TinyML 参数生成器、模型数组、YOLO demo 派生 `main.cc` 和官方库，并先生成 Sapphire BSP 再构建软件。硬件使用 Efinity 2026.1 的 `efx_run.bat Ti60_AR0135.xml --flow pgm` 从本候选 LBF/LPF 生成 `.bit/.hex`。调试采用《Edge Vision SoC User Guide v7.0》第 18–23 页的先配置 FPGA、再用 OpenOCD 加载应用的流程。本定制板的调试器 USB ID、DDR3 地址隔离与串口接法已按实际工程适配，不能照搬官方开发板的终端日志预期。
