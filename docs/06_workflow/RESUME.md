# 恢复工作记录

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
