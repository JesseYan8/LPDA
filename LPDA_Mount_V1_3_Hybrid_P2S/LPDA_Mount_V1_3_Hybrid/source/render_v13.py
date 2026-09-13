#!/usr/bin/env python3
from generate_v13 import *
from render_utils import render, tube, rot, C, panel, font
from PIL import Image,ImageDraw
D=Hybrid(json.loads((ROOT/'source'/'parameters.json').read_text())).make()
cache={}
def mes(s):return mesh(s)

def itemcolor(it):
    if it.get('id')=='P07_four_hole_cassette':return (.035,.54,.48)
    if it.get('id')=='P02_lower_half':return (.17,.39,.44)
    if it.get('id')=='P05_pressure_shoe':return (.3,.49,.53)
    if it.get('id')=='P06_M4_knob':return (.10,.57,.62)
    if it['name'].startswith('nylon'):return (.89,.86,.73)
    return (.13,.29,.35)
bare=[(mes(i['shape']),itemcolor(i),1) for i in D.items]
hard=[(mes(i['shape']),(.88,.84,.7) if i['name'].startswith('nylon') else (.65,.69,.73),1) for i in D.hardware]
pads=[(mes(i['shape']),(.2,.23,.25),1) for i in D.pads]
render(bare+hard+pads,ROOT/'preview'/'structure_raw.png',(610,-810,570),(0,0,150),234,(1600,1200))
panel(ROOT/'preview'/'structure_raw.png',ROOT/'preview'/'01_structure.png','V1.3 HYBRID | EXISTING LOWER SUPPORT RETAINED','4 lower clamps + 4 nylon hole cassettes | fixed backbone | no rotation / no tray','CAD model; nominal geometry only. Physical printing and load tests are still required.')
scene=bare+hard+pads
pcb=D.reference_pcb()
for a in (0,90,180,270):scene.append((mesh(turn(pcb,a)),(.10,.61,.38),.24))
# Cable geometry is an illustrative route, NOT a specified minimum bend radius.
mid=58+D.p['pcb_preview_height_mm']/2;tip=132+D.p['pcb_preview_length_mm']
pts=[[tip-10,4.5,mid],[160,4.5,mid]]
for u in np.linspace(0,1,40)[1:]:pts.append([160-100*u,4.5,mid+(D.seat-3-mid)*(1-math.cos(math.pi*u))/2])
pts.append([46,4.5,D.seat-3])
for u in np.linspace(0,math.pi/2,40)[1:]:pts.append([46-26*math.sin(u),4.5*(1-u/(math.pi/2)),D.seat-29+26*math.cos(u)])
pts.extend([[20,0,70],[20,0,30]])
for a in (0,90,180,270):
    scene.append((rot(tube(pts,2),a),(.05,.35,.82),1))
    sma=cyl(3,10,(tip-12,4.5,mid),(1,0,0)).union(hexagon(7.5,5,(tip-12,4.5,mid),(1,0,0)))
    scene.append((mesh(turn(sma,a)),(.65,.56,.36),1))
render(scene,ROOT/'preview'/'assembly_raw.png',(900,-1150,860),(0,0,155),380,(1800,1400))
panel(ROOT/'preview'/'assembly_raw.png',ROOT/'preview'/'02_assembly_reference.png','LPDA V1.3 | FOUR-HOLE + LOWER-SUPPORT HYBRID','Green PCB outlines and blue cables are illustrative; antenna dimensions are NOT measured.','Mounts contain local hole clearance AND independent installation compensation. Do not force PCB alignment.')
# One complete sector: upper + lower + cassette, useful to see load path.
sector=[]
clip=box(38,205,-45,45,35,300)
for it in D.items:
    if it['id'] in ('P03_fixed_mast','P04_anchor_base'):continue
    ss=it['shape'].intersect(clip)
    if ss.val().Volume()>1:sector.append((mesh(ss),itemcolor(it),1))
for it in D.hardware:
    if it['name'].startswith(('nylon_0_','adapter_0_','clamp_40_0_')):sector.append((mesh(it['shape']),(.89,.86,.73) if 'nylon' in it['name'] else (.68,.71,.74),1))
