# 2026-10-05 用户暂停恢复点

**该暂停已由用户后续“继续”撤销。最新状态见[已完成的r4资源与参考验证](../05_experiments/v0.5/resource_r4.md)。以下是暂停时的历史快照，不代表当前状态。**

用户明确要求暂停；恢复前不要继续编译、上板或提交推送。

- 当前目标仍未完成。原 fpga-w.-codex 不可修改。
- FPGA 副本 artifacts/evsoc-4x4-fc-lite-map：官方 Generator 4x4 Conv + FC LITE；map/interface/pnr 退出0。XLR59801/60800，RAM244，DSP65；clk_sys setup +0.171ns，JTAG跨域 -0.403/-1.307ns，未时序签核。pgm已启动，恢复时先检查 pgm.exitcode，勿重复启动。
- artifacts/evsoc-4x4-fc-disable-map：4x4 Conv + FC DISABLE；map/interface/pnr 退出0。XLR58819，RAM240，DSP57；clk_sys setup +0.157ns，JTAG跨域 -0.290/-1.297ns。尚未启动pgm，尚未上板。
- 两组 Generator 原始报告在教程 artifacts/official-4x4-fc-lite 与 official-4x4-fc-disable；模型数组逐字节一致。教程 scripts/generate_official_tinyml.py 新增 --fc-mode（parse_model后设置），未提交。
- r3基线 XLR57739，TinyML27425、CPU9496；Standard FC4029.5，Lite FC947。资源方案已证明4x4能容纳；新方案耗时和数值未验证。
- 本次复测 r3.1 启动脚本：旧OpenOCD接受GDB但3分钟无初始响应，已结束本次GDB PID43336并重启原OpenOCD PID44180。新服务 PID41504 扫描全1，无法读器件ID，初始化失败；日志在 deliverables/v0.5-ti60-debug-r3.1/openocd-retest.*.log。已异步询问板卡当前连接状态，未获答。
- tools/package_evsoc_debug_r3.py 和 docs/CNN_ELF_RUN_R3_1.md 未提交：分离stdout/stderr，增加下载180秒/运行60秒超时；未完成三向量时不再误报已完成。源码最后修改后尚未重新生成/验证r3.1包；现有zip/extracted入口是旧候选，不可宣称已同步最新修正。文档已撤销r3.1板上复测成功的误导性表述。
- FPGA outflow/Ti60_AR0135.tcl.out 原已有改动，保留。未提交、未推送、未合并。下一步应先检查后台进程和产物，再归档资源报告、校验脚本/包、根据连接状态进行同ELF同输入板上比较，然后同步现有Draft PR。
- 用户暂停；阶段6仍未验收，15FPS及动态采集/推理/Overlay未完成。
