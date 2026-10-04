# 阶段 5.3：构建 RISC-V 静态 INT8 验证固件

本子步骤完成的是 **ELF 交叉编译与构建审计**。模型执行、arena 实测和周期结果必须来自板端日志，不能用编译成功代替。

## 三组输入为何先于摄像头

模型、量化参数和输入 bytes 已在桌面冻结。先把同样的 bytes 放进 RISC-V 固件，可以把 runtime/算子差异与摄像头曝光、ROI、缩放差异分开定位。三组向量覆盖 paper、rock、scissors，预期 INT8 logits 分别是 `[11,0,-2]`、`[-1,79,-60]`、`[1,-75,63]`。这是一致性自检，不是新的精度测试集。

## 构建所需文件

| 输入 | 实际选择 |
|---|---|
| SDK | 用户提供 `Work/FPGA Contest/env/RISCV-IDE`；GCC/G++ 实测 13.4.0 |
| ISA / ABI | `rv32im_zicsr_zifencei` / `ilp32`，C++11 |
| BSP、启动文件、外设驱动 | 本地 DDR3 静态示例的 `sapphire_soc_tinyml` workspace，2025 年版本 |
| TFLite Micro、平台、TinyML 库 | 官方固定 2026.1 runtime 的 `SapphireSoc` workspace |
| 模型数据 | 本项目 `scripts/export_board_bundle.py` 的带哈希包 |
| 应用与构建脚本 | 独立 FPGA 副本内 `firmware/cnn_static/main.cc`、`tools/build_cnn_static.py` |

旧示例缺少部分 FlatBuffers/算子头文件，所以没有继续使用它的不完整 runtime。当前混合 BSP/runtime 仅通过编译链接检查；硬件 ABI、启动、UART、DDR 和算子运行兼容性仍待板端确认。

## 复现

先在 CNN-Tutorial 中运行 `python scripts/export_board_bundle.py`。然后在 **CNN-Tutorial-FPGA 副本**中执行下列命令；所有生成文件写到副本的 ignored `artifacts/`。输入目录只读。输出目录若存在，脚本拒绝覆盖，请换一个新名称。

```powershell
python tools/build_cnn_static.py `
  --vendor-workspace 'C:\Users\SteLl1a\Desktop\Work\FPGA Contest\demo\tinyml-main\tinyml_hello_world\Ti60F225_tinyml_helloworld\embedded_sw\sapphire_soc_tinyml' `
  --runtime-workspace 'C:\Users\SteLl1a\Desktop\CNN-Tutorial\refs\TinyML\upstream-2026.1\tinyml_hello_world\Ti60F225_tinyml_hello_world\embedded_sw\SapphireSoc' `
  --sdk 'C:\Users\SteLl1a\Desktop\Work\FPGA Contest\env\RISCV-IDE' `
  --bundle 'C:\Users\SteLl1a\Desktop\CNN-Tutorial\artifacts\v0.3-board-bundle' `
  --output artifacts/cnn-static-rebuild
```

Notebook [05](../../notebooks/05_riscv_static_bringup.ipynb) 默认读取真实归档报告，可选择重新构建；不会下载 bitstream 或打开 JTAG。

## 关键代码

`bsp_init()` 设置厂商 BSP 串口，随后输出模型 SHA-256。`MicroMutableOpResolver<5>` 只注册模型需要的五类算子。`AllocateTensors()` 后检查 input/output 的数量、维度、int8 类型、字节数和 scale/zero point，避免错用模型或布局。

arena 为 16 字节对齐的 256 KiB 全局数组，这是首次测试容量上限，**不是已测最小值**。解释器和 resolver 用局部对象，避免裸机启动缺少 C++ 动态卸载句柄引发链接失败。计时器以 high-low-high 的方式读取 64 位 cycle，避免低位溢出导致读数撕裂。

每次 `Invoke()` 后输出实际/预期 logits、最大字节差、类别和周期高低位。只在三组输出均逐字节一致时打印 `exact_vectors=3/3 PASS`，差一位仍报 `MISMATCH`。需要进一步用实际 UART 日志判定，不提前假定各版本量化舍入完全相同。

## 2026-10-04 实际构建结果

本地输出 `CNN-Tutorial-FPGA/artifacts/cnn-static-2026-r5/`，108 个翻译单元编译并链接成功。ELF32 little-endian RISC-V，入口 `0x1000`。模型仍为 33,240 字节，SHA-256 `7891518a9b70ec6b3be8649123651780ce87ede1e69a9a49c394c17d203a0baa`。

GNU size：text 92,992 字节，data 58,686 字节，bss 合计 2,359,928 字节。此处 size 的 bss 合计包含 linker 预留的 **2 MiB 栈**；实际 `.bss` 为 262,776 字节，其中含 256 KiB arena。不要把固件内存预留误报成模型参数大小或 arena 实测。

ELF SHA-256：`3d65ae1f03ec620c9cab6afa06ca81399e36242dd5bbd3fd930ae49d666ca0d4`。调试路径会影响 ELF 哈希，跨目录重建应比较模型/源文件哈希及构建参数，不要求 ELF 必然相同。

构建报告记录源码清单、脚本、模型、库和 linker 哈希，并保留 compile/link log、ELF header/attributes/sections。newlib nosys 的未实现 POSIX 系统调用和 RWX LOAD 段警告仍存在；UART 日志使用 BSP，尚未验证其他库路径的目标行为。没有把这些警告隐藏为“零警告构建”。小体积报告在 [v0.4 归档](../05_experiments/v0.4/build_report.json)。

下一步是建立与板卡匹配的独立 Sapphire 静态硬件工程，核对 C4/DDR3/引脚/时钟，再取得三组 golden 日志、arena 占用与周期。当前 ELF 的低地址布局冲突，**不可直接加载到现有视频系统**。CI 与缓存约束见 [接口说明](riscv_custom_instruction.md)。
