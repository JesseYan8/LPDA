#!/usr/bin/env python3
"""Generate release documentation from the actual geometry/check manifests."""
from pathlib import Path
import json, html, hashlib, importlib.metadata
ROOT=Path(__file__).resolve().parents[1]
G=json.loads((ROOT/'validation/geometry.json').read_text())
A=json.loads((ROOT/'validation/audit.json').read_text())
S=json.loads((ROOT/'validation/assembly_stages.json').read_text())
P=json.loads((ROOT/'validation/plates.json').read_text())
VOL=sum(v['volume_mm3']*v['qty'] for v in G)/1000
SOURCES=[
 ('P2S 官方规格，打印范围','https://bambulab.com/en/p2s/specs'),
 ('Essentra M3×0.5×25 尼龙盘头螺钉，50M030050P025','https://www.essentracomponents.com/en-us/p/plastic-pan-head-screws/50m030050p025'),
 ('Home Depot：Hillman 3990，M4×20 盘头','https://www.homedepot.com/p/Hillman-M4-0-7-x-20-mm-Phillips-Pan-Head-Machine-Screws-15-Pack-3990/204794789'),
 ('Home Depot：Hillman 4156，M4×25 外六角；完整螺纹段待实物确认','https://www.homedepot.com/p/The-Hillman-Group-M4-0-70-x-25-mm-External-Hex-Hex-Head-Cap-Screw-25-Pack-4156/204794751'),
 ('Home Depot：Hillman 4044，M4 六角螺母','https://www.homedepot.com/p/Hillman-Stainless-Metric-Hex-Nut-M4-0-70-4044/204801217'),
 ('Home Depot：Hillman 4118，M4 平垫圈','https://www.homedepot.com/p/Hillman-Stainless-Steel-Metric-Flat-Washer-M4-Screw-Size-4118/204801237'),
 ('Home Depot：VELCRO 91141 窄尾软绑带','https://www.homedepot.com/p/VELCRO-8-in-x-1-4-in-One-Wrap-Ties-Black-25-Count-91141/203307537'),
 ('Essentra 塑料六角螺母系列；采购 M3-0.5，核对外形','https://www.essentracomponents.com/en-us/p/standard-hex-nuts-plastic'),
 ('Essentra SR1940 / DIN 9021 大外径垫圈系列；M3、OD9、0.8 mm，非美国库存声明','https://www.essentracomponents.co.th/en-th/fasteners-and-fixings/washers-spacers-and-bushes/sr1940-washers-din-9021'),
 ('Prusa PETG 材料指导：支架用途与桥接注意','https://help.prusa3d.com/article/petg_2059'),
 ('Toray 尼龙机械特性：载荷、温度与吸湿影响','https://www.plastics.toray/technical/amilan/tec_001.html')]
def esc(s):return html.escape(str(s))
def link(i):
 t,u=SOURCES[i];return '<a href="'+u+'">'+t+'</a>'
def table(head,rows):
 return '<table>\n<thead><tr>'+''.join('<th>'+str(x)+'</th>' for x in head)+'</tr></thead>\n<tbody>\n'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>\n' for row in rows)+'</tbody></table>\n'
