# 恢复工作记录

额度已恢复；2026-10-05 本轮最近查询短时已用50%、周已用39%，后续接近99%按用户要求保存暂停。当前无活动本地编译；恢复时重新查询实际额度。

## 2026-10-05 最新：调试包已生成，上位机入口补齐，等待业务bit与板上运行确认

本轮官方PGM PASS，artifacts/evsoc-system-r1/outflow/Ti60_AR0135.bit 已生成。固定发布包在 FPGA副本 deliverables/v0.5-ti60-debug-r1.zip，解压在 artifacts/releases/v0.5-ti60-debug-r1。SHA见docs/05_experiments/v0.5/debug_release_report.json，48文件哈希和zip内容校验PASS。新增tools/package_evsoc_debug.py拒绝覆盖既有发布；当前map/res/timing报告与历史top_integration_report文件哈希不同，已重新读取实际报告确认相同资源/17条setup与17条hold关系、仅两条JTAG跨域负裕量，manifest记录本次审核与当前文件hash，未伪称历史报告逐字节匹配。

ELF增加cnn_debug_status和cnn_debug_done断点，官方make成功，ELF SHA694ff2a91c8a9f9811fb32af5479da1799ad969c633c587e5c9d4fba0132ff47。D-cache状态发布沿用官方0x500f指令，仍是静态3样本，不设置firmware_ready。旧ELF在候选history/static-before-debug。包内脚本只准备未执行，未由agent下载/擦Flash/启动OpenOCD。GDB离线符号检查通过，有本机编码警告但符号可读。

用户报告自己编译并下载后host无法连接，截图明确为SPI Active using JTAG Bridge + hex，控制台只显示到擦除Flash。Windows端口开始为空，后枚举CH340 COM8；agent只读查询确认COM8可打开但GET_STATUS超时。已告知等Flash操作完成后选JTAG + 业务bit，不能把桥接镜像运行当作业务设计运行。Build只生成ELF，还需OpenOCD加载并Resume；纯FPGA UART无需ELF应能握手。不要继续说串口未枚举，不要误报已恢复连接或推理成功。用户尚未反馈重新配置bit后的结果。

host新增“图像→TinyML 手势”入口/独立面板，支持请求与实际状态、未就绪禁用推理、旧固件能力门控、通信失败不虚报成功。旧GUI须重启加载更新。连接错误区分COM打不开与握手超时。4项新GUI+5CNN+14原host+8camera+2advanced=33项分套件PASS。最初混跑有Tk GC线程问题，新GUI测试tearDown在主线程清理后单套件PASS；旧混跑session24914已exit1，不能再当活动会话。

下一步先确认业务bit实际运行下的UART/HDMI，再使用包内官方OpenOCD/GDB启动脚本加载ELF运行三组静态推理，收集cnn_debug_status/PC/异常寄存器。同时尚需RAW8 crop/resize、实时摄像头固件循环、720p压力及JTAG CDC审计。原fpga-w.-codex严格只读，副本outflow/Ti60_AR0135.tcl.out用户改动保留，阶段6/7未完成。用户偏好简单任务用6-sol，实际模型选择需遵循当前会话能力，不能虚称已切换。

教程原ee84e46 CI run37261177254成功，本轮新提交CI需按新SHA确认。

## 2026-10-05 最新：真实顶层综合通过，2×2 PNR通过但时序未签核

原视频根目录example_top保留；tools/integrate_evsoc_top.py在artifacts/evsoc-system-r1生成真实顶层，接CPU/TinyML/shared DDR、UART/Overlay、官方USER1 JTAG。配置config/cnn为官方2×2生成，4×4 XLR63390、2×4 XLR61392均超60800；2×2为57695容量通过，LUT35399/FF26944/DSP53/RAM233。map和interface均PASS，PNR session49440已exit0/PASS，161秒，无活动本地编译。最差setup为JTAG→clk_sys -1.307ns，反向-0.384ns；需审计官方JTAG CDC/时钟约束，未签核，不能直接上板。map75172、软件9027均已exit0。SDC有优化掉的端口对象告警，最终时序尚未签核。原source.f必须全登记，RS_MODE/RESHAPE_MODE需同值别名。

