#!/usr/bin/env python3
"""LPDA fixed fixture V1.2.1; CadQuery BREP, millimetres.
No template of the antenna outline and no adjustable clamp spacing.
A prototype, not a load-certified product. Exported meshes are print-oriented.
"""
from __future__ import annotations
import json, math, pathlib, argparse
from dataclasses import dataclass
import cadquery as cq
import numpy as np
import trimesh
ROOT=pathlib.Path(__file__).resolve().parents[1]
DEFAULT={'fit_clearance':0.35,'clamp_spacing':130.0,'lower_seat_z':40.0,
         'pcb_preview_thickness':1.6,'pcb_preview_height':224.0,'pcb_preview_length':240.0,
         'cable_preview_diameter':4.0,'knob_floor':2.6}

def box(x0,x1,y0,y1,z0,z1):
    assert x1>x0 and y1>y0 and z1>z0
    return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).translate(((x1+x0)/2,(y1+y0)/2,(z1+z0)/2))
def cyl(r,L,start,axis=(0,0,1)):
    return cq.Workplane('XY').newObject([cq.Solid.makeCylinder(r,L,cq.Vector(*start),cq.Vector(*axis))])
def align_z(s,axis):
    a=np.array(axis,float);a/=np.linalg.norm(a);v=np.array([0.,0.,1.])
    if np.allclose(a,v):return s
    if np.allclose(a,-v):return s.rotate((0,0,0),(1,0,0),180)
    return s.rotate((0,0,0),tuple(np.cross(v,a)),float(np.degrees(np.arccos(np.clip(v@a,-1,1)))))
def hexagon(af,L,start=(0,0,0),axis=(0,0,1),clock=0):
    s=cq.Workplane('XY').polygon(6,af/math.cos(math.pi/6)).extrude(L)
    if clock:s=s.rotate((0,0,0),(0,0,1),clock)
    return align_z(s,axis).translate(start)
def join(*args):
    s=args[0]
    for v in args[1:]:s=s.union(v)
    return s.clean()
def turn(s,a):return s.rotate((0,0,0),(0,0,1),a)
def mesh(s):
    v,f=s.val().tessellate(.085,.14)
    return trimesh.Trimesh(np.array([x.toTuple() for x in v]),np.array(f),process=True)
def cv(a,b):
    aa=a.val().BoundingBox();bb=b.val().BoundingBox()
    if aa.xmax<=bb.xmin+.0001 or bb.xmax<=aa.xmin+.0001 or aa.ymax<=bb.ymin+.0001 or bb.ymax<=aa.ymin+.0001 or aa.zmax<=bb.zmin+.0001 or bb.zmax<=aa.zmin+.0001:return 0.
    return a.val().intersect(b.val()).Volume()
def slot(x,y,L,w,z0,z1):
    return cq.Workplane('XY').center(x,y).slot2D(L,w).extrude(z1-z0).translate((0,0,z0))
@dataclass
class Part:
    id:str; title:str; shape:object; qty:int; orient:tuple=(); note:str=''
def print_shape(p):
    s=p.shape
    for ax,ang in p.orient:s=s.rotate((0,0,0),dict(X=(1,0,0),Y=(0,1,0),Z=(0,0,1))[ax],ang)
    bb=s.val().BoundingBox();return s.translate((-bb.xmin,-bb.ymin,-bb.zmin))

