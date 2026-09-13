#!/usr/bin/env python3
"""Additional physical access checks, beyond assembled-part interference."""
from generate_v13 import *
from scipy.spatial import ConvexHull
from itertools import product

def convex_sweep(s, vector):
    pts=np.array([v.toTuple() for v in s.val().Vertices()]);pts=np.vstack((pts,pts+np.asarray(vector)))
    h=ConvexHull(pts);ff=[]
    for tri,eq in zip(h.simplices,h.equations):
        pp=pts[tri]
        if np.cross(pp[1]-pp[0],pp[2]-pp[0])@eq[:3]<0:pp=pp[::-1]
        w=cq.Wire.makePolygon([cq.Vector(*p) for p in pp]+[cq.Vector(*pp[0])]);ff.append(cq.Face.makeFromWires(w))
    return cq.Workplane('XY').newObject([cq.Solid.makeSolid(cq.Shell.makeShell(ff))]).clean()
def hits(s,items):return [dict(name=i['name'],volume_mm3=round(cv(s,i['shape']),5)) for i in items if cv(s,i['shape'])>.03]
D=Hybrid(json.loads((ROOT/'source'/'parameters.json').read_text())).make()
S=[i for i in D.items if i['id'] not in ('P05_pressure_shoe','P06_M4_knob')]
R={'scope':'Nominal conservative sweeps plus explicitly stated sampled motions. Not a physical installation test.'}
# Existing structural tools, after the real new geometry replaces the old upper.
rows=[]
for f in D.fasteners:
    if not f['name'].startswith(('base_','frame_')):continue
    active=S
    if f['name'].startswith('base_'):active=[i for i in S if i['id'] in ('P03_fixed_mast','P04_anchor_base')]
    elif f['name'].startswith('frame_40'):active=[i for i in S if i['id'] not in ('P01_upper_carrier','P07_four_hole_cassette')]
    elif f['name'].startswith('frame_170'):active=[i for i in S if i['id']!='P07_four_hole_cassette']
    p=np.array(f['head']);u=-np.array(f['axis'])
    for dd,ll,hh in [(5.5,90,26),(8,80,40)]:
        t=join(cyl(dd/2,ll,tuple(p+u*3.3),tuple(u)),cyl(hh/2,80,tuple(p+u*(3.3+ll)),tuple(u)))
        t=turn(t,f['angle']).translate((0,0,f['z_offset']))
        rows.append(dict(name=f['name'],shaft=dd,shaft_length=ll,handle=hh,hits=hits(t,active)))
R['staged_structure_drivers']=rows
# Retained lower shoes top-load (with upper carrier present, before PCB is installed).
rows=[]
for a,t in product((0,90,180,270),(.8,1.6,4,6.5)):
    env=join(box(137,157,t,t+5,6,71),box(137.2,140.8,t+4.9,t+18,14.2,62.8),box(153.2,156.8,t+4.9,t+18,14.2,62.8),box(137,157,t-1,t,6,71))
    env=turn(env,a).translate((0,0,52))
    rows.append(dict(angle=a,shoe_face_y=t,hits=hits(env,S)))
R['lower_shoe_conservative_45mm_sweeps']=rows
# M3 nut exterior insertion from the back; no PCB needed in this phase.
rows=[]
for a in (0,90,180,270):
    for ix,(dx,dz) in enumerate(product((-D.px/2,D.px/2),(-D.pz/2,D.pz/2))):
        x,z=D.hx+dx,D.hz+dz
        ex=hexagon(5.5,2.4,(x,-18,z),(0,-1,0))
        env=turn(convex_sweep(ex,(0,-50,0)),a)
        rows.append(dict(angle=a,hole=ix,hits=hits(env,S)))
