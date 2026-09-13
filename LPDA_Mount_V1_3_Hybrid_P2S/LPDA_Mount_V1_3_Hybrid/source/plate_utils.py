#!/usr/bin/env python3
"""Reproducible neutral 3MF plates, BOM and review. Does not slice or produce G-code."""
from pathlib import Path
import json,math,zipfile,html,hashlib,io,base64
import numpy as np,trimesh,shapely
from shapely.geometry import Polygon
from PIL import Image,ImageDraw,ImageFont
from generate_v13 import *
ROOT=Path(__file__).resolve().parents[1]
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
def footprint(m):
    t=m.vertices[m.faces,:2]
    ar=np.abs((t[:,1,0]-t[:,0,0])*(t[:,2,1]-t[:,0,1])-(t[:,2,0]-t[:,0,0])*(t[:,1,1]-t[:,0,1]))
    return shapely.unary_union(shapely.polygons(t[ar>1e-7]))
def load(id):return trimesh.load_mesh(ROOT/'STL'/f'{id}.stl')
def posed(m,ang,x,y):
    m=m.copy();m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(ang),(0,0,1)));m.apply_translation(-m.bounds[0]);m.apply_translation((x,y,0));return m
def write3mf(path,entries):
    objects=[];build=[]
    for i,(name,m) in enumerate(entries,1):
        vs=''.join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x,y,z in m.vertices)
        fs=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in m.faces)
        objects.append(f'<object id="{i}" name="{html.escape(name)}" type="model"><mesh><vertices>{vs}</vertices><triangles>{fs}</triangles></mesh></object>');build.append(f'<item objectid="{i}"/>')
    model=f'<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xmlns="{NS}"><metadata name="Title">LPDA V1.3 Hybrid | GEOMETRY ONLY | select P2S/PETG explicitly</metadata><resources>'+''.join(objects)+'</resources><build>'+''.join(build)+'</build></model>'
    ct='<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rel='<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('[Content_Types].xml',ct);z.writestr('_rels/.rels',rel);z.writestr('3D/3dmodel.model',model)
    # Read back geometries with an independent parser.
    sc=trimesh.load(path,force='scene');assert len(sc.geometry)==len(entries),(path,len(sc.geometry),len(entries))
    polys=[footprint(m) for _,m in entries];clear=[]
    for i,p in enumerate(polys):
        assert p.bounds[0]>=3 and p.bounds[1]>=3 and p.bounds[2]<=253 and p.bounds[3]<=253
        for j in range(i):
            dist=p.distance(polys[j]);assert dist>1.,(path,entries[i][0],entries[j][0],dist)
            clear.append(dist)
    info={'file':path.name,'objects':len(entries),'min_footprint_gap_mm':min(clear) if clear else None,
          'bbox_mm':sc.bounds.tolist(),'geometry_only':True,'no_gcode':True,
          'entries':[{'name':n,'bbox_mm':m.bounds.round(3).tolist()} for n,m in entries]}
    return info

def draw_plate(path,entries,title):
    S=1100;scale=3.7;ox=76;oy=88
    im=Image.new('RGB',(S,1160),'#f7fafb');dr=ImageDraw.Draw(im)
    from font_utils import local_font
    f=lambda n:local_font(n)
    dr.text((45,18),title,font=f(27),fill='#183d48')
    dr.rectangle((ox,oy,ox+256*scale,oy+256*scale),fill='#e9eef0',outline='#9daeb3',width=2)
    colors=['#275a68','#39838a','#719a9f','#4f7782']
    for i,(name,m) in enumerate(entries):
        p=footprint(m);geos=list(p.geoms) if p.geom_type=='MultiPolygon' else [p]
        for pol in geos:
            dr.polygon([(ox+x*scale,oy+(256-y)*scale) for x,y in pol.exterior.coords],fill=colors[i%len(colors)],outline='#1f4753')
            for interior in pol.interiors:dr.polygon([(ox+x*scale,oy+(256-y)*scale) for x,y in interior.coords],fill='#e9eef0')
        if len(entries)<8:
            x,y=p.representative_point().coords[0];dr.text((ox+x*scale-25,oy+(256-y)*scale),name[:3],font=f(21),fill='white')
    dr.text((45,1060),'256 x 256 mm bed | XY silhouettes | print by layer, not by object',font=f(18),fill='#385760')
    dr.text((45,1100),'Geometry only: select the P2S / nozzle / material before slicing.',font=f(18),fill='#385760');im.save(path)

