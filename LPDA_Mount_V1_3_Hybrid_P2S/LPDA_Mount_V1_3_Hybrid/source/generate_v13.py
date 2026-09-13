#!/usr/bin/env python3
"""LPDA V1.3 hybrid prototype; mm; no printer G-code.
Legacy lower support / mast / base are preserved. The upper pressure mechanism
is replaced by an independently fitted four-hole cassette. Hole spacing is
EDGE GAP + ASSUMED actual hole diameter; the diameter is NOT measured.
The short installation compensation is NOT an adjustable main clamp spacing.
"""
from __future__ import annotations
import argparse, json, math, pathlib, hashlib, sys
import cadquery as cq
import numpy as np
import trimesh
from legacy_v121 import box, cyl, hexagon, join, turn, mesh, cv, Part, print_shape, Design as Legacy
ROOT=pathlib.Path(__file__).resolve().parents[1]

def rounded_xz(cx,cz,w,h,r,yfront,depth):
    # XZ extrusion points in -Y; flat face at yfront.
    s=cq.Workplane('XZ').center(cx,cz).rect(w,h).extrude(depth).translate((0,yfront,0))
    if r:s=s.edges('|Y').fillet(r)
    return s

def slot_xz(cx,cz,L,w,angle,yfront,depth):
    return cq.Workplane('XZ').center(cx,cz).slot2D(L,w,angle).extrude(depth).translate((0,yfront,0))