CSS='''body{margin:0;background:#eef4f5;color:#163a46;font-family:system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.8}main{max-width:1060px;margin:26px auto;background:white;padding:36px 44px;border-radius:12px}h1{font-size:31px;line-height:1.35}h2{margin-top:32px;font-size:22px;border-bottom:2px solid #deebed;padding-bottom:6px}h3{font-size:18px}a{color:#087782}table{width:100%;border-collapse:collapse;font-size:14px;margin:16px 0}th,td{padding:9px 11px;border-bottom:1px solid #dbe8eb;vertical-align:top;text-align:left}th{background:#e7f0f2}img{max-width:100%;height:auto}figure{margin:22px 0}figcaption,.muted{font-size:13px;color:#59717c}.note,.warn{padding:15px 20px;border-left:5px solid #157d80;background:#edf8f7;margin:20px 0}.warn{border-color:#b68434;background:#fff5e4}code{background:#edf2f4;padding:2px 4px}pre{background:#edf2f4;padding:15px;overflow-x:auto}li{margin:9px 0}nav{display:flex;gap:16px;flex-wrap:wrap;font-size:14px}@media print{body{background:white}main{padding:0;margin:0;max-width:none}h2{break-after:avoid}tr,figure,.note,.warn{break-inside:avoid}a{color:inherit}}'''
def page(filename,title,body):
 text='<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>'+esc(title)+'</title>\n<style>'+CSS+'</style>\n</head>\n<body><main>\n<p class="muted">SPECTRUM_SENSING / LPDA MOUNT V1.3 HYBRID / 2026-09-12</p>\n<h1>'+title+'</h1>\n<nav><a href="Assembly_Guide_V1_3_zh.html">装配说明</a><a href="BOM_V1_3_zh.html">采购清单</a><a href="Validation_V1_3_zh.html">复核记录</a></nav>\n'+body+'\n</main></body></html>\n'
 (ROOT/filename).write_text(text,encoding='utf-8')
part_titles={'P01_upper_carrier':'上层四向承载半框（新）','P02_lower_half':'下层承托半框（沿用）','P03_fixed_mast':'固定方柱（沿用）','P04_anchor_base':'锚固底座（沿用）','P05_pressure_shoe':'下夹活动压块（沿用）','P06_M4_knob':'下夹防轴移旋钮（沿用）','P07_four_hole_cassette':'四孔安装板（新）'}
body='''
<div class="note"><strong>下托、下夹、中央固定骨架保留；四孔尼龙连接替代原上夹。</strong><br>18 个 PETG 打印件。V1.2.1 已有合格件可复用，只新增 2 个上半框和 4 个四孔安装板。不恢复转动机构、主夹距调节轨道或电子板托盘。</div>
<div class="warn"><strong>放行等级：名义几何通过，进入局部首件验证；不是已通过实物验证的量产图纸。</strong><br>天线真实孔径、孔组到板边的关系尚未实测。先核对薄孔位样片和一个实际安装板；不得为对孔把 PCB 提离下托、掰弯 PCB 或强迫螺钉入孔。</div>
<figure><img src="preview/LPDA_V1_3_overview.png"><figcaption>真实 CAD 渲染。绿色 PCB 和蓝色馈线为未实测的参考占位。预览姿态不等于 RF 性能或线缆最小弯曲半径已验证。</figcaption></figure>
<h2>1. 定位、承重、锁紧的分工</h2>
<p>下缘的局部承托唇接住 PCB，原下夹压块通过薄软垫保持板面贴靠。四孔安装板的四个共面支撑台，通过 16 套 M3 全尼龙紧固件固定四副 PCB。安装板再由两颗 M4 螺钉连接上框。不要先把上板拧死再用下夹把 PCB 拉到另一个平面。</p>
<p>下夹是保留的支承与辅助约束，不是新四孔连接的竞争定位器。4 个孔周接触面、下夹固定面以同一个板面基准设置软垫。上部金属 M4 位于 PCB 后缘内侧的接口，不穿过天线；天线本身的螺钉、螺母与垫圈全部使用非金属件。</p>
<p>主骨架层间位置沿用 V1.2.1，不调节。小安装板的短闭口槽只吸收装配位置差；锁紧后才可承载。闭口槽不是免锁紧设计，也不能宣称螺钉松开后仍保持精确方向。</p>
<h2>2. 孔距与允许的安装范围</h2>
'''
body+=table(['项目','本版采用值','含义'],[
 ['沿辐射方向孔边净距','21.66 mm','用户卡尺测得的最近孔边净距'],
 ['板面内垂直辐射方向孔边净距','26.60 mm','不是中心距'],
 ['实际 PCB 孔径','暂假定 3.00 mm','“适配 M3”不是直径实测'],
 ['名义孔中心距','24.66 × 29.60 mm','净距 + 假定实际孔径；后续可改参数'],
 ['四个打印让位窗口','5.2 × 5.2 mm，圆角 1 mm','原 PCB 孔不改、不扩'],
 ['每根 M3 局部位置余量','两个板面方向各 ±0.8 mm','9 个偏置／孔的名义刚体检查，不等于打印公差保证'],
 ['安装板相对上框位置余量','径向 ±10 mm；竖向 ±18 mm','两颗 M4 与交叉方向闭口槽共同对位'],
 ['有效板厚范围','0.8–4.0 mm 名义值','按指定软垫、垫圈和螺母的螺钉轴向堆叠检查'],
 ['整组孔中心到后缘止挡','24–44 mm','不是从照片量出的实物位置；超范围不可硬装'],
 ['整组孔中心高于下承托面','98–134 mm','下缘落座后测量或持件对照，不得悬空迁就孔位']])
