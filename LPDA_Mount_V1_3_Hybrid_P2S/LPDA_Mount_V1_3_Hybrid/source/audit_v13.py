#!/usr/bin/env python3
"""Geometry audit. Explicit nominal envelopes, NOT a structural certification."""
from generate_v13 import *
from itertools import product
import time
D=Hybrid(json.loads((ROOT/'source'/'parameters.json').read_text())).make()
R={'scope':'Nominal BREP, assembly motions and analytical stack-ups; no physical test or FEA.','failures':[]}
allitems=D.items+D.hardware+D.pads
pairs=[]
for i,it in enumerate(allitems):
    for other in allitems[:i]:
        v=cv(it['shape'],other['shape'])
        if v>0.03:pairs.append(dict(a=it['name'],b=other['name'],volume_mm3=round(v,5)))
R['final_interferences']=pairs
print('FINAL',pairs,flush=True)
# Sliding install allowance: 9 representative poses, not infinite geometry fit.
mount=[]
static=[i for i in D.items if i['id']!='P07_four_hole_cassette']
for dx,dz in product((-10.,0.,10.),(-18.,0.,18.)):
    ca=D.parts['P07_four_hole_cassette'].shape.translate((dx,0,dz))
    hits=[(i['name'],round(cv(ca,i['shape']),5)) for i in static if cv(ca,i['shape'])>.03]
    # M4 threads must pass both crossed windows; washers must have bearing area.
    carrier=next(i['shape'] for i in D.items if i['name']=='upper_carrier_0')
    for x in D.bolt_xs:
        rod=cyl(2,22,(x+dx,-9,D.bolt_z),(0,-1,0))
        for lab,s in [('cassette',ca),('carrier',carrier)]:
            v=cv(rod,s)
            if v>.03:hits.append((lab+' thread collision',round(v,5)))
        # Rear nuts all must be accessible without contact with carrier edge ribs.
        envelope=cyl(4.5,4,(x+dx,-23.01,D.bolt_z),(0,-1,0))
        v=cv(envelope,carrier)
        if v>.03:hits.append(('rear washer/nut space',round(v,5)))
    mount.append(dict(dx_mm=dx,dz_mm=dz,hits=hits))
R['cassette_compensation_9_poses']=mount
print('POSES',mount,flush=True)
# Two-dimensional local hole float, using actual solid screw cylinder.
floats=[];areas=[]
ca=D.parts['P07_four_hole_cassette'].shape
for i,(dx,dz) in enumerate(product((-D.px/2,D.px/2),(-D.pz/2,D.pz/2))):
    x,z=D.hx+dx,D.hz+dz
    for ux,uz in product((-.8,0.,.8),(-.8,0.,.8)):
        rod=cyl(1.5,18,(x+ux,-.5,z+uz),(0,-1,0))
        v=cv(rod,ca)
        # A 0.05-mm wafer of the rear washer bearing against the back of plate.
        wa=cyl(4.5,.05,(x+ux,-17,z+uz),(0,1,0)).cut(cyl(1.6,.08,(x+ux,-17.01,z+uz),(0,1,0)))
        area=cv(wa,ca)/.05
        areas.append(area)
        floats.append(dict(hole=i,offset=[ux,uz],solid_overlap_mm3=round(v,6),rear_washer_bearing_mm2=round(area,3)))
R['M3_local_float_36_poses']=floats;R['minimum_rear_washer_bearing_mm2']=min(areas)
print('M3 floats bad', [x for x in floats if x['solid_overlap_mm3']>.03], 'min bearing',min(areas),flush=True)
# Fully extended driver shafts and handles after adjacent PCBs have been installed.
# Target bolts are removed from the obstacles. Shafts start outward of the drive face.
pcbs=[dict(name='pcb_'+str(a),shape=turn(D.reference_pcb(),a)) for a in (0,90,180,270)]
drivers=[]
for a in (0,90,180,270):
    for x in D.bolt_xs:
        shaft=turn(cyl(2.75,80,(x,-6.9,D.bolt_z),(0,1,0)),a)
        hand=turn(cyl(18,90,(x,73.1,D.bolt_z),(0,1,0)),a)
        obs=D.items+pcbs
        hits=[o['name'] for o in obs if cv(shaft,o['shape'])>.03 or cv(hand,o['shape'])>.03]
        drivers.append(dict(type='M4 adapter',angle=a,x=x,hits=hits))
    for dx,dz in product((-D.px/2,D.px/2),(-D.pz/2,D.pz/2)):
        x,z=D.hx+dx,D.hz+dz
        shaft=turn(cyl(2.,70,(x,D.p['pcb_preview_thickness_mm']+2.2,z),(0,1,0)),a)
        hand=turn(cyl(14,70,(x,D.p['pcb_preview_thickness_mm']+72.2,z),(0,1,0)),a)
        hits=[o['name'] for o in D.items+pcbs if cv(shaft,o['shape'])>.03 or cv(hand,o['shape'])>.03]
        drivers.append(dict(type='M3 nylon',angle=a,hits=hits))
R['driver_envelopes']=drivers
print('DRIVER BAD',[x for x in drivers if x['hits']],flush=True)
# Hardware placement routes: exact prisms translated along their normal approach,
# 1-mm sampled (not continuous proof). Typical sideways hand/tool gaps not physical hand model.
insert=[]
for name in ['cassette_0']:
    cas=next(i['shape'] for i in D.items if i['name']==name)
    # Drop parallel to carrier face, before M4 bolts and before lower clamp pressure.
    bad=[]
    for zz in np.arange(0,121,5):
        c=cas.translate((0,0,float(zz)))
        for i in static:
            v=cv(c,i['shape'])
            if v>.03:bad.append(dict(dz=float(zz),part=i['name'],volume=v))
    insert.append(dict(name=name,motion='Z down, 5 mm sampling, lower jaw open/no upper bolts',bad=bad))
R['cassette_drop_in']=insert
print('INSERT',insert,flush=True)
# Bolt lengths with normal nylon washer envelopes; full nut engagement at range ends.
stacks=[]
for t in (.8,1.,1.6,2.,3.,4.):
    # head-face -> back of full nut, all components in mm
    grip=0.5+t+1+15+1+2.4
    stacks.append(dict(pcb_mm=t,grip_mm=grip,bolt_mm=25,tip_beyond_mm=25-grip,full_nut=25>=grip))
R['nylon_M3x25_six_thicknesses']=stacks
# Derived relation to legacy rear/bottom datum; NOT measured on the physical antenna.
R['whole_pattern_installation_envelope_mm']={
    'center_radial_from_rear_stop':[D.hx-10-132,D.hx+10-132],
    'center_height_above_lower_seat':[D.hz-18-58,D.hz+18-58],
    'warning':'Only within this envelope can the present linkage fit without regenerating it. Do not lift PCB off lower seat to force hole alignment.'}
R['unchanged_reuse_ids']=['P02_lower_half','P03_fixed_mast','P04_anchor_base','P05_pressure_shoe','P06_M4_knob']
R['not_tested']=['printed tolerances','Bambu Studio slicing/support generation','physical first fit','creep/strength/pull test','actual cable bend radius','RF matching/patterns','true PCB hole diameter and edge-to-pattern location']
R['failures'] += pairs
R['failures'] += [p for p in mount if p['hits']]
R['failures'] += [p for p in floats if p['solid_overlap_mm3']>.03]
R['failures'] += [p for p in drivers if p['hits']]
R['failures'] += [p for p in insert if p['bad']]
(ROOT/'validation'/'audit.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
print('TOTAL FAILURE RECORDS',len(R['failures']),flush=True)
