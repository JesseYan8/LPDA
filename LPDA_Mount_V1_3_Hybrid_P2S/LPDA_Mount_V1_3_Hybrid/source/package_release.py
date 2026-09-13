#!/usr/bin/env python3
"""Final consistency checks and ZIP packaging; no printer G-code is produced."""
from pathlib import Path
import json, zipfile, hashlib, py_compile
from collections import Counter
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent

def include(path):
 return path.is_file() and '__pycache__' not in path.parts and not path.name.endswith('_raw.png') and path.suffix!='.pyc'

def run():
 g=json.loads((ROOT/'validation/geometry.json').read_text());a=json.loads((ROOT/'validation/audit.json').read_text());s=json.loads((ROOT/'validation/assembly_stages.json').read_text());p=json.loads((ROOT/'validation/plates.json').read_text());c=json.loads((ROOT/'validation/cable_route.json').read_text())
 assert len(g)==7 and sum(x['qty']for x in g)==18
 assert not a['failures'] and not s['failures'] and not c['rigid_part_interferences']
 assert all(x['watertight'] and x['winding'] and x['components']==1 and x['valid'] for x in g)
 assert all(x.get('nylon_hardware_included') and x.get('adjacent_complete_antennas')for x in s['PCB_cassette_insertion_24_sample_poses'])
 assert all(x['symmetric_difference_mm3']<.05 for x in s['reuse_geometry'])
 assert s['STEP_roundtrip']['assembled_solids']==18
 assert len(json.loads((ROOT/'validation/fasteners.json').read_text()))==40
 expected={x['id']:x['qty']for x in g};actual=Counter()
 for row in p:
  assert row['geometry_only'] and row['no_gcode']
  with zipfile.ZipFile(ROOT/'plates'/row['file']) as z:assert z.testzip() is None
  if row['file'].startswith('FULL'):
   for entry in row['entries']:actual[entry['name'].rsplit('_',1)[0]]+=1
 assert dict(actual)==expected,(actual,expected)
 broken=[]
 for f in ROOT.glob('*.html'):
  tree=html.parse(str(f))
  for url in tree.xpath('//@href | //@src'):
   if url.startswith(('http:','https:','data:','#','mailto:')):continue
   target=f.parent/url.split('#')[0]
   if not target.exists():broken.append((f.name,url))
 assert not broken,broken
 for f in (ROOT/'source').glob('*.py'):py_compile.compile(str(f),doraise=True)
 report={'release':'V1.3 Hybrid','formal_print_parts':18,'formal_types':7,'screws_total':40,'new_prints_from_V121':6,'geometry_failure_records':0,'retained_STEP_symmetric_difference_mm3':{x['id']:x['symmetric_difference_mm3']for x in s['reuse_geometry']},'plate_quantity_check':dict(actual),'local_HTML_broken_links':broken,'motion_checks_include_preassembled_nylon':True,'no_physical_or_slicer_validation':True}
 (ROOT/'validation/release_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 files=sorted(f for f in ROOT.rglob('*')if include(f) and f.name!='SHA256SUMS.txt')
 (ROOT/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(ROOT).as_posix()for f in files)+'\n')
 files.append(ROOT/'SHA256SUMS.txt')
 dest=OUT/'LPDA_Mount_V1_3_Hybrid_P2S.zip'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for f in files:z.write(f,(Path(ROOT.name)/f.relative_to(ROOT)).as_posix())
  assert z.testzip() is None
 common=[f for f in files if f.parent==ROOT and f.suffix in('.html','.md')or (f.parent==ROOT/'preview')or (f.parent==ROOT/'validation' and f.suffix=='.json')or f.parent==ROOT/'docs']
 kits=[
  ('LPDA_V1_3_First_Fit_Kit.zip','LPDA_V1_3_First_Fit',
   ['STL/P07_four_hole_cassette.stl','STL/T01_hole_pattern.stl','STL/T02_M4_slot_fit.stl','STL/T03_carrier_fit.stl','STEP/P07_four_hole_cassette.step','plates/FIRST_FIT_CASSETTE_NOT_LOAD_TEST.3mf','plates/TINY_HOLE_PATTERN_ONLY.3mf'],
   '本包仅含局部首件：一块P07、T01/T02/T03及对应3MF。先用T01确认四孔，再用真实P07装尼龙件。\n快检块不能单独承重。主骨架、完整源代码和其余STEP请使用完整设计包。\n每副首件需要：M3×25尼龙4、M3尼龙螺母4、正面小垫圈4、背面大垫圈4、孔周软垫4；接口另用M4×20两颗、螺母2、薄垫圈4。\n'),
  ('LPDA_V1_3_Upgrade_from_V121.zip','LPDA_V1_3_Upgrade',
   ['STL/P01_upper_carrier.stl','STL/P07_four_hole_cassette.stl','STEP/P01_upper_carrier.step','STEP/P07_four_hole_cassette.step','STEP/LPDA_V1_3_assembly.step','plates/FULL_02_UPPER.3mf','plates/FULL_04_CASSETTES.3mf'],
   '只在已有合格V1.2.1下框/方柱/底座/压块/旋钮时使用本升级包。\nFULL_02打印2个上承载半框，FULL_04打印4个P07。其他打印件复用，不要重复打印。\nM4接口新增8套（正反各一垫圈），并新增16套M3全尼龙固定件；对照完整BOM核算手上可复用五金。\n本包不含完整源代码及所有原版STL，需要时使用完整包。\n')]
 for name,folder,rel,readme in kits:
  chosen={*common,*[ROOT/x for x in rel],*[f for f in files if f.parent==ROOT/'OPTIONAL_TPU']}
  with zipfile.ZipFile(OUT/name,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   z.writestr(folder+'/KIT_README_zh.md',readme)
   for f in sorted(chosen):z.write(f,(Path(folder)/f.relative_to(ROOT)).as_posix())
   assert z.testzip() is None
 for f in [dest,*[OUT/x[0]for x in kits]]:print(f.name, f.stat().st_size)
 print('RELEASE CHECKS PASS')
if __name__=='__main__':run()