body+='''
<p><strong>两种余量解决两种问题：</strong>5.2 mm 小窗口吸收孔距与打印误差；安装板的短闭口槽吸收孔组相对板边位置的不确定性。前者不能替代后者。超过上表有限范围时，应只修改安装板／局部接口并重新验证，不修改天线、不取消下托。</p>
<p>名义孔组中心为 X=166、Z=174 mm；旧后缘止挡 X=132，实际下承托软垫上表面 Z=58 mm。图中 240 mm 长、232 mm 高、1.6 mm 厚 PCB 仅用于碰撞示例，不能用于出天线尺寸图。</p>
<h2>3. 单副四孔连接：先台面预装，避免空中找螺母</h2>
<figure><img src="preview/04_cassette_exploded.png"><figcaption>四个局部凸台承接 PCB；背面平直，螺母不放进位置锁死的精配窝。孔组中间有开窗，馈线仍独立返回。</figcaption></figure>
<pre>头部 → 小尼龙垫圈 → PCB → 1 mm 孔周软垫 → 15 mm 安装板/凸台
     → 大外径尼龙垫圈（OD 9 mm） → 全尼龙 M3 螺母</pre>
<p>四颗螺钉先全部自然穿入，再交替轻轻拧到四处贴合；不要用螺钉强行拉正孔位。背面垫圈随螺杆移动，不能把螺母固定到四个刚性中心。背面大垫圈要跨住让位窗口，不用小垫圈任意替代。</p>
<p>接触软垫仅在凸台及旧下夹上使用。不要添加一整片厚塑料背板，不粘住或压住中轴馈线。尼龙和 PETG 都不是电磁透明材料；初版需要比较装配前后的匹配及方位响应。</p>
<h2>4. 推荐装配顺序</h2>
<ol>
<li><strong>薄样片先行。</strong>打印 T01，直接与实物四孔对照，四颗 M3 必须同时自然穿过。T01 厚 2 mm，仅用于对孔，不用它承重，不靠拧紧来凑孔距。</li>
<li><strong>试装一个真实 P07。</strong>打印 FIRST_FIT 板（一个 P07，加 T01/T02/T03）。在有软垫的台面上放稳天线，装孔周软垫、前后尼龙垫圈、4 颗 M3×25 和 4 个尼龙螺母；四处仅贴合，不压弯 PCB。T03 是局部接口试块，不是可单独悬挂天线的支架。</li>
<li><strong>安装主体。</strong>向裸方柱先放入 12 个结构螺母。4 颗底部 M4×20 加垫圈从底座下方上拧，之后才将底座夹固／锚固到台面。先安装并锁紧两块下半框，再安装两块上承载半框，各半框 2 颗 M4×20＋头下垫圈。</li>
<li><strong>保留下夹的正确入口。</strong>4 套下夹：先放 M4 工作螺母，再从顶部放入已贴软垫的双导柱压块。台面先组装外六角 M4×25、旋钮帽与背面保持螺母，再旋入下夹。只有保持螺母对旋钮轴向限位；它不是夹口工作螺母。用手推回压块，留出约2 mm附加间隙以便落入；名义装入检查采用这一步。</li>
<li><strong>PCB 与 P07 作为一个组件装入。</strong>各自从上方靠入，PCB 后部下缘真正落在 2 mm 承托软垫上，后缘靠齐旧止挡。P07 贴向新上框接口。先不锁下夹，用上框的两颗 M4×20 松装 P07，两颗都自然穿入才继续。</li>
<li><strong>M4 接口正反面各一片垫圈。</strong>每副 P07 两颗螺钉：盘头在外侧开放面，背面放平垫圈和普通 M4 螺母。背面可用 7 mm 小扳手／尖嘴钳辅助，不把螺母胶死在固定中心。手工先带入数扣，不用电动工具迫使塑料归位。</li>
<li><strong>先贴合再交替锁紧。</strong>保持下缘落座、板面不弯，上部两颗 M4 交替锁紧；最后轻合下夹，使它接触并辅助防转。上部装完若下缘离座，立即退回重装，不能加大下夹压力纠偏。四副采用一致姿态及可复现的对位标记。</li>
<li><strong>最后固定馈线。</strong>SMA 后方自然返回→本方向上框内侧线桥的下表面软衬→两根软绑带→方柱本侧两处整理点。线从侧面放入，不穿小孔。各路互不跨越，多余线长留在下方；不用线缆、SMA 或 PCB 作为搬运把手。</li>
</ol>
<p>拆单副时先解除本路线缆约束、托住板子，退开下夹并拆上部两颗 M4，整副 PCB 连同 P07 向上退出；不必在架子上反复拆 4 颗尼龙螺钉。带载时不要拆下层结构螺钉；维修下层需先移除天线及上层。</p>
<h2>5. P2S 打印与复用</h2>
'''
body+=table(['零件','数量','单件打印包围盒 mm','建议摆放 / 注意'],[
 [part_titles[g['id']],g['qty'],' × '.join(f'{v:g}' for v in g['bbox_mm']),{
 'P01_upper_carrier':'平底朝下；直立连接板横槽顶部为局部短桥接，逐层检查',
 'P02_lower_half':'原 V1.2.1 平底方向；下承托唇向上',
 'P03_fixed_mast':'竖直；侧装螺母窗口的短桥接需检查；按实际板面选择 brim',
 'P04_anchor_base':'平底；底面螺钉沉孔顶部检查桥接；先接柱再锚固',
 'P05_pressure_shoe':'大平面朝下、双导柱朝上；从夹口顶部装入',
 'P06_M4_knob':'平底朝下、六角窝朝上；背面另装保持螺母',
 'P07_four_hole_cassette':'平背面朝下、四凸台向上；孔位与槽竖向贯穿，不在孔中埋支撑'}[g['id']]]for g in G])