新DDR3 BSP软件make通过（7a1f8384 ELF），不再用旧HyperRAM BSP；PIO旧DMA条件编译，官方PLIC A初始化已调用。静态自检不设置固件ready。APB0x28写47535452就绪/0清除，真实SoC要求就绪；APB/UART/reset三测试PASS。无板卡下载。下一步PNR报告、SDC审计/资源余量、720p/FIFO压力与RAW8预处理/软件循环。最新详细top_integration.md和报告；原工程只读，用户outflow修改保留。


## 2026-10-05 最新：官方转换器响应修复与SoC内存封装

新增cnn_axi_full_to_half_duplex.v（官方MIT源码仅加BRESP传递及重命名）、cnn_evsoc_memory.v（真实SoC/转换器/shared DDR实例）。两项新仿真PASS：转换器协议与转换器+共享DDR组合，CPU256拍abort、TinyML R停顿、350次视频读取、越界写DECERR不丢失。封装仅语法编译PASS，尚未接example_top。详细docs/05_experiments/v0.5/evsoc_memory.md/report.json。

下一步直接使用cnn_evsoc_memory接现有video AWARMux后端口和DdrCtrl唯一输入，父层须处理AI复位等待ai_quiescent、JTAG/SPI/UART、IP/XML/SDC。不能把当前封装当完整顶层；无综合/板上结果。生成器会覆盖派生封装，人工改动前先保存。原fpga-w.-codex只读，副本outflow用户改动保留。教程023606c CI37228805738已success，新提交CI另查。无本地运行中工具、无下载板卡，阶段6/7未完成。额度接近上限时保存并停止，恢复时先查询实际额度。


## 2026-10-05 最新：共享DDR事务层组合验证已通过

FPGA最新3d10d636已推送Draft20。新增cnn_axi_transaction_buffer、cnn_axi_isolated_port、cnn_ddr_arbiter、cnn_shared_ddr及4个runner/testbench。AI先完整缓存写突发、为读预留完整空间；独立ai_abort取消未发出事务、排空已发出事务，窗口/缓存/仲裁都不能接CPU独立复位。三路端口0视频物理地址，1/2为CPU/TinyML逻辑窗口。

四项ModelSim仿真通过，包含256拍缓冲、隔离窗口、12事务轮询、CPU写中abort与TinyML不接读结果时的共享通路。组合测试347次视频读取继续完成（不是帧数/FPS）。证据docs/05_experiments/v0.5/shared_ddr_report.json。共享测试初版negedge TB ready竞争，改posedge采握手后通过，RTL未改来迎合测试。无活动仿真/编译，无下载板卡。

下一步实际top：将cpu raw combined和TinyML full AXI接入这两路，视频现有AWARMux后接端口0，DdrCtrl唯一驱动接共享输出。官方axi_full_to_half_duplex.v的s_axi_bresp固定0，不能直接使用，否则吞掉窗口DECERR；应保留许可的小改版或正确适配并测试。然后接cnn_soc_subsystem、AI排空复位、JTAG/SPI/UART与IP依赖，走Efinity综合。官方加密IP ModelSim仍不支持，不造假模型代替。

完整720p真实reader/writer/FIFO压力、BRAM推断/资源、时序/布局布线、RAW8预处理和软件循环/板上验证仍待完成。原fpga-w.-codex只读，副本用户outflow改动保留。阶段6/7保持未完成。


## 2026-10-05 最新：额度已恢复，SoC外层与AI内存窗口已提交

FPGA最新8bbc931e（Draft20），新增cnn_soc_subsystem.v：实际Sapphire78端口和TinyML35个AXI端口完整连接，自定义指令/中断/APB1端点有真实实例代码；尚未接example_top。生成器由实际公开声明生成，用户编辑后拒绝覆盖。新cnn_axi_window.v进行[0x1000,0x04001000)→[0x04000000,0x08000000)受限转换，非法全突发DECERR，无DDR访问。窗口数字仿真与外层语法编译PASS。

重要：完整官方Sapphire/TinyML的ModelSim编译失败（加密保护区域语法错误exit2），不是完整SoC仿真通过；后续通过Efinity官方综合验证，不换假IP冒充。证据docs/05_experiments/v0.5/subsystem_report.json。没有运行中的工具任务，未下载板卡。

