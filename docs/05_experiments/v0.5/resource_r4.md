# r4：恢复4×4卷积、验证参考后端

2026-10-05，阶段6子步骤完成：三组静态INT8输出与独立参考后端逐字节一致，4×4候选实际加速约2.45倍。动态摄像头采集、推理和Overlay尚未完成，阶段6不勾选。

## 资源和板端耗时

XLR是整套设计的逻辑资源。r3总57739，其中TinyML27425，Sapphire CPU9496，DDR、视频和控制等还占用其他资源。官方Generator按模型已经禁用ADD/LR/MUL/MIN_MAX；本次保留Conv STANDARD、缓存和Reshape，调整FC。

|配置|XLR/60800|RAM10|DSP|三次Invoke平均ms|静态推理次数/秒|
|---|---:|---:|---:|---:|---:|
|2×2 + FC Standard|57739|233|53|173.640|5.76|
|4×4 + FC Lite|59801|244|65|70.673|14.15|
|4×4 + FC Disable|58819|240|57|70.905|14.10|

同一模型、同一旧ELF、同一输入，在三组硬件上比较。FC Standard约4030 XLR，Lite约947；FC计算仅1024×3乘加，软件回退实测成本很小，因此选择4×4+FC Disable为动态链路候选，留下1981 XLR。没有删减原视频功能。14.1仅为Invoke吞吐，不包含采集/预处理/Overlay；15FPS的预算约66.7ms，尚未达到。

map/interface/pnr/pgm均通过。4×4+FC Disable的96MHz系统域setup裕量+0.157ns，JTAG跨域仍有-0.290/-1.297ns，未完成时序签核。

## 原来的±1为何存在

`scripts/audit_int8_backends.py`在TensorFlow2.15.1用冻结的372张评估集独立比较三个后端，输入量化沿用原函数。模型SHA256保持`7891518a9b70ec6b3be8649123651780ce87ede1e69a9a49c394c17d203a0baa`。

- 默认XNNPACK后端完整复现v0.3的全部输出。
- BUILTIN_REF与原输出有46个元素相差1；无默认delegate的builtin模式有45个元素相差1。
- 三个后端全部类别一致，准确率均95.43%。后两个模式并非全部372张逐字节相同，须明确基准后端。
- 三组golden输入在参考后端输出`[11,0,-2]`、`[-1,78,-60]`、`[1,-74,63]`，与三个板端硬件候选输出完全一致。

这是后端数值差异的直接复现，尚未定位到具体算子内部舍入实现。原XNNPACK golden保持不变；新增参考基准放在`artifacts/v0.5-backend-audit`。FPGA派生验证应用只更新期望输出，保留输入、模型、runtime和严格比较。重新构建、下载及回读后，板端返回`CNN_RESULT 1195655729 9 0 3 3`，三组严格通过。不能把桌面372张评估当成372张板上验证。

原ELF SHA256：`694ff2a91c8a9f9811fb32af5479da1799ad969c633c587e5c9d4fba0132ff47`。参考验证ELF：`c68c53488bd0eca63a314551d9602e155d8035a05f381003264abbd1f296e74f`。4×4+FC Disable bit：`828fc3ec402ee481f4000670ed6ae44402f229526c5ba8d5dc48941e7d2695e1`。

## 复现入口与后续

参考基准脚本在`CNN-Tutorial-Quant`环境运行。官方Generator使用Efinity `bin/python3.bat`，新增`--fc-mode LITE`或`DISABLE`，模型C数组逐字节校验保持开启。

独立FPGA副本的工程入口：`C:/Users/SteLl1a/Desktop/CNN-Tutorial-FPGA/artifacts/evsoc-4x4-fc-disable-map/Ti60_AR0135.xml`。r4包：同仓库`deliverables/v0.5-ti60-debug-r4`。`start-openocd.ps1`建立调试服务后，用`start-gdb.ps1`下载、验证及运行；正常GDB stderr单独记录，实际失败仍停止。

证据见本目录的`resource_r4_backend.json`、`resource_r4_reference.json`，更完整资源/板端证据与调试包在[FPGA PR #20](https://github.com/Starfall-git/fpga-w.-codex/pull/20)。本轮先恢复JTAG器件扫描，再重新下载r3配置恢复CPU，随后测试两组候选，均仅使用易失性JTAG配置，没有写Flash。

下一步实现原始灰度64×64 ROI快照、APB读入、官方TinyML循环和结果发布，保持视频链路独立；需要追加CDC/帧一致性仿真、资源/时序检查及动态上板验证。当前host不显示实时推理就绪是预期，静态固件不伪造firmware_ready。
