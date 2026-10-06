# 阶段 6：软件向视频链路发布手势结果

## 问题与实现

CPU一次识别会产生帧号、类别和ROI坐标。逐个寄存器写入不能让像素端立即使用，否则可能显示新类别与旧坐标的混合。FPGA 副本增加 `src/cnn/cnn_result_apb.v`：先写影子寄存器，再一次提交83位数据包给现有 `cnn_result_mailbox`，在视频帧边界接收。软件准备下一帧不会修改邮箱已锁定的数据。

接口采用官方 EVSoC Sapphire 的 APB 信号，以及官方 `io.h` 的 read_u32/write_u32。独立的 `firmware/evsoc_gesture/gesture_result.h` 提供单生产者发布函数，基址必须由最终BSP确认。没有向尚未匹配的BSP中硬编码寄存器地址，也没有修改官方相机寄存器语义。

## 实测证据

FPGA 提交 `59beb73d`，命令 `python tools/run_cnn_result_apb_sim.py`。ModelSim 仿真用真实异步邮箱，覆盖setup无副作用、忙时拒绝、原子快照、帧边界接收、非法地址/提交值、清除结果和复位，PASS、零错误/警告。RISC-V g++ 对实际发布函数调用方使用 -Wall -Werror 编译成功。

最初包含整个 bsp.h 时，严格警告检查触发了官方打印/半主机头文件的已有警告；将依赖缩小到函数实际使用的官方 io.h 后通过，无需修改官方库或关闭告警。

完整文件哈希、编译命令与日志哈希见 [机器报告](result_apb_report.json)。该报告的 hardware_verified 和 top_integrated 均为 false。

## 尚待实现

将结果接口连接到最终Sapphire地址空间及Overlay，接入独立UART推理/叠加开关和坐标变换。然后完成共用DDR控制器的仲裁、摄像头预处理、匹配IP/BSP生成、综合布局布线和板上验证。当前只是阶段6的一个完成子步骤，用户阶段6勾选保持未完成。
