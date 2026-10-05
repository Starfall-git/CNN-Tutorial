# 阶段 6：DMI 调试链路定位

日期：2026-10-05。用户确认 JTAG `.bit` 下载后，HDMI 是随场景变化的实时摄像头画面，COM8 原上位机能连接。OpenOCD 识别 `0x10660a79` 后仍发生 DMI 2秒超时，尚未成功 examine/halt CPU；尚不能运行 GDB 加载应用。

已核对实际生成的 Sapphire、USER1 顶层连线及官方 BSP 参数，与官方 YOLO demo 的硬 JTAG 隧道形式相符。实时视频是原视频链路工作的证据，不能替代 SoC 复位及调试域信号观测。此前的 SPI 桥接怀疑不再作为当前故障的首要解释。

下一次实验使用独立副本 `CNN-Tutorial-FPGA/tools/diagnose_evsoc_jtag.ps1`，默认100 kHz，保留官方 init/halt、原2秒超时并记录详细日志。脚本不更改原 release、硬件与 ELF，不写 Flash；运行时可能暂停 CPU。完整操作及证据见 FPGA 副本 `docs/CNN_JTAG_DIAGNOSTICS.md`。100 kHz 能否连接仍待板上实测，不据此认定跨时钟域违例无害。

本次交付的是诊断工具与源码审计，未完成阶段6；下一验收点是 OpenOCD 成功 examine/halt CPU，然后才是 ELF 下载及三组 INT8 自检。