下一步实际集成：CPU/加速器两路统一地址窗口，完整写突发/读响应缓存、有界DDR仲裁、ID回传和AI复位排空；随后接example_top、Sapphire/TinyML和端点、注册官方依赖并做Efinity综合。窗口单独复位不能丢在途DDR事务；窗口本身不保证AI停顿不影响视频。SoC调试UART与现有命令UART不得并驱动TX，需决定调试通道或复用。

本轮开始额度短时1%、周0%（均为已用）已恢复；继续工作中，不沿用旧额度100%停止状态。教程PR7最新状态需按最新提交检查。原fpga-w.-codex只读，副本用户outflow改动保留。阶段6/7仍未完成。


## 2026-10-05 最新：真实视频工程96MHz Sapphire生成成功，额度保存

FPGA提交06b1b668已推送Draft #20。候选目录 artifacts/evsoc-system-r1 从独立副本的实际视频顶层/XML/peri/DDR IP准备，官方source保持原内容。已确认 example_top 的 w_ddr3_ui_clk=clk_sys=96MHz，不是DDR物理时钟。官方IPM API生成Sapphire成功、exit0，session87651已结束，无需等待或重启。RTL/模板/匹配BSP及日志哈希见 docs/05_experiments/v0.5/sapphire_system_generation.json。

配置：CPU/peripheral96MHz、128位combined DDR、APB0禁用/APB1启用，原自定义指令保留；DDR逻辑窗口64MiB。计划AI物理64–128MiB，保护低48MiB视频区，但地址转换尚未实现，不能直接下载当前软件或称为整机可运行。原DdrCtrl行列/物理时钟未改，候选XML只登记了Sapphire，example_top尚未实例化。

下一步必须核对模板与官方edge_vision_soc实例，实施Sapphire/TinyML子系统、CPU和加速器一致地址转换、受限DDR仲裁、ID返回及APB endpoint接线，再做RAW8预处理/坐标映射。不要再退回旧静态r3路线或重复生成同一IP。教程PR7上轮6c0e813 CI成功。此前任何“IP生成正在运行”已失效。

短时额度到95%时开始保存，继续前重新查询；用户要求接近1%剩余即暂停。原fpga-w.-codex只读，副本outflow/Ti60_AR0135.tcl.out用户修改保留。阶段6未完成，无新下载，无板上FPS/arena结果。


## 2026-10-05 最新：UART与结果/Overlay端点已组合验证

FPGA最新提交07597651已推送Draft #20。UART CNN_ENABLE默认为0，新50/51命令与cnn_video_endpoint在三时钟组合仿真通过；cpu推理开关和pixel叠加独立，ACK来自实际Overlay enabled寄存器。APB 0x24可读推理允许/online。主机SerialClient已有get_cnn/set_cnn，GUI按钮尚未做。29项host测试、123组几何数据包、旧UART/Overlay/APB回归通过；详见docs/05_experiments/v0.5/uart_endpoint.md与报告。

旧geometry fixture两处预期过时，旧HEAD也复现，已修正；两项旧runner输出迁移artifacts，运行产生的tracked历史work改动已恢复。FPGA唯一剩余非本轮改动仍是用户outflow/Ti60_AR0135.tcl.out。

教程 Draft PR #7 已附加到聊天，先前bb07dba的CI成功。本轮新推送后需看新SHA的CI。无运行中编译、无下载板卡，阶段6保持未完成。下一步要连接真实example_top与官方Sapphire实例、DDR仲裁和预处理，不能继续只报告模块准备完成。保持原项目只读。


## 2026-10-05 最新：PR #4 已合并，APB结果接口通过

教程 PR #4 已按用户授权合并，merge SHA 78997389db3a89efd93998f3f4c8e7abbb273d02（合并前CI成功）。教程当前分支 codex/evsoc-system-integration。阶段1–5用户勾选保留，当前推进阶段6。

FPGA 副本最新提交 59beb73d，已推送 Draft #20：APB影子寄存器原子提交、真实跨域邮箱协议仿真及官方RISC-V发布函数编译通过。证据 docs/05_experiments/v0.5/result_apb_report.json；实现说明在副本 docs/CNN_RESULT_APB.md。不存在活跃编译，尚未下载板卡。