class Design:
    def __init__(self,p=None):
        self.p=DEFAULT.copy();self.p.update(p or {})
        self.parts={};self.items=[];self.hardware=[];self.pads=[];self.fasteners=[]
        self.levels=[self.p['lower_seat_z'],self.p['lower_seat_z']+self.p['clamp_spacing']]
        self.mast_height=self.levels[1]+30;self.base_h=12.
        self.joints=[(26,-12),(-12,26),(-26,12),(12,-26)]
        self.lower_joints=[(54,-16),(-16,54),(-54,16),(16,-54)]
    def add(self,id,title,s,qty,orient=(),note=''):
        s=s.clean();assert s.val().isValid() and len(s.solids().vals())==1,(id,'invalid/disconnected')
        self.parts[id]=Part(id,title,s,qty,orient,note);return s
    def put(self,id,name,a=0,z=0,s=None):
        s=turn(s if s is not None else self.parts[id].shape,a).translate((0,0,z))
        self.items.append({'id':id,'name':name,'shape':s});return s
    def hard(self,name,s,a=0,z=0):
        s=turn(s,a).translate((0,0,z));self.hardware.append({'name':name,'shape':s});return s
    def soft(self,name,s,a=0,z=0):
        s=turn(s,a).translate((0,0,z));self.pads.append({'name':name,'shape':s});return s
    def frame(self,lower):
        c=self.p['fit_clearance']
        s=box(-34,34,-34,34,0,8).cut(box(-16-c,16+c,-16-c,16+c,-1,30))
        # Split at x+y=0; an assembly gap, not an adjustable joint.
        keep=cq.Workplane('XY').polyline([(-300,300.6),(300,-299.4),(300,300)]).close().extrude(35).translate((0,0,-1))
        s=s.intersect(keep)
        # An open-top, two-web beam: no long cantilevered top-flange support.
        beam=join(box(30,62 if lower else 52,-26,24,0,8),box(44,128,-26,-6,0,4),
                  box(44,128,-26,-22,3.9,28),box(44,128,-10,-6,3.9,28),
                  box(112,128,-26,-6,3.9,28))
        # Solid load-transfer root with a 45 degree rise, not an abrupt thin neck.
        for ya,yb in ((-26,-22),(-10,-6)):
            ramp=cq.Workplane('XZ').polyline([(34,8),(54,28),(54,8)]).close().extrude(yb-ya).translate((0,yb,0))
            beam=beam.union(ramp)
        cl=join(box(124,132,-26,22,0,28),box(132,161,-8,-2,0,28),box(132,161,12,22,0,28))
        # Top-loaded nut, open and serviceable; 7 mm AF is across x.
        cl=cl.cut(box(143.3,150.7,11.9,15.6,11.7,29))
        cl=cl.cut(cyl(2.25,12,(147,11,16),(0,1,0)))
        # R1: top-entry guides, not closed bores. The entire shoe is lowered in Z.
        # Side clearance is 0.3 mm. The open guide floor sets the 16 mm screw centre height.
        for x in (139,155):
            cl=cl.cut(box(x-2.1,x+2.1,11,23,14.2,29))
            # Small 45-degree entrance flare, preserves the lower locating walls.
            flare=cq.Workplane('XZ').polyline([(x-2.1,26.8),(x+2.1,26.8),(x+3.3,28),(x-3.3,28)]).close().extrude(12).translate((0,23,0))
            cl=cl.cut(flare)
        if lower:cl=cl.union(box(132,150,-2,12,0,4))
        arm=beam.union(cl)
        if not lower:
            # Cable is held under this bridge with two SOFT bands, not rigidly pinched.
            saddle=box(88,124,-6.4,16,0,5)
            for x in (98,114):
                for ya,yb in ((-3,0),(9,12)):saddle=saddle.cut(box(x-4,x+4,ya,yb,-1,6))
            arm=arm.union(saddle)
        for a in (0,90):s=s.union(turn(arm,a))
        for x,y in (self.lower_joints if lower else self.joints)[:2]:s=s.cut(cyl(2.25,10,(x,y,-1)))
        # Four straight, side-loaded cable corridors continue through the collars.
        for a in (0,90,180,270):s=s.cut(turn(box(18,36,-5,5,-1,30),a))
        # Small unambiguous layer marks: one bar lower, two bars upper.
        for j in range(1 if lower else 2):s=s.cut(box(19+3*j,20.4+3*j,19,25,7.3,8.2))
        return s.clean()
    def make(self):
        self.add('P01_upper_half','上层半框／顶装压块导槽与独立馈线座',self.frame(False),2,note='平底朝下；导槽向上开放。其余孔槽按切片逐层复核；不将支撑塞满螺母口。')
        self.add('P02_lower_half','下层半框／顶装导槽、外移螺孔与板边承托',self.frame(True),2,note='平底朝下；承托唇不可削薄；贴 2 mm 软垫。')
        H=self.mast_height
        m=join(box(-16,16,-16,16,0,H),box(-32,32,-32,32,0,8))
        for seat in self.levels:
            lower=(seat==self.levels[0]);joints=self.lower_joints if lower else self.joints
            if lower:
                # R1: lower bolt centres moved 8 mm radially out, with their own 8 mm thick support pads.
                ring=box(-16,16,-16,16,seat-1,seat)
                for bx,by in joints:
                    a=0 if bx==54 else 90 if by==54 else 180 if bx==-54 else 270
                    tangent=(by if a==0 else -bx if a==90 else -by if a==180 else bx)
                    rib=cq.Workplane('XZ').polyline([(15.8,0),(38,0),(62,24),(62,seat),(15.8,seat)]).close().extrude(12).translate((0,tangent+6,0))
                    ring=ring.union(turn(rib,a))
                m=m.union(ring)
            else:
                shoulder=cq.Workplane('XY').workplane(offset=seat-28).rect(32,32).workplane(offset=16).rect(64,64).loft()
                inner=cq.Workplane('XY').workplane(offset=seat-28-.01).rect(22,22).workplane(offset=16.02).rect(52,52).loft()
                shoulder=shoulder.cut(inner)
                ring=box(-32,32,-32,32,seat-12,seat).cut(box(-26,26,-26,26,seat-12.1,seat+.1))
                for bx,by in joints:
                    a=0 if bx==26 else 90 if by==26 else 180 if bx==-26 else 270
                    tangent=(by if a==0 else -bx if a==90 else -by if a==180 else bx)
                    rib=cq.Workplane('XZ').polyline([(16,seat-28),(29,seat-15),(29,seat),(16,seat)]).close().extrude(12).translate((0,tangent+6,0))
                    ring=ring.union(turn(rib,a))
                m=m.union(shoulder).union(ring)
            for x,y in joints:
                m=m.cut(cyl(2.25,17,(x,y,seat-15)))
                m=m.cut(hexagon(7.4,3.6,(x,y,seat-10.4)))
                reach=64 if lower else 34
                if abs(x)>abs(y):
                    xa,xb=(x,reach) if x>0 else (-reach,x)
                    m=m.cut(box(xa,xb,y-3.7,y+3.7,seat-10.4,seat-6.8))
                else:
                    ya,yb=(y,reach) if y>0 else (-reach,y)
                    m=m.cut(box(x-4.3,x+4.3,ya,yb,seat-10.4,seat-6.8))
        m=m.cut(box(-11,11,-11,11,-1,H+1))
        for a in (0,90,180,270):
            m=m.cut(turn(box(18,36,-5,5,-1,H+1),a))
            for z in (78,118):
                for ya,yb in ((-12,-7),(7,12)):
                    lug=box(15.9,22.5,ya,yb,z,z+14)
                    ramp=cq.Workplane('XZ').polyline([(16,z-9),(22.5,z),(16,z)]).close().extrude(yb-ya).translate((0,yb,0))
                    lug=lug.union(ramp).cut(box(18,20.5,ya-1,yb+1,z+3,z+11))
                    m=m.union(turn(lug,a))
        for x in (-24,24):
            for y in (-24,24):
                m=m.cut(cyl(2.25,10,(x,y,-1))).cut(hexagon(7.4,4.2,(x,y,4)))
                xa,xb=(x,66) if x>0 else (-66,x)
                m=m.cut(box(xa,xb,y-3.7,y+3.7,4,8.2))
        self.add('P03_fixed_mast','固定方柱／扩展下层支承与四路走线',m,1,note='竖直打印；两层固定台肩，不含调节孔；底部建议 5–6 mm brim。')
        b=box(-32,32,-32,32,0,12)
        for a in (0,90,180,270):
            arm=join(box(28,72,-14,14,0,6),box(54,74,-18,18,0,6))
            for ya,yb in ((-13,-9),(9,13)):
                arm=arm.union(cq.Workplane('XZ').polyline([(32,6),(32,12),(58,6)]).close().extrude(yb-ya).translate((0,yb,0)))
            arm=arm.cut(slot(65,0,12,5.5,-1,7))
            b=b.union(turn(arm,a))
        b=b.union(box(-10.65,10.65,-10.65,10.65,11.9,16))
        for x in (-24,24):
            for y in (-24,24):b=b.cut(cyl(2.25,14,(x,y,-1))).cut(cyl(5.,5.,(x,y,-.2)))
        self.add('P04_anchor_base','减料十字锚固底座',b,1,note='底面朝下；至少两个分开的锚固点；不是配重底座。')
        # R1: top-entry shoe with 5 mm body, for retention-nut clearance at thin PCB settings.
        sh=box(137,157,0,5,-10,10)
        for x in (139,155):sh=sh.union(box(x-1.8,x+1.8,4.9,18,-1.8,1.8))
        sh=sh.cut(cyl(2.2,1.1,(147,4,0),(0,1,0)))
        # Lead-in to the screw-tip pocket; no ball joint and no extra part.
        lead=cq.Workplane('XY').newObject([cq.Solid.makeCone(2.2,2.7,.5,cq.Vector(147,4.5,0),cq.Vector(0,1,0))])
        sh=sh.cut(lead)
        self.add('P05_pressure_shoe','双导柱活动压块',sh,8,(('X',90),),note='大平面朝下、导柱朝上；粘 1 mm 软垫。')
        k=cyl(12,6.4,(0,0,0))
        for ang in np.linspace(0,2*math.pi,16,endpoint=False):k=k.cut(cyl(1.2,10,(12*math.cos(ang),12*math.sin(ang),-1)))
        k=k.cut(cyl(2.25,10,(0,0,-1))).cut(hexagon(7.4,5,(0,0,self.p['knob_floor'])))
        self.add('P06_M4_knob','M4 外六角旋钮／背面标准保持螺母',k,8,note='头部陷入六角槽；背面另装一颗标准 M4 保持螺母。全牙螺钉；先在台面组装旋钮。')
        self.assemble();return self
    def screw(self,name,head,axis,L,nutplane,hexhead=False,a=0,z=0):
        p=np.array(head,float);v=np.array(axis,float)
        s=cyl(2.,L,tuple(p),tuple(v))
        hs=hexagon(7.,2.8,tuple(p-2.8*v),tuple(v)) if hexhead else cyl(4.,3.2,tuple(p-3.2*v),tuple(v))
        self.hard(name+'_bolt',s.union(hs),a,z)
        if not hexhead:self.hard(name+'_washer',cyl(4.5,.8,tuple(p),tuple(v)).cut(cyl(2.15,1,tuple(p-.1*v),tuple(v))),a,z)
        np0=np.array(nutplane,float)
        nut=hexagon(7,3.2,tuple(np0),tuple(v),clock=30 if hexhead else 0).cut(cyl(2.,3.4,tuple(np0-.1*v),tuple(v)))
        self.hard(name+'_nut',nut,a,z)
        q=float((np0-p)@v)
        self.fasteners.append({'name':name,'length_mm':L,'head':head,'axis':axis,'angle':a,'z_offset':z,
          'hexhead':hexhead,'nut_start_mm':q,'engagement_mm':max(0,min(q+3.2,L)-max(0,q)),'tip_past_nut_mm':L-q-3.2})
    def assemble(self):
        t=self.p['pcb_preview_thickness'];B=self.base_h
        self.put('P04_anchor_base','anchor_base')
        self.put('P03_fixed_mast','fixed_mast',z=B)
        for x in (-24,24):
            for y in (-24,24):self.screw(f'base_{x}_{y}',(x,y,4.0),(0,0,1),20,(x,y,16.0))
        for lower,seat in ((True,self.levels[0]),(False,self.levels[1])):
            id='P02_lower_half' if lower else 'P01_upper_half'
            for a in (0,180):self.put(id,f'{"lower" if lower else "upper"}_half_{a}',a=a,z=B+seat)
            for i,(x,y) in enumerate(self.lower_joints if lower else self.joints):self.screw(f'frame_{int(seat)}_{i}',(x,y,8.8),(0,0,-1),20,(x,y,-6.8),z=B+seat)
            for a in (0,90,180,270):
                self.put('P05_pressure_shoe',f'shoe_{int(seat)}_{a}',s=self.parts['P05_pressure_shoe'].shape.translate((0,t,16)),a=a,z=B+seat)
                ks=align_z(self.parts['P06_M4_knob'].shape,(0,1,0)).translate((147,t+29-self.p['knob_floor'],16))
                self.put('P06_M4_knob',f'knob_{int(seat)}_{a}',s=ks,a=a,z=B+seat)
                self.screw(f'clamp_{int(seat)}_{a}',(147,t+29,16),(0,-1,0),25,(147,15.5,16),hexhead=True,a=a,z=B+seat)
                # R1: a second STANDARD nut traps the 2.6 mm knob floor against the bolt head.
                # The pressure screw must be fully threaded: nut reaches within 2.6 mm of head.
                kp=(147,t+29-self.p['knob_floor'],16)
                hn=hexagon(7.,3.2,kp,(0,-1,0)).cut(cyl(2.,3.4,(kp[0],kp[1]+.1,kp[2]),(0,-1,0)))
                self.hard(f'clamp_{int(seat)}_{a}_retaining_nut',hn,a=a,z=B+seat)
                self.soft(f'fixed_pad_{int(seat)}_{a}',box(137,157,-2,-1,6,26),a=a,z=B+seat)
                self.soft(f'moving_pad_{int(seat)}_{a}',box(137,157,t-1,t,6,26),a=a,z=B+seat)
                if lower:self.soft(f'edge_pad_{a}',box(132,150,-2,12,4,6),a=a,z=B+seat)
                else:self.soft(f'cable_pad_{a}',box(91,121,.5,8.5,-1,0),a=a,z=B+seat)


