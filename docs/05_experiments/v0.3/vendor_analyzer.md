# 本地厂商分析器原始输出

探测并行度 1/1；不代表选定 FPGA 配置。冒号后的数字不作为算子版本解释。

```text
input type: 9, shape: 1x64x64x1
output(0) size: 2, type: 9, shape: 1x3
CONV_2D:3

MAX_POOL_2D:3

CONV_2D:3

MAX_POOL_2D:3

CONV_2D:3

MAX_POOL_2D:3

AVERAGE_POOL_2D:3

RESHAPE:3

FULLY_CONNECTED:3

=======================

conv_depthw_mode:1

conv_depthw_std_out_ch_fifo_a:64

conv_depthw_std_filter_fifo_a:288

conv_depthw_std_cnt_dth:64

add_mode:0

mul_mode:0

min_max_mode:0

fc_mode:1

fc_max_in_node:1024

fc_max_out_node:3

tinyml_cache:1

=========================


```