sector.append((mesh(pcb.intersect(box(130,203,-2,7,55,280))),(.10,.61,.38),.22))
render(sector,ROOT/'preview'/'sector_raw.png',(475,510,390),(127,-5,148),119,(1400,1300))
panel(ROOT/'preview'/'sector_raw.png',ROOT/'preview'/'03_single_sector.png','ONE ANTENNA | SUPPORT / LOCATE / RETAIN','Lower clamp stays. Upper pressure shoe is replaced, not stacked with another full clamp.','First seat the board. Fit all 4 nylon screws loosely. Lock the two rear-link M4 bolts last.')
# Cassette only, front view and exploded nylon hardware.
cs=[(mesh(D.parts['P07_four_hole_cassette'].shape),(.035,.53,.49),1)]
for it in D.hardware:
    if it['name'].startswith('nylon_0_'):
        sh=it['shape'];dy=13 if ('bolt' in it['name'] or 'front_washer' in it['name']) else -12
        cs.append((mesh(sh.translate((0,dy,0))),(.89,.86,.73),1))
for it in D.pads:
    if it['name'].startswith('hole_pad_0_'):cs.append((mesh(it['shape'].translate((0,5,0))),(.2,.25,.25),1))
render(cs,ROOT/'preview'/'cassette_raw.png',(315,460,320),(127,-7,185),82,(1500,1150))
panel(ROOT/'preview'/'cassette_raw.png',ROOT/'preview'/'04_cassette_exploded.png','LOCAL CASSETTE | OPEN ACCESS, NO FIXED NUT CAGES','M3 x 25 nylon screws | four 5.2 mm rounded windows | rear large nylon washers','Nominal pitch 24.66 x 29.60 mm assumes 3.00 mm PCB holes. Local screw offset target: +/-0.8 mm.')
# Plain CAD front projection with drawn scale/dimension callouts.
r=ROOT/'preview'/'cassette_front_raw.png'
render([(mesh(D.parts['P07_four_hole_cassette'].shape),(.06,.50,.46),1)],r,(128,700,186),(128,-11,186),65,(1200,1050))
panel(r,ROOT/'preview'/'05_cassette_face.png','PATTERN TOLERANCE IS NOT A FIXED FOUR-PIN FIT','The nut and rear washer move with each nylon screw. PCB holes are NOT enlarged.','All four lands share one contact plane; soft pads are fitted before tightening.')
# Test the exact piecewise cable centreline against the actual rigid geometry.
coll=[]
for j,(aa,bb) in enumerate(zip(pts,pts[1:])):
    aa=np.asarray(aa,float);bb=np.asarray(bb,float);v=bb-aa;l=np.linalg.norm(v)
    seg=cyl(2,l,tuple(aa),tuple(v/l))
    hits=[i['name'] for i in D.items+D.hardware if cv(seg,i['shape'])>.03]
    if hits:coll.append({'segment':j,'hits':hits})
(ROOT/'validation'/'cable_route.json').write_text(json.dumps({'illustrative_only':True,'line_diameter_mm':4,'rigid_part_interferences':coll,'minimum_bend_radius_not_validated':True},indent=2))
print('CABLE HITS',coll,flush=True)
# A compact single overview, no claims of real-world testing.
canvas=Image.new('RGB',(2100,1600),'#f4f8f8');dr=ImageDraw.Draw(canvas)
dr.text((45,22),'LPDA V1.3  /  HYBRID MOUNT',font=font( forty:=40,True),fill='#163e49')
dr.text((45,81),'Nylon four-hole attachment + retained lower support | Bambu Lab P2S',font=font(22),fill='#4e6d75')
im=Image.open(ROOT/'preview'/'assembly_raw.png');im.thumbnail((1230,1380));canvas.paste(im,(0,135))
im=Image.open(ROOT/'preview'/'sector_raw.png');im.thumbnail((850,800));canvas.paste(im,(1230,135))
im=Image.open(ROOT/'preview'/'cassette_raw.png');im.thumbnail((850,580));canvas.paste(im,(1230,910))
dr.text((1270,880),'Lower support remains; upper screw clamp removed.',font=font(18),fill='#254c56')
dr.text((45,1510),'18 printed parts | 4 hole cassettes | independent cable restraint | no rotating or adjustable backbone',font=font(23),fill='#264e57')
dr.text((45,1554),'PCB and cable models are illustrative, not measured. STL / STEP are real CAD; physical first-fit is still required.',font=font(18),fill='#627a81')
canvas.save(ROOT/'preview'/'LPDA_V1_3_overview.png')