下一步：真正连接Sapphire/APB结果与Overlay及UART控制，再解决共享DDR接口、RAW8预处理、几何映射和匹配BSP。不要把新增接口当成已接入顶层。不要重复训练/改名或重新跑不相关旧构建。仍保留副本 outflow/Ti60_AR0135.tcl.out 用户修改，原 fpga-w.-codex 只读。

此前“PR #4待合并/额度待恢复”均为历史记录；本轮额度短时已用17%、周81%，后续需重新查询，接近1%剩余按用户要求保存停止。


## 最新用户确认与额度保存

本轮读取 MAIN.md 实际用户改动：阶段2/3/4/5已由用户勾选，原样保留同步；阶段6/7未勾选。以后以此最新记录为准，旧文中的“阶段2/3待确认”“阶段5未完成”属于历史状态。后续工程任务属于阶段6的完整系统实现和上板验收，不能将checkbox解释为已有硬件/FPS实测。

短时额度已用95%时开始最后保存，继续前先查询恢复情况。当前无活跃编译：gesture全量make和Overlay仿真均已结束通过；最后推送主体为教程 cbe3e0a（CI run 37207875050 success）和 FPGA c1520434。用户确认同步后的最新SHA需重新检查CI，并按已有授权处理教程PR #4合并；FPGA Draft #20仍未完成完整硬件集成，保持明确状态。恢复后无需重复训练、生成或编译已经验证的同一产物。

## 最新接续：gesture 命名与 Overlay 模块

- 用户要求应用改名 `evsoc_tinyml_gesture`，已更新独立副本应用目录、`.project/.cproject`、Makefile PROJ_NAME、准备/适配/构建脚本及 manifest。官方参考源仍保持 ypd 原名。新 ELF SHA `371cd1ac4118e7bbd85356fd596901c19d9b07675b8c1365c9bb4b0e6a205113`，官方 Makefile 全量编译 exit 0；旧对象移至副本 `legacy_ypd_build` 保存。
- FPGA 新增 `src/cnn/cnn_result_mailbox.v`、`cnn_video_overlay.v`、`cnn_overlay_bridge.v`，测试 `tools/run_cnn_overlay_sim.py`：9帧16×12（1,728像素），异步传递、忙时保护、源/目标复位、帧边界开关、过期和三类字形/颜色均 PASS。说明在 FPGA `docs/CNN_OVERLAY.md`。
- 当前未接入 example_top.v/UART/APB；不要把小尺寸模块仿真称为整链路或物理CDC通过。下一步加结果寄存器与UART控制桥、ROI显示坐标映射，并将桥接模块接到ISP输出；仍需共享DDR仲裁、Sapphire/TinyML顶层、RAW8预处理及匹配BSP。
- 当前顶层 DDR 控制器是合并地址接口，`AXI4_AWARMux` 合并视频 AW/AR，现有 size 固定为4（128位）；SoC/加速器接入必须核对尺寸/突发转换，不能套用旧静态工程完整AXI4接口而不做适配。

## 最新用户方向与接续点：官方 YOLO EVSoC 双链路

2026-10-04 用户恢复执行，明确采用官方 `Ti60F225_yolo_person_detect_demo` 的 main.cc/edge_vision_soc.v 作为 AI 基线，与原 example_top.v 视频链路集成。详见 `docs/04_deployment/evsoc_dual_pipeline.md`；不要回退成只交付独立静态软件的路线。

