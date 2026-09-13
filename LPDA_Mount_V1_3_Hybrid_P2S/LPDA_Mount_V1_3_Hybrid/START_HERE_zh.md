# LPDA V1.3 Hybrid — 先读这里

本版保留下托、下夹、方柱、锚固底座；四孔尼龙连接替代上夹。
18 个 PETG 件，不包含软垫。无旋转机构、无电子板托盘。

## 先做哪一步
先打印 plates/TINY_HOLE_PATTERN_ONLY.3mf：T01 仅核对四孔能否同时自然穿入。
然后打印 FIRST_FIT_CASSETTE_NOT_LOAD_TEST.3mf：一个真实 P07 + 3 个局部试块。
薄样片和试块不能单独承重，不要把整块天线悬挂到这些试块上。

## 两个已知的适配边界
21.66 / 26.60 mm 是最近孔边净距。实际孔径未测；当前假定3.00，中心距24.66×29.60。
孔窗口允许局部±0.8 mm（名义几何），不修改天线孔。
孔组中心必须同时落在：距后缘止挡24–44 mm、高于下承托面98–134 mm。
超出这个范围只改局部接口后再验证，不能抬起天线让下托悬空。

## 已有V1.2.1可少打印
只新打 FULL_02_UPPER.3mf 和 FULL_04_CASSETTES.3mf，共6件。
复用P02×2、P03×1、P04×1、P05×4、P06×4。P01不是旧上夹，不混装。
没有旧件：FULL_01…04各打印一板。合格首件可计入整机，删掉重复对象。

## 打印
Bambu Lab P2S，0.4mm喷嘴、普通PETG、0.20mm层高、5圈墙、30%填充为试打起点。
3MF只有模型与位置，没有G-code、机器配置、支撑或实际切片时间。
按层打印，不自动缩放。添加brim或支撑后重新检查热床与零件间距。
OPTIONAL_TPU内是软垫备选，不能用PETG替代。M3尼龙螺钉为购买件，不打印。

## 看整体
STEP/LPDA_V1_3_assembly.step 为18个打印件的实际装配位置。
STEP/LPDA_V1_3_hardware_assembly.step 另含名义五金与软垫。
visual_reference_NOT_MEASURED.step 内绿色PCB仅占位，不是实测天线。

## 文件
Assembly_Guide_V1_3_zh.html：顺序、姿态、兼容范围、复用与首件条件。
BOM_V1_3_zh.html：最新净数量；M4可参考Home Depot，M3全尼龙未确认该店库存。
Validation_V1_3_zh.html：实际执行的检查与未验证范围。
source/：CadQuery参数化代码，reference/v121/为复用几何依据。

本版名义几何检查通过；未实物打印、承载、蠕变或RF验证。先固定底座再装天线。
