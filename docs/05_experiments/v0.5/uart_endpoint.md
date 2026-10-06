# 阶段6：独立推理/叠加控制与视频端点

FPGA提交 `07597651`。在官方APB结果接口基础上，`cnn_video_endpoint` 将结果寄存器、跨域邮箱、Overlay连接为可供最终顶层实例化的单元。现有UART新增查询0x50、设置0x51，bit0控制是否启动新推理，bit1控制是否叠加。Overlay在帧边界实际改变后的状态返回UART，成功应答不提前冒充显示生效。

`SerialClient.get_cnn()` / `set_cnn(inference, overlay)` 已支持，先检查设备声明；旧固件不发送新命令。查询区分 requested/applied；500ms超时并不撤销请求，恢复帧同步后可能生效，需要查询或显式设置0。恢复默认同时等待两个开关实际清零。CPU离线不影响关闭推理或独立控制叠加，原视频链路没有AI反压。

## 证据

[组合回归报告](uart_endpoint_report.json) 保存源码与日志哈希；[更新后的APB/官方SDK编译报告](result_apb_control_report.json) 保存含0x24控制状态读取的接口验证。

| 检查 | 结果 |
| --- | --- |
| 物理UART、三异步时钟、实际Overlay ACK、独立控制、超时、默认恢复、CPU复位视频直通 | PASS，零错误/警告 |
| APB原子发布/邮箱、官方RISC-V函数编译 | PASS |
| Overlay原1728像素回归 | PASS，4条旧测试未接新状态输出的端口警告 |
| 原UART阈值/按键/ISP回归 | PASS，23条旧测试未连接可选端口警告 |
| 123组几何串口数据包与真实DDR reader配置确认 | PASS |
| 上位机协议、客户端、旧ISP/相机相关测试 | 29项PASS |

几何旧测试曾把能力DATA6写死0、将现在合法的Gaussian位当作非法值；修改前UART也复现失败。已按现有协议修正为DATA6=15、非法保留bit7，保留完整123组检查。两个旧runner输出改放artifacts，不再改写仓库历史仿真库。

## 边界与下一步

这是组合模块验证，尚未连接物理 example_top、Sapphire IP、真实AI在线条件，也没有增加GUI按钮或下载板卡。CNN_ENABLE默认0，旧顶层不会提前宣称支持新功能。

下一步应从官方edge_vision_soc/Sapphire实例出发，实现与example_top实际视频、时钟及DDR接口的顶层连接：独立AI复位、共享DDR受限仲裁及地址分区、RAW8预处理和显示坐标映射，然后生成匹配BSP、运行完整综合/布局布线和板上分层验证。阶段6仍未完成。