- 已读取 TinyML 用户手册 3.4 并渲染关键页。用户共享聊天链接未返回正文，未核对其中额外信息。
- 原静态 r3 编译已结束：map/interface PASS，PNR FAIL（`jtag_inst2_TDI` 缺失）。无活跃编译需等待，也未下载板卡。
- 官方 2026.1 生成器实际生成模型参数：`artifacts/v0.5-official-generator-r2`；模型数组逐字节一致。桌面 tools 生成器是旧格式，而桌面 YOLO main/top 与固定 2026.1 正文相同。不要混用旧 define.cc 和新版 accel_settings.cc。
- FPGA 独立副本 `artifacts/evsoc-gesture-r1` 已复制用户官方 demo，并保留原文件快照。静态 main 派生自官方源文件、使用生成的 gesture 模型，官方 Makefile/SDK 编译链接成功。ELF SHA `b7889b9da8efb41862dd6faacde94fb8331f9b4e14ef60e9f30efd3900f67b5f`。
- 复现脚本：教程仓库 `scripts/generate_official_tinyml.py`；FPGA 副本 `tools/prepare_evsoc_gesture.py`、`adapt_evsoc_static.py`、`build_evsoc_application.py`，主函数片段 `firmware/evsoc_gesture/static_main.inc`。结果汇总在 `docs/05_experiments/v0.5`。
- 当前 copied BSP 仍是官方 HyperRAM 版本，应用编译成功不代表 DDR3 板上可运行。下一步必须实现双链路顶层、同一 DDR 控制器下的地址分区/仲裁、RAW8 预处理、UART 控制、帧边界 Overlay，并重新生成匹配 BSP。
- 软件静态验证仅为中间步骤，不能取代最终双链路。原视频 example_top 无关逻辑不改，AI 忙只丢 AI 输入，禁止拖停摄像头/HDMI；当前模型输出类别而非 YOLO 框。
- 保留副本用户修改 `outflow/Ti60_AR0135.tcl.out`，禁止修改原 `fpga-w.-codex`；MAIN 阶段勾选由用户确认。

## 最新：r3 IP 生成完成，硬件编译正在运行

2026-10-04 本轮已实际完成独立 r3 的 Sapphire RTL/BSP 生成（exit 0），不是板上验收。FPGA 工具提交 `3a6519e5` 已推送现有分支 / PR #20。

- 目录：`C:/Users/SteLl1a/Desktop/CNN-Tutorial-FPGA/artifacts/hardware-static-r3`。
- 修复：完整 AXI4，关闭未连接 APBSlave1，连接 CPU BRESP，未用 SPI 输入和 userInterruptB 置零；FT232H 配置独立保存为 `openocd/cnn_ft232h_ti.cfg`，0403:6014/channel 0。所有生成脚本语法检查通过；r3 实际生成和适配成功。
- 硬件完整 Compile 已启动：终端 session `17895`；最近确认 `efx_map.exe` PID `33828`、控制 Python PID `25784` 活跃。先查询该 session / 进程及 `compile.log`、`outflow/`。结束时 wrapper 会写 `compile.exitcode`。不能仅因日志暂空而重启，也不能把 r3 当作通过或可下载。
- IP 参数及调试配置摘要归档 `docs/05_experiments/v0.4/ip_generation/`。新生成 BSP 固件的成功报告仍对应 r2：`artifacts/cnn-static-generated-bsp-r1/build_report.json`。r3 BSP 后续需重新编译固件。
- 待办：核对所有 IP/综合诊断、布局布线与时序、引脚和 DDR 参数；通过后才下载本板候选 bitstream，然后完成 UART/DDR/三组 INT8 golden 分层验证。还没有板上 golden、arena 或 FPS 数据。
- 本轮开始保存时短时额度已用 91%。继续前先查询额度；不购买或使用重置权益。原 FPGA 工程不修改，副本用户 outflow 改动保留。

## 2026-10-04 最新接续点：用户要求 Astra / Medium

用户要求后续使用 GPT-6 Astra、中等推理强度。当前工具没有直接切换本对话模型的接口；不能声称已经切换。工程未完成，下一轮从以下状态继续，不重复训练或生成已验证产物。