body+='''
<p><strong>只复用 V1.2.1 同编号合格件：</strong>P02×2、P03×1、P04×1、P05×4、P06×4。P01、P07 是新版。主结构仅更换上框；旧上夹的另外 4 套压块、旋钮、夹紧螺钉闲置。勿把最早 V1.2 的不可装压块混入。</p>
'''
body+=table(['正式排版','对象数','用途'],[[p['file'],p['objects'],'新打印'if p['file']in('FULL_02_UPPER.3mf','FULL_04_CASSETTES.3mf')else'已有合格 V1.2.1 件可跳过']for p in sorted(P,key=lambda x:x['file'])if p['file'].startswith('FULL')])
body+=f'''
<p>完整新制为 4 张正式排版，18 个硬质打印件。升级只需要 FULL_02 与 FULL_04 两张，6 个新件。合格首件 P07 可投入整机，正式第 4 板删除一个重复对象。</p>
<p>按 P2S 的 256×256×256 mm 打印空间拆件，来源：{link(0)}。3MF 是普通模型与位置文件，<strong>没有打印机配置、耗材设置、支撑、brim 或 G-code</strong>。实际 P2S 中选择喷嘴及材料后再切片；不能自动缩放模型，按层打印，不按对象逐个打印。</p>
<p>建议试打起点：普通未填充 PETG、0.4 mm 喷嘴、0.20 mm 层高、5 圈墙、约 30% 填充。软垫用合适的柔软硅胶或 TPU，不能用硬 PETG 替代。PETG 的桥接／支撑处理需要注意，参见 {link(9)}；不保证全部零件无需支撑。自动支撑不要塞进不可拆除的导槽和螺母槽。</p>
<p>四张正式板的模型最小间距约 5.0–15.6 mm，加入 brim 或支撑后必须重新检查，必要时重新排版。P03 高 200 mm，附近零件较多，不能开启逐对象打印而忽略喷头碰撞。</p>
<p><strong>没有实际切片计时。</strong>本版 STL 实体几何总体积约 {VOL:.1f} cm³，与 V1.2.1 的约 854.6 cm³ 接近；这不是实际耗材体积或重量。减少的是上部夹紧组件、首件成本和重复打印，不宣传打印时间下降一半。</p>
<h2>6. 首件验收与使用边界</h2>
<p>在低位软垫台面、底座已锚固的条件下先安装一副。四颗 M3 自然穿孔，螺母完整啮合；下缘持续落座，PCB 无可见弯曲；上下受轻微扰动后没有滑转或永久位移；轻拉下游线缆，SMA 及前段线不被牵动。做重复拆装，复查软垫、旋钮保持螺母和上部两颗 M4 的稳定性。</p>
<p>可在夹面／螺钉处作可擦对位标记，静置后与初装照片比较。这是建议验收方法，不是已完成试验。发现蠕变、软垫松弛、孔周压痕或开裂立即卸载。尼龙性能随持续载荷、温度和吸湿变化，不能照搬金属紧固件扭矩：{link(10)}。</p>
<p>本件为室内台架原型；未验证额定载荷、风载、运输带载、抗跌落、长期蠕变及 RF 方向图。局部几何无干涉不能代替实际载荷／RF 测试。已执行的几何检查详见<a href="Validation_V1_3_zh.html">本轮复核记录</a>。</p>
<h2>7. 修改与重新生成</h2>
<p>STEP 保存整体正确装配位置，源代码为 CadQuery。参数文件中的孔边净距和实际孔径分别保存，不把两者混为中心距。对接高度、印刷板占位和槽范围并非无限可调；修改后必须重跑检查、重做打印排版。脚本的名义测试包络不能自动验证任意实物轮廓。</p>
<pre>python -m pip install -r source/requirements.txt
python source/generate_v13.py
python source/audit_v13.py
python source/check_assembly_stages.py
python source/pack_v13.py
python source/render_v13.py
python source/make_overview.py
python source/export_soft_pads.py
python source/write_release_docs.py</pre>
<p>reference/v121 内保存原版几何供复用检查；legacy_v121.py 提供沿用的底座、方柱、下夹定义。不要只缩放一个 STL 修改尺寸，否则孔、螺母窝与配合关系会一起改变。</p>
'''
page('Assembly_Guide_V1_3_zh.html','V1.3 混合固定：保留下托，四孔带余量',body)
BOM=[
 ['M4-0.7×20 十字盘头（金属）',20,2,'12 颗底座／半框，8 颗四孔板接口',link(2)],
 ['M4-0.7×25 外六角全牙（金属）',4,0,'下夹旋钮；须靠近头部也有可用螺纹',link(3)+'；商品标题未确认全牙，采购复核'],
 ['M4 普通六角螺母（金属）',28,2,'12 结构＋8 接口＋4 下夹工作＋4 旋钮保持',link(4)],
 ['M4 薄平垫圈（金属）',28,4,'12 原结构＋16 接口，接口正反各一片',link(5)],
 ['M3-0.5×25 全牙盘头（全尼龙）',16,4,'穿 PCB；成品 PA66／普通未填充尼龙',link(1)+'；非 Home Depot 已确认现货'],
 ['M3-0.5 六角螺母（全尼龙）',16,4,'名义对边 5.5、高 2.4 mm',link(7)+'；核对具体尺寸'],
 ['M3 小垫圈（全尼龙）',16,4,'PCB 正面：ID≈3.2、OD≈7、厚0.5 mm','按该尺寸采购，未核实 Home Depot 对应品'],
 ['M3 大外径垫圈（全尼龙）',16,4,'安装板背面：ID≈3.2、OD≈9、厚0.8–1.0 mm',link(8)+'；系列规格示例，非当地库存声明'],
 ['窄尾软绑带',16,2,'每路上框2、方柱2；先穿窄尾',link(6)]]