class Hybrid:
    def __init__(self,p):
        self.p=p;self.parts={};self.items=[];self.hardware=[];self.pads=[];self.fasteners=[]
        self.px=p['edge_gap_radiation_mm']+p['assumed_pcb_hole_diameter_mm']
        self.pz=p['edge_gap_transverse_mm']+p['assumed_pcb_hole_diameter_mm']
        self.hx=p['cassette_center_x_mm'];self.hz=p['cassette_center_z_mm'];self.seat=p['upper_frame_seat_z_mm']
        self.bolt_xs=(80.,110.);self.bolt_z=self.seat+20
    def add(self,id,title,shape,qty,orient=(),note=''):
        shape=shape.clean()
        assert shape.val().isValid() and len(shape.solids().vals())==1,(id,'invalid or disconnected')
        self.parts[id]=Part(id,title,shape,qty,orient,note)
    def put(self,id,name,a=0,z=0):
        self.items.append(dict(id=id,name=name,shape=turn(self.parts[id].shape,a).translate((0,0,z))))
    def upper(self):
        # All dimensions here relative to legacy upper frame seating plane.
        s=box(-34,34,-34,34,0,8).cut(box(-16.35,16.35,-16.35,16.35,-1,50))
        keep=cq.Workplane('XY').polyline([(-300,300.6),(300,-299.4),(300,300)]).close().extrude(65).translate((0,0,-1))
        s=s.intersect(keep)
        beam=join(box(30,66,-26,24,0,8),box(44,132,-26,-6,0,4),
                  box(44,65,-26,-22,3.9,28),box(44,65,-10,-6,3.9,28))
        for ya,yb in ((-26,-22),(-10,-6)):
            beam=beam.union(cq.Workplane('XZ').polyline([(34,8),(54,28),(65,28),(65,8)]).close().extrude(yb-ya).translate((0,yb,0)))
        # Open-backed upright: rear nuts and a small wrench can approach in -Y.
        carrier=box(62,132,-23,-17,3.8,38)
        for x in self.bolt_xs:
            carrier=carrier.cut(slot_xz(x,20,26,4.6,0,-16,8))
        # Edge gussets kept out of swept washer/nut access envelopes.
        for xa,xb in ((62,65),(129,132)):
            rib=cq.Workplane('YZ').polyline([(-30,4),(-23,4),(-23,34)]).close().extrude(xb-xa).translate((xa,0,0))
            carrier=carrier.union(rib)
        beam=beam.union(carrier)
        # Same independent rear cable route as V1.2.1, on underside of bridge.
        # Keep the cable bridge inboard of the sliding cassette; no rail crosses its insertion path.
        beam=beam.cut(box(56,134,-17,-6,-1,45))
        saddle=box(42,68,-6.4,16,0,5)
        for x in (50,60):
            for ya,yb in ((-3,0),(9,12)):saddle=saddle.cut(box(x-4,x+4,ya,yb,-1,6))
        beam=beam.union(saddle)
        for a in (0,90):s=s.union(turn(beam,a))
        for x,y in ((26,-12),(-12,26)):s=s.cut(cyl(2.25,10,(x,y,-1)))
        for a in (0,90,180,270):s=s.cut(turn(box(18,36,-5,5,-1,45),a))
        # Three shallow bars designate revised upper carrier (not a legacy jaw).
        for j in range(3):s=s.cut(box(19+3*j,20.4+3*j,19,25,7.3,8.2))
        return s.clean()
    def cassette(self):
        hx,hz=self.hx,self.hz
        # Rear bridge: plate normal Y. Back -17; front -11, contact bosses to -2.
        body=rounded_xz(hx,hz,self.px+15,self.pz+15,3,-11,6)
        body=body.cut(rounded_xz(hx,hz,26,14,2,-10,8))
        # Mounting tongue toward mast, two CLOSED vertical compensation slots.
        tab=rounded_xz((68+hx-16)/2,self.bolt_z,(hx-16)-68,56,3,-11,6)
        for x in self.bolt_xs:
            tab=tab.cut(slot_xz(x,hz+(self.bolt_z-self.hz),44,4.6,90,-10,8))
        # Remove non-load-bearing upper-right corner; preserve both bolt columns and lower load strap.
        tab=tab.cut(rounded_xz(142,hz+53,46,60,4,-10,8))
        # Material relief between columns; retains substantial end straps.
        tab=tab.cut(rounded_xz(95,hz+29,15,30,2,-10,8))
        body=body.union(tab)
        for dx in (-self.px/2,self.px/2):
            for dz in (-self.pz/2,self.pz/2):
                x,z=hx+dx,hz+dz
                body=body.union(cyl(7,9,(x,-11,z),(0,1,0)))
                body=body.cut(rounded_xz(x,z,self.p['window_side_mm'],self.p['window_side_mm'],
                    self.p['window_corner_radius_mm'],-1,18))
        return body.clean()
    def make(self):
        legacy=Legacy({'pcb_preview_thickness':self.p['pcb_preview_thickness_mm']}).make()
        for id in ('P02_lower_half','P03_fixed_mast','P04_anchor_base','P05_pressure_shoe','P06_M4_knob'):
            o=legacy.parts[id];q=4 if id in ('P05_pressure_shoe','P06_M4_knob') else o.qty
            self.add(id,o.title,o.shape,q,o.orient,'UNCHANGED from V1.2.1; '+o.note)
        self.add('P01_upper_carrier','上层半框：开放螺母与短行程安装补偿',self.upper(),2,note='Flat underside down. No moving upper jaw.')
        self.add('P07_four_hole_cassette','四孔尼龙锁紧板／双闭口补偿槽',self.cassette(),4,(('X',90),),
                 note='Back side down, four raised lands upwards. No support inside holes.')
        # Reuse only the physically retained items, not the former upper jaws.
        for it in legacy.items:
            keep=it['id'] in ('P02_lower_half','P03_fixed_mast','P04_anchor_base') or ('40_' in it['name'] and it['id'] in ('P05_pressure_shoe','P06_M4_knob'))
            if keep:self.items.append(it)
        for it in legacy.hardware:
            if it['name'].startswith('clamp_170_'):continue
            self.hardware.append(it)
        for it in legacy.pads:
            if '170_' in it['name'] or it['name'].startswith('cable'):continue
            self.pads.append(it)
        self.fasteners.extend([f for f in legacy.fasteners if not f['name'].startswith('clamp_170_')])
        for a in (0,180):self.put('P01_upper_carrier',f'upper_carrier_{a}',a,self.seat)
        for a in (0,90,180,270):
            self.put('P07_four_hole_cassette',f'cassette_{a}',a)
            self.pads.append(dict(name=f'cable_pad_new_{a}',shape=turn(box(44,66,.5,8.5,self.seat-1,self.seat),a)))
            for i,x in enumerate(self.bolt_xs):
                z=self.bolt_z;head=(x,-10.2,z)
                bolt=cyl(2,20,head,(0,-1,0)).union(cyl(4,3.2,head,(0,1,0)))
                self.hardware.append(dict(name=f'adapter_{a}_{i}_bolt',shape=turn(bolt,a)))
                for n,y in [('front',-10.2),('rear',-23.)]:
                    wa=cyl(4.5,.8,(x,y,z),(0,-1,0)).cut(cyl(2.15,1,(x,y+.1,z),(0,-1,0)))
                    self.hardware.append(dict(name=f'adapter_{a}_{i}_{n}_washer',shape=turn(wa,a)))
                nu=hexagon(7,3.2,(x,-23.8,z),(0,-1,0)).cut(cyl(2,3.4,(x,-23.7,z),(0,-1,0)))
                self.hardware.append(dict(name=f'adapter_{a}_{i}_nut',shape=turn(nu,a)))
                self.fasteners.append(dict(name=f'adapter_{a}_{i}',diameter_mm=4,length_mm=20,engagement_mm=3.2,tip_past_nut_mm=3.2))
            for i,(dx,dz) in enumerate([(dx,dz) for dx in (-self.px/2,self.px/2) for dz in (-self.pz/2,self.pz/2)]):
                x,z=self.hx+dx,self.hz+dz;t=self.p['pcb_preview_thickness_mm'];heady=t-.5
                bo=cyl(1.5,25,(x,heady,z),(0,-1,0)).union(cyl(2.8,2.6,(x,heady,z),(0,1,0)))
                self.hardware.append(dict(name=f'nylon_{a}_{i}_bolt',shape=turn(bo,a)))
                wf=cyl(3.5,.5,(x,t-1,z),(0,1,0)).cut(cyl(1.6,.8,(x,t-1.1,z),(0,1,0)))
                wr=cyl(4.5,1,(x,-17,z),(0,-1,0)).cut(cyl(1.6,1.2,(x,-16.9,z),(0,-1,0)))
                nu=hexagon(5.5,2.4,(x,-18,z),(0,-1,0)).cut(cyl(1.5,2.6,(x,-17.9,z),(0,-1,0)))
                for n,v in [('front_washer',wf),('rear_large_washer',wr),('nut',nu)]:
                    self.hardware.append(dict(name=f'nylon_{a}_{i}_{n}',shape=turn(v,a)))
                pad=cyl(7,1,(x,-2,z),(0,1,0)).cut(rounded_xz(x,z,5.4,5.4,1,-.9,1.2))
                self.pads.append(dict(name=f'hole_pad_{a}_{i}',shape=turn(pad,a)))
                self.fasteners.append(dict(name=f'nylon_{a}_{i}',diameter_mm=3,length_mm=25,engagement_mm=2.4,tip_past_nut_mm=5.1-t))
        assert len(self.items)==18,(len(self.items),[x['name'] for x in self.items])
        return self
    def reference_pcb(self):
        z0=58.;mid=z0+self.p['pcb_preview_height_mm']/2;L=self.p['pcb_preview_length_mm'];t=self.p['pcb_preview_thickness_mm']
        s=cq.Workplane('XZ').polyline([(132,z0),(132+L,mid),(132,z0+2*(mid-z0))]).close().extrude(t).translate((0,t-1,0))
        for dx in (-self.px/2,self.px/2):
            for dz in (-self.pz/2,self.pz/2):s=s.cut(cyl(self.p['assumed_pcb_hole_diameter_mm']/2,t+2,(self.hx+dx,t,self.hz+dz),(0,-1,0)))
        return s