- 阶段 5：独立静态工程准备中，尚未完成板上推理。已生成 `CNN-Tutorial-FPGA/artifacts/hardware-static-r2` 的 Sapphire 3.4.0 RTL/BSP，完整 AXI4、100 MHz、C4。r1 是合并地址通道的历史探测，不用于硬件编译。
- 新 BSP 固件构建在 FPGA 副本 `artifacts/cnn-static-generated-bsp-r1` 成功，108 编译单元；ELF SHA-256 `2c52655d4b4ad169f6ca141f70e7dfa71961ff21da47dcf503f3d304f0a9cb0c`。仅证明编译链接，不代表上板通过。
- JTAG 已读到 1 颗 Ti60，IDCODE `0x10660a79`；链文件在 `artifacts/hardware-static-r1/detected_chain.jcf`。FTDI `ftdi://0x0403:0x6014:2:1b/1`（重新连接后可能变化）。没有下载 bitstream/ELF，没有写 Flash，没有打开 UART。
- 下一步审核 `tools/prepare_cnn_hardware.py`：官方配置 APBSlave1 启用但旧 DDR3 wrapper 未接，考虑显式禁用后生成 r3；核对 DDR BRESP 输入连接、TAP_COUNT 和 DEVKIT_CUSTOM 调试参数。soft JTAG 未启用，不能把条件编译分支误报为接口缺失。新 BSP 未找到旧版 config 目录，教程应按实际目录修订。
- 新增未提交：FPGA 副本 `tools/prepare_cnn_hardware.py`、`tools/generate_cnn_sapphire.py`；教程仓库 `docs/04_deployment/efinity_to_riscv_workflow.md`。整理验证证据后提交、推送并更新现有 PR #4 / FPGA PR #20。
- FPGA 副本 `outflow/Ti60_AR0135.tcl.out` 是用户工具产生的改动，保留，不纳入本次提交。用户另有桌面 tinyml-main 官方工程的 Efinity 编译，勿停止它。
- 工具路径已经改为下划线：`C:/Users/SteLl1a/Desktop/Work/FPGA_Contest/env/Efinity_IDE/2026.1` 和同级 `RISCV-IDE`；旧 DDR3 参考在 `FPGA_Contest/demo/tinyml-main/tinyml_hello_world/Ti60F225_tinyml_helloworld`。历史报告路径不回写；新文档和 notebook 运行入口应更新。
- 本次接续前用量读取：5 小时额度已用 73%，周额度已用 58%。继续前重新查询，按用户要求接近 1% 剩余额度时保存停止。

2026-10-04：用户恢复执行后额度已恢复，阶段 4 的桌面量化验证已完成。后续交付继续明确阶段编号，接近额度阈值先保存再停止。

## 已完成并合并

- 阶段 1：用户在 MAIN 勾选，PR #1 已合并。
- 阶段 2/3：训练验证与一次分组优化技术工作完成，用户授权完成当前工作后合并，PR #2 已合并。MAIN 阶段 2/3 的勾选仍由用户确认。
- 远端 main 为 `0172385c5de67b6044e5fcd5f22a341aafafad0a`，两个 PR 的 CI 均通过。
- 最终模型：26,371 参数、10,030,080 MACs；公开回顾性基准 accuracy 95.70%，macro-F1 0.9563，paper recall 87.10%。真实相机和背景拒识未验证。
- 权重：`artifacts/v0.2-grouped-study/refit/best.pt`，SHA-256 `ed3e422f75b1765953cddc91fd49ab0f140e43f5c2c72e2a69785930365972ad`。

## 阶段 4 本轮完成

- 阶段 4 工作分支为 `feat/v0.3-int8-export`，该 PR 已合并；当前分支见文末 v0.4 记录。
- 独立环境 `CNN-Tutorial-Quant`：Python 3.11.16、TensorFlow 2.15.1、NumPy 1.26.4 已安装，`pip check` 通过。原训练环境保持 PyTorch CUDA。
- `scripts/prepare_conversion.py` 已实际运行，生成 `artifacts/v0.3-conversion-input/`。
- `weights.npz` 是冻结权重；`calibration.npz` 为训练池中每类 100 张，共 300 张；`evaluation.npz` 为 372 张官方测试图、标签与 PyTorch logits。校准/评估内容哈希不交叉。
- manifest 保存上述文件与模型摘要。转换输入不得混用其他 checkpoint。
- `scripts/convert_int8.py` 已实际执行：FP32 最大误差 1.049e-5，类别完全一致；INT8 accuracy 95.43%，下降 0.2688 个百分点，macro-F1 0.9535，33,240 字节。
- `artifacts/v0.3-int8/gesture_int8.tflite` SHA-256：`7891518a9b70ec6b3be8649123651780ce87ede1e69a9a49c394c17d203a0baa`。
- FlatBuffer 审计：14 个 INT8、5 个 INT32 张量，无 float/custom ops。三组 golden 向量已独立逐字节回放通过。
- 随 refs 提供的厂商 `tflite.exe` 返回 0，识别 Conv/FC；1/1 仅为分析探测参数，没有生成硬件配置，没有板端验证。
- Notebook 04 已在真实 Jupyter kernel 执行。报告、算子审计、哈希与环境快照归档于 `docs/05_experiments/v0.3/`，二进制留在本地 artifacts。