def export(d,root):
    for sub in ('STL','STEP','validation','source'): (root/sub).mkdir(parents=True,exist_ok=True)
    stats=[]
    for p in d.parts.values():
        ps=print_shape(p)
        cq.exporters.export(ps,str(root/'STL'/f'{p.id}.stl'),tolerance=.075,angularTolerance=.15)
        cq.exporters.export(p.shape,str(root/'STEP'/f'{p.id}.step'))
        mm=trimesh.load_mesh(root/'STL'/f'{p.id}.stl')
        rec={'id':p.id,'title':p.title,'qty':p.qty,'bbox_mm':mm.extents.round(3).tolist(),'volume_mm3':float(mm.volume),
             'watertight':bool(mm.is_watertight),'winding_consistent':bool(mm.is_winding_consistent),'components':len(mm.split()),'cad_valid':p.shape.val().isValid(),
             'fits_256':bool(max(mm.extents)<256),'note':p.note}
        stats.append(rec);print(rec,flush=True)
        assert rec['watertight'] and rec['winding_consistent'] and rec['components']==1 and rec['fits_256']
    a=cq.Assembly(name='LPDA_V1_2_1_Fixed_printed_parts')
    for it in d.items:a.add(it['shape'],name=it['name'],color=cq.Color(.10,.28,.34) if 'knob' not in it['name'] else cq.Color(.10,.57,.58))
    a.export(str(root/'STEP'/'LPDA_V1_2_1_assembly.step'))
    for it in d.hardware:a.add(it['shape'],name=it['name'],color=cq.Color(.68,.70,.72))
    for it in d.pads:a.add(it['shape'],name=it['name'],color=cq.Color(.19,.22,.23))
    a.export(str(root/'STEP'/'LPDA_V1_2_1_hardware_assembly.step'))
    allit=d.items+d.hardware+d.pads;hits=[]
    for i,it in enumerate(allit):
        for jt in allit[i+1:]:
            v=cv(it['shape'],jt['shape'])
            if v>.025:hits.append({'a':it['name'],'b':jt['name'],'overlap_mm3':round(v,5)})
    report={'version':'V1.2.1 Fixed','parts':stats,'count':sum(p.qty for p in d.parts.values()),'screws':len(d.fasteners),
            'geometric_volume_cm3':sum(r['qty']*r['volume_mm3'] for r in stats)/1000,
            'assembly_overlaps':hits,'fasteners':d.fasteners,
            'limitations':['No physical assembly or load test','No printer/material certified strength','No RF pattern or cable-minimum-bend-radius qualification','No slice/G-code time yet']}
    (root/'validation'/'geometry_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (root/'source'/'parameters.json').write_text(json.dumps(d.p,indent=2))
    print('OVERLAPS',json.dumps(hits),flush=True)
    print('TOTALS',report['count'],report['screws'],report['geometric_volume_cm3'],flush=True)
    assert not hits, 'Unexpected final-state solid overlaps; do not release.'
    return report
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,default=ROOT);ap.add_argument('--params',type=pathlib.Path);ns=ap.parse_args()
    d=Design(json.loads(ns.params.read_text()) if ns.params else None).make();export(d,ns.out)