def export(d):
    for sub in ('STL','STEP','validation','reference'): (ROOT/sub).mkdir(exist_ok=True)
    rows=[]
    for id,o in d.parts.items():
        ss=print_shape(o);path=ROOT/'STL'/f'{id}.stl'
        cq.exporters.export(ss,str(path),tolerance=.07,angularTolerance=.14)
        cq.exporters.export(o.shape,str(ROOT/'STEP'/f'{id}.step'))
        m=trimesh.load_mesh(path)
        r=dict(id=id,qty=o.qty,bbox_mm=m.extents.round(3).tolist(),volume_mm3=float(m.volume),watertight=bool(m.is_watertight),winding=bool(m.is_winding_consistent),components=len(m.split()),valid=bool(o.shape.val().isValid()),print_note=o.note)
        assert r['watertight'] and r['winding'] and r['components']==1 and max(m.extents)<256,r
        rows.append(r);print(r,flush=True)
    ass=cq.Assembly(name='LPDA_V1_3_Hybrid_printed_parts')
    for it in d.items:ass.add(it['shape'],name=it['name'],color=cq.Color(.12,.33,.38) if it['id']!='P07_four_hole_cassette' else cq.Color(.04,.53,.48))
    ass.export(str(ROOT/'STEP'/'LPDA_V1_3_assembly.step'))
    for it in d.hardware:ass.add(it['shape'],name=it['name'],color=cq.Color(.85,.82,.70) if it['name'].startswith('nylon') else cq.Color(.60,.64,.67))
    for it in d.pads:ass.add(it['shape'],name=it['name'],color=cq.Color(.2,.24,.25))
    ass.export(str(ROOT/'STEP'/'LPDA_V1_3_hardware_assembly.step'))
    for a in (0,90,180,270):ass.add(turn(d.reference_pcb(),a),name=f'ILLUSTRATIVE_NOT_MEASURED_PCB_{a}',color=cq.Color(.08,.54,.32,.35))
    ass.export(str(ROOT/'STEP'/'LPDA_V1_3_visual_reference_NOT_MEASURED.step'))
    (ROOT/'validation'/'geometry.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    (ROOT/'validation'/'fasteners.json').write_text(json.dumps(d.fasteners,ensure_ascii=False,indent=2))
    # Small and flat first-fit templates: no full frame needs to be printed first.
    pat=d.parts['P07_four_hole_cassette'].shape.intersect(box(d.hx-22,d.hx+22,-17,-15,d.hz-24,d.hz+24))
    assert pat.val().isValid() and len(pat.solids().vals())==1
    cp=Part('T01_hole_pattern','四孔薄样片',pat,1,(('X',90),))
    cq.exporters.export(print_shape(cp),str(ROOT/'STL'/'T01_hole_pattern.stl'))
    # Reduced socket cross section to check washer / M4 slot / finger access offline.
    fit=box(0,68,0,30,0,6)
    for j,x in enumerate((15,49)):
        fit=fit.cut(cq.Workplane('XY').center(x,15).slot2D(26,4.6).extrude(8).translate((0,0,-1)))
    cq.exporters.export(fit,str(ROOT/'STL'/'T02_M4_slot_fit.stl'))
    return rows

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--params',type=pathlib.Path,default=ROOT/'source'/'parameters.json');args=ap.parse_args()
    design=Hybrid(json.loads(args.params.read_text())).make();export(design)