## 恢复后的顺序

1. 先检查账号用量；用户要求额度恢复再继续，不购买额外额度、不消耗重置权益。
2. 核对 git 状态、当前分支、PR 和本地 artifacts；不要重复下载数据或重训已经冻结的模型。
3. 核对新 PR #4 的最新提交、CI 和阶段确认（PR #3 已合并）。按用户约定处理确认后的合并，不自行勾选阶段。
4. 阶段 5 已收到工程：用户禁止修改 `C:/Users/SteLl1a/Desktop/fpga-w.-codex`。已从远端新克隆到 `C:/Users/SteLl1a/Desktop/CNN-Tutorial-FPGA`，基线 `51f7e55f8ce8614f2801f93e5af9bd7bc2c91c01`，分支 `feat/cnn-tinyml-bringup`。原目录未提交改动不复制、不触碰。
5. 先用 golden 输入对齐目标 runtime 的输出字节/argmax，测 arena，再接 64×64 灰度 ROI。相机数据位深、黑电平、resize 坐标和舍入需明确对齐。
6. 阶段 6 实测连续视频、HDMI 叠加与端到端 FPS；阶段 7 第二模型保持用户给出的后续顺序。整个目标尚未完成。

## 阶段 5 当前进度与恢复入口

- 工程确认 Ti60F225、C4、Efinity 2026.1.132.3.9；没有 Sapphire/TinyML。DDR 12×4MiB 槽占低 48MiB，新增内存必须避开并设计仲裁。
- FPGA 副本新增 `ar0135_capture.gray8` 与顶层 `cnn_raw_gray8`；尚无下游消费者。ModelSim 修改前后两帧 720p 回归通过，1,843,200 像素的 RAW8 和旧 RGB565 对齐；视频配置检查通过。
- 正常仿真工具 `D:/WORK/modelsim/win64`；Intel Edition 另一安装许可证失败，不再重试其许可证。
- `scripts/export_board_bundle.py` 已生成本地 `artifacts/v0.3-board-bundle/`。C++11 数据数组与原始模型/golden bytes 同包，哈希校验；新增往返/损坏拒绝测试，现共 10 项测试通过。目标 C++ 数据和静态固件交叉编译已完成，见下面的新进展。
- Efinity 路径 `C:/Users/SteLl1a/Desktop/Work/FPGA Contest/env/Efinity IDE/2026.1/bin`（用户确认）；未在此发现 RISC-V GCC/G++/Eclipse/OpenOCD，只有运行库 DLL，勿误称具备交叉工具链。
- 本地 DDR3 TinyML 示例位于 `C:/Users/SteLl1a/Desktop/Work/FPGA Contest/demo/tinyml-main/tinyml_hello_world/Ti60F225_tinyml_helloworld`，已有 Sapphire/BSP，版本 2025.1.110.1.5、I3。下一步先读其 RTL/BSP 与当前 DDR/IP 差异；只读参考，移植到新工作副本。
- 官方新版已固定克隆在 `refs/TinyML/upstream-2026.1`，commit `96886fa0c73e25e6218db7d0863f84677cf65138`；长路径 checkout 已通过 local core.longpaths 与 sparse checkout 修复，状态干净。不要重下全部源码。
- 详细记录 `docs/04_deployment/fpga_bringup.md`，FPGA 副本内为 `docs/CNN_TINYML_BRINGUP.md`。
- 前次曾在短期额度 9% 时保存；本轮已恢复。继续在接近 1% 前保存并停止，不消耗重置权益。

## 其他状态

- Code Review 插件仍返回无法连接 GitHub；GitHub 连接器可正常读写、查询 CI。不得声称插件审查通过。
- Jupyter 服务在本机 8889；已有 d2l 服务在 8888，保持不动。暂停前没有仍在运行的训练或依赖安装任务。
- Notebook 00 的 kernel 名称由 Jupyter 保存为小写 `cnn-tutorial`，已保留该变更。

## 2026-10-04 RISC-V 路径补充后的新进展