body='''
<div class="note"><strong>本版是 M4 金属结构件＋M3 全尼龙天线固定件。</strong><br>共 40 颗螺钉：24 颗 M4、16 颗 M3。比“全夹具版”增加了四孔连接，不能沿用旧版的五金净数量。</div>
<p>下表净用量不含备件、台面锚固件。单副首件列针对实际 P07＋局部接口 T03，不含完整下夹／底座；首件试块不是承重支架。</p>
'''+table(['物料','整套','单副局部首件','位置／要求','采购目录'],BOM)+'''
<h2>不能混用的几种物料</h2>
<p><strong>全尼龙螺母 ≠ 带尼龙圈的金属防松螺母。</strong>后者主体仍为金属，不作为本版穿过天线附近的尼龙紧固件。PCB 前后不用金属垫圈，不自行打印细小 M3 螺纹代替成品紧固件。</p>
<p>M4×20 为盘头，不是沉头。下夹的 M4×25 为外六角全牙，不能改成内六角圆柱头；保持螺母需要拧到头部附近。采购如只有半牙螺钉，不要勉强装入旋钮。</p>
<p>4 个孔位的背面必须用 OD 约 9 mm 的大外径尼龙垫圈跨住 5.2 mm 窗口。不要把前面的小垫圈全数用到背面，也不要省去后垫圈让螺母只压一条窄边。窗口的“±0.8 mm”以指定外形检查，并非任意螺母或垫圈均兼容。</p>
<h2>螺钉长度与名义包络</h2>
<p>所有长度从头部下面量起。M3 穿板堆叠：前垫圈0.5＋PCB厚度t＋软垫1＋打印座15＋后垫圈1＋螺母2.4 = t+19.9 mm。M3×25 在 t=0.8–4.0 mm 时，穿过完整螺母后约余4.3–1.1 mm。若换成更厚垫圈、螺母或其他软垫，需重新计算，不以“25 mm”强行拉紧。</p>
<p>CAD 工具／五金检查包络：M4头直径8、高3.2；M4螺母对边7、高3.2；M4垫圈OD9、厚0.8；M3盘头最大示例OD5.6、高2.6；M3螺母对边5.5、高2.4。它们是名义检查外形，不是每个供应商产品的公差认证。实际物料先试配。</p>
<p>尼龙螺钉仅用合适手动螺丝刀轻拧至贴合；按供应商允许条件操作，不提供未经验证的扭矩数值。不要使用电动起子，不用额外胶黏剂把四个螺母定位成精配孔。</p>
<h2>软垫与工具</h2>
'''+table(['位置','每片名义尺寸 mm','数量','用途'],[
 ['下夹固定／活动面','20×20×1',8,'两面贴合，不能压弯 PCB'],
 ['下缘承托','18×14×2',4,'局部接住后部下缘'],
 ['四孔凸台','OD14×1，中央约5.4方形圆角窗',16,'减小硬接触，保留穿孔余量'],
 ['新上框馈线座','22×8×1',4,'下表面软衬'],
 ['立柱线缆接触处','按实际贴薄软衬','按需','不能改变线缆自然弯曲或压扁护套']])+'''
<p>软垫可裁切柔软硅胶片；包内 OPTIONAL_TPU 仅提供另一制作方式，使用未填充合适硬度 TPU。M3 尼龙紧固件不是这些打印软垫的一部分。</p>
<p>工具：与盘头匹配的十字螺丝刀，7 mm 小扳手、5.5 mm 小扳手或细尖嘴钳，剪刀和去毛刺工具。新 M4 接口用外露杆约80 mm、杆径≤5.5、手柄直径≤36 mm 的示例包络；M3 采用约70 mm杆、杆径≤4、手柄直径≤28 mm。标准不等于所有粗手柄都可达，优先台面预装 P07 的尼龙件。</p>
<h2>采购状态</h2>
<p><strong>金属 M4 螺钉、螺母、垫圈及软绑带已找到 Home Depot 目录对应商品；没有选择门店、没有核实当地现货。</strong>精确 M3 全尼龙套件和软硅胶片未核实到 Home Depot 对应现货，不承诺一次在该店买齐。Essentra 的 M3×25 尼龙件为对应规格参考；核对实际包装、材料和尺寸后采购。</p>
<p>底座锚固／夹固方式由实际台面确定，不额外增加 RF 开关板托盘或 SMA 穿板转接件。</p>
'''
page('BOM_V1_3_zh.html','V1.3 五金与软垫采购单',body)
rows=[
 ['静态装配','7种打印几何及装配五金／软垫','非预期正体积相交为0；判断阈值0.03 mm³'],
 ['局部孔余量','4孔×9偏置=36组','M3杆与窗口无干涉；OD9背垫圈最小名义承压接触面积约37.44 mm²'],
 ['整板安装余量','x=-10/0/+10、z=-18/0/+18，共9组','安装板、M4杆、后垫圈／螺母空间无检出干涉'],
 ['新增螺丝刀','8组M4接口＋16组M3，24组','示例相邻PCB已装；名义位置下杆／手柄无碰撞'],
 ['沿用结构工具','12结构位置×2工具规格，24组','依照底座→下框→上框的分阶段顺序检查'],
 ['下夹压块','4方向×4位置，16个保守扫掠包络','旧顶装压块路线在新上框存在时无碰撞'],
 ['尼龙螺母入口','16个背向进入保守扫掠','外形扫掠无碰撞；不等同真实手指／扳手握持'],
 ['PCB连安装板落入','4方向×6高度，24个采样姿态','含预装尼龙五金与孔周软垫；另三副完整示例天线已装，目标下夹退开2 mm，无检出碰撞；不是连续无碰撞证明'],
 ['单安装板落入','0…120 mm，5 mm间隔','一方向代表例无碰撞，依对称复制；不含任意新板形'],
 ['M3螺钉长度','6种名义板厚','全厚螺母均覆盖，最小余长1.1 mm'],
 ['示例RF线','4mm直径，固定分段路线','未检出打印结构干涉；最小弯曲半径未验证'],
 ['网格/STEP','7种STL，18件STEP回读','封闭、法向一致、单连通；回读实体与源几何体积一致'],
 ['复用件','5类原版STEP与新几何双向差','对称几何差为0；确认V1.2.1复用，不是更早版'],
 ['3MF','4张正式板＋2张试装板','独立回读数量与位置；正式18件，平面投影不重叠']]