R['nylon_nut_back_insertion_sweeps']=rows
# Complete preassembled PCB + cassette + ALL its nylon hardware and land pads.
# Other three antennas/cassettes/fasteners are present. Target lower clamp is
# retracted 2 mm in the local +Y direction; target adapter bolts are not installed.
rows=[]
unit_shapes=[D.parts['P07_four_hole_cassette'].shape,D.reference_pcb()]
unit_shapes += [i['shape'] for i in D.hardware if i['name'].startswith('nylon_0_')]
unit_shapes += [i['shape'] for i in D.pads if i['name'].startswith('hole_pad_0_')]
# Test components separately to avoid slow booleans on a large disconnected compound.
for a in (0,90,180,270):
    obstacles=[]
    for it in D.items+D.hardware+D.pads:
        name=it['name']
        if name==f'cassette_{a}' or name.startswith((f'nylon_{a}_',f'hole_pad_{a}_',f'adapter_{a}_')):continue
        ss=it['shape']
        retract=(name in (f'shoe_40_{a}',f'knob_40_{a}',f'moving_pad_40_{a}',f'clamp_40_{a}_bolt',f'clamp_40_{a}_retaining_nut'))
        if retract:ss=ss.translate((-2*math.sin(math.radians(a)),2*math.cos(math.radians(a)),0))
        obstacles.append(dict(name=name,shape=ss))
    obstacles += [dict(name=f'adjacent_pcb_{aa}',shape=turn(D.reference_pcb(),aa)) for aa in (0,90,180,270) if aa!=a]
    for z in (0,5,15,30,60,120):
        found=[]
        for component_index,component in enumerate(unit_shapes):
            u=turn(component.translate((0,0,z)),a)
            found += [dict(moving_component=component_index,**h) for h in hits(u,obstacles)]
        rows.append(dict(angle=a,vertical_offset_mm=z,nylon_hardware_included=True,adjacent_complete_antennas=True,lower_clamp_retracted_mm=2,hits=found))
R['PCB_cassette_insertion_24_sample_poses']=rows
# STEP exports really contain the intended independent parts; check per-part volume too.
rows=[]
for id,p in D.parts.items():
    sh=cq.importers.importStep(str(ROOT/'STEP'/f'{id}.step'))
    rows.append(dict(id=id,solids=len(sh.solids().vals()),valid=sh.val().isValid(),volume_delta_mm3=abs(sh.val().Volume()-p.shape.val().Volume())))
a=cq.importers.importStep(str(ROOT/'STEP'/'LPDA_V1_3_assembly.step'))
R['STEP_roundtrip']={'assembled_solids':len(a.solids().vals()),'parts':rows}
# Verify retained part geometry against published V1.2.1 STEP solids.
oldroot=ROOT/'reference'/'v121'
reuse=[]
for id in ('P02_lower_half','P03_fixed_mast','P04_anchor_base','P05_pressure_shoe','P06_M4_knob'):
    # Mesh triangulation may vary with exporter settings; compare original STEP solids,
    # not file hashes, and intersect both directions to verify geometry.
    orig=cq.importers.importStep(str(oldroot/f'{id}.step'))
    now=D.parts[id].shape
    reuse.append(dict(id=id,old_volume_mm3=orig.val().Volume(),new_volume_mm3=now.val().Volume(),symmetric_difference_mm3=orig.val().cut(now.val()).Volume()+now.val().cut(orig.val()).Volume()))
R['reuse_geometry']=reuse
bad=[]
for key in ('staged_structure_drivers','lower_shoe_conservative_45mm_sweeps','nylon_nut_back_insertion_sweeps','PCB_cassette_insertion_24_sample_poses'):
    bad += [dict(category=key,**r) for r in R[key] if r['hits']]
if len(a.solids().vals())!=18:bad.append({'STEP':'wrong count'})
if any(x['volume_delta_mm3']>.05 for x in rows):bad.append({'STEP':'volume discrepancy'})
R['failures']=bad
(ROOT/'validation'/'assembly_stages.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
print('STAGE FAILURES',json.dumps(bad,ensure_ascii=False),flush=True)
print('STEP count',len(a.solids().vals()),flush=True)