- 用户给出 `Work/FPGA Contest/env/RISCV-IDE`，GCC/G++ 实测 13.4.0；不再重复询问工具链位置。
- 实时核对发现 PR #3 已合并，远端 main `a3ac752fc7cc0d57220d714a4fd26acf572e9728`。先前补充提交 32c1423 在合并之后，故已从 main 建 `feat/v0.4-fpga-static` 并 cherry-pick 为 8e8e783，后续使用新 PR，不能再向已合并 PR #3 追加代码。
- FPGA 副本分支仍 `feat/cnn-tinyml-bringup`，Draft PR #20。新增 `firmware/cnn_static/main.cc` 与 `tools/build_cnn_static.py`。
- 当前成功构建在 FPGA 副本 `artifacts/cnn-static-2026-r5/`；模型哈希未变，108 units、ELF32 RV32IM/ilp32。报告和 ELF 属性在训练仓库 `docs/05_experiments/v0.4/`。
- 构建只读取本地旧 DDR3 BSP 和官方 2026 runtime，复制依赖后编译；源码逐文件哈希在本地 `input_hashes.json`。旧 runtime 头文件不完整，勿退回旧 runtime。
- 编译器的 C++ 标准库与 `-ffreestanding` 组合会失败，此构建使用正常 C++11 编译、厂商裸机启动和 nosys 链接。局部解释器对象避免静态析构注册引入缺失的 `__dso_handle`。
- UART 初始化与模型 SHA 日志已补齐；256 KiB arena 仅容量，2 MiB 默认栈不是模型大小。nosys/RWX 警告保留在报告。
- 三份用户 PDF 已读取并渲染关键页；解释在 `riscv_custom_instruction.md`，构建解释在 `riscv_static_firmware.md`，Notebook 05 提供报告回放。
- 下一步：匹配本板 C4、DDR3 和引脚的独立 Sapphire 硬件/BSP。当前 ELF 从 0x1000 开始，不能直接载入视频系统。先拿到静态 UART golden/arena/cycles，再进行 CI 加速和视频地址分区。没有烧写设备、没有硬件运行成绩。

- 已同步：CNN-Tutorial PR #4 https://github.com/Starfall-git/CNN-Tutorial/pull/4；FPGA Draft PR #20 固件提交 `1d7a905a00cf8e0c0403587f89d45e0e73d67df8`。Notebook 05 实际执行、10 项测试、格式/链接及视频配置检查通过。Code Review 本轮仍连接失败；CI 以新 PR 最新 SHA 为准。

- PR #4 提交 `74a53d726a4641463a206db1a8f45f349307e48c` 的 GitHub Actions run 37175072197 已成功。之后的文档补充须按最新 SHA 核对 CI。
- 阶段 5.4 已核对 UART/晶振 GPIO，并记录 C4/I3、96/300 MHz、DDR row=16/14 等差异；详见 hardware_preflight.md。未修改控制器参数。Win32_SerialPort 和按常见名称筛选的 PnP 查询未发现设备，已异步询问板卡连接状态，等待用户回答；未进行任何硬件下载。


## 本轮额度保存点

- 短时额度剩约 6% 时开始最后保存，按用户要求在耗尽前暂停，额度恢复后继续；不购买额度、不使用重置权益。
- 用户已明确确认板卡供电、JTAG 与 UART 连接。不要再询问是否连接。再次 PnP 枚举发现 FTDI COM7（0403:6014）与 CH340 COM8（1A86:7523），均 OK；端口角色待下载器配置核对。
- 最新完成的代码/文档主体提交 `37706db824c5845f4e29d1e47a27ba8d66338dde`，GitHub Actions run 37175295666 success；之后仅补充连接/保存状态。FPGA 分支干净，HEAD `1d7a905a00cf8e0c0403587f89d45e0e73d67df8`。
- 当前阶段 5.3 交叉编译完成，5.4 仅硬件预检查。后续先只读检查 Efinity `pgm/bin` 工具接口和下载器枚举，再在独立副本准备匹配 C4/DDR3 的 Sapphire 静态工程/BSP。已连接并不代表当前视频 bitstream 内含 Sapphire，不能直接运行当前 ELF。
- 所有训练、编译任务已退出，无待恢复的训练进程；模型/ELF/日志均已保存。Notebook 05 默认回放。整个目标未完成。