body='''
<div class="note"><strong>当前几何脚本未检出失败项。</strong>该结论仅覆盖下面明确列出的模型、工具包络、位置与运动检查，不是已打印实物或结构标准认证。</div>
<p>复核对象是本次发布的实际 STL/STEP/3MF 与源代码，不是只看渲染图。旧 V1.2.1 参考 STEP 一并放在 reference/v121，便于独立确认哪些实体被保留。</p>
<h2>1. 设计过程中修正的干涉</h2>
<p>首个混合草案的原馈线桥与新安装板及其下落路线重叠。已在局部梁中让出移动通道，并把软绑带桥移向中央，最后重跑静态、位置及落入检查。两个 M4 补偿槽使用闭口结构，端部及螺栓列保留连续材料；删除右上方无用面料时未删除两螺栓列及下部承力带。</p>
<h2>2. 已实际执行的项目</h2>
'''+table(['项目','覆盖范围','结果与解释'],rows)+'''
<p>孔周37.44 mm²是垫圈与打印座名义重叠面积，<strong>不是</strong>尼龙垫圈允许承压、弯曲挠度或额定载荷。大范围位置、局部孔偏差和工具检查并未穷举所有组合；打印收缩、实际孔斜度与任意PCB轮廓不包含在这些离散检查里。</p>
<h2>3. 相邻天线与手工装配</h2>
<p>工具检查含占位 PCB，安装板 M4 螺钉布置在后缘内侧，避免螺丝刀必须穿过自己的天线板。四孔尼龙件建议在台面先装，因此不依赖手在狭窄中央空间内拿住四个小螺母。安装板背面的螺母通道开放，未把可变孔位重新锁死。</p>
<p>采用已知阶段顺序不代表任意顺序都可装。底座底部螺钉须先装再锚固，下框结构须先锁再装上框。不能声称上层带载时仍可自由维修下层。</p>
<h2>4. 尚未验证</h2>
<p>未执行 Bambu Studio 实际切片、支撑生成、打印首件、有限元分析、夹紧力／拉脱力、长期蠕变、跌落、风载或RF性能测试。没有额定承载数值，没有保证任意硬度尼龙或任意线径均兼容。实际孔径和孔组相对下缘／后缘仍需实物核对。</p>
<p><strong>下一步只放行小样／单副首装：</strong>T01自然穿孔；实际P07落座范围匹配；所有螺母／垫圈有正确接触；下托不悬空；PCB不弯；轻微扰动后无滑转；下游拉线不传到SMA。通过后才复制四路。使用过程中按观察结果决定复紧，不给出没有试验依据的周期和扭矩。</p>
<h2>5. 数据与复现</h2>
'''
body+=table(['文件','内容'],[[f'<a href="validation/{x}.json">{x}.json</a>',t]for x,t in[
 ('geometry','网格、数量、尺寸、实体体积'),('fasteners','40组螺钉的名义轴向连接'),('audit','孔位余量、位置、工具、落入与堆叠'),('assembly_stages','原结构工具、下夹入口、螺母入口、STEP复用'),('cable_route','4mm示例线径路线'),('plates','实际3MF回读与投影间距')]])
body+=f'<p>完整结构 STL 实体体积约 {VOL:.1f} cm³；几何体积不等于实际耗材。请勿把本报告的“0个几何失败项”转述成“已通过工程认证”。</p>\n'
page('Validation_V1_3_zh.html','V1.3 实际几何与装配复核记录',body)
start='''# LPDA V1.3 Hybrid — 先读这里

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
'''
(ROOT/'START_HERE_zh.md').write_text(start,encoding='utf-8')
(ROOT/'source'/'requirements.txt').write_text('\n'.join(f'{p}=={importlib.metadata.version(p)}'for p in ['cadquery','cadquery-ocp','numpy','scipy','trimesh','Pillow','vtk','shapely'])+'\n')
(ROOT/'docs'/'sources.json').write_text(json.dumps({'date':'2026-09-12','scope':'Public product/material references; not local-stock or structural certification.', 'sources':[{'title':t,'url':u}for t,u in SOURCES]},ensure_ascii=False,indent=2))
print('DOCS WRITTEN',ROOT)
