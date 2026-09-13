#!/usr/bin/env python3
"""Optional soft-pad geometries. These are NOT PETG structural parts or screws."""
from generate_v13 import *
out=ROOT/'OPTIONAL_TPU';out.mkdir(exist_ok=True)
shapes={
 'S01_lower_face_20x20x1':(box(0,20,0,20,0,1),8),
 'S02_lower_seat_18x14x2':(box(0,18,0,14,0,2),4),
 'S03_hole_land_OD14_T1':(cq.Workplane('XY').circle(7).extrude(1).cut(cq.Workplane('XY').rect(5.4,5.4).extrude(2).edges('|Z').fillet(1)),16),
 'S04_cable_pad_22x8x1':(box(0,22,0,8,0,1),4)}
rows=[]
for name,(shape,qty) in shapes.items():
 p=Part(name,name,shape,qty,())
 path=out/(name+'.stl');cq.exporters.export(print_shape(p),str(path),tolerance=.05,angularTolerance=.1)
 m=trimesh.load_mesh(path)
 assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
 rows.append(dict(id=name,qty=qty,bbox_mm=m.extents.tolist(),watertight=bool(m.is_watertight)))
(out/'README_zh.md').write_text('仅是软垫的可选制造方式，可用尺寸相同的柔软硅胶片替代。\n不要用PETG打印这些软垫。尼龙M3螺钉、螺母、垫圈必须使用购买的成品，不属于这组文件。\nS01×8，S02×4，S03×16，S04×4。打印软垫未做实际验证。\n',encoding='utf-8')
(ROOT/'validation'/'optional_soft_pads.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print('Optional soft pads:',len(rows),'types')
