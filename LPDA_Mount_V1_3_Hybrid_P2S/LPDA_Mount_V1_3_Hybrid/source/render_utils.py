#!/usr/bin/env python3
"""Explicit, limited geometry checks and CAD-derived illustrations."""
from pathlib import Path
import json,math,os
import numpy as np
import cadquery as cq
import trimesh
import vtk
from vtk.util.numpy_support import numpy_to_vtk,vtk_to_numpy
from PIL import Image,ImageDraw,ImageFont
from generate_v13 import *
ROOT=Path(__file__).resolve().parents[1]
C={'body':(.10,.27,.32),'lower':(.14,.38,.43),'knob':(.08,.59,.60),'metal':(.67,.70,.73),'pad':(.18,.21,.23),'pcb':(.10,.58,.42),'cable':(.06,.39,.83),'gold':(.71,.58,.30),'shoe':(.30,.48,.52)}
def tr(m,xyz):m=m.copy();m.apply_translation(xyz);return m
def rot(m,a):m=m.copy();m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(a),(0,0,1)));return m

def tube(points,r=2):
    p=vtk.vtkPoints()
    for x in points:p.InsertNextPoint(*[float(v) for v in x])
    ln=vtk.vtkPolyLine();ln.GetPointIds().SetNumberOfIds(len(points))
    for i in range(len(points)):ln.GetPointIds().SetId(i,i)
    cells=vtk.vtkCellArray();cells.InsertNextCell(ln);po=vtk.vtkPolyData();po.SetPoints(p);po.SetLines(cells)
    tf=vtk.vtkTubeFilter();tf.SetInputData(po);tf.SetRadius(r);tf.SetNumberOfSides(16);tf.CappingOn();tf.Update()
    tri=vtk.vtkTriangleFilter();tri.SetInputConnection(tf.GetOutputPort());tri.Update();out=tri.GetOutput()
    return trimesh.Trimesh(vtk_to_numpy(out.GetPoints().GetData()),vtk_to_numpy(out.GetPolys().GetData()).reshape(-1,4)[:,1:],process=True)

def render(items,path,cam,focal,scale,size=(1800,1350)):
    ren=vtk.vtkRenderer();ren.SetBackground(.965,.977,.98);ren.SetUseFXAA(True);ren.SetTwoSidedLighting(True)
    for m,c,op in items:
        pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.array(m.vertices),deep=True))
        cells=vtk.vtkCellArray();fa=np.hstack((np.full((len(m.faces),1),3),m.faces)).astype(np.int64)
        from vtk.util.numpy_support import numpy_to_vtkIdTypeArray
        cells.SetCells(len(m.faces),numpy_to_vtkIdTypeArray(fa.ravel(),deep=True))
        po=vtk.vtkPolyData();po.SetPoints(pts);po.SetPolys(cells)
        norms=vtk.vtkPolyDataNormals();norms.SetInputData(po);norms.SetFeatureAngle(35);norms.Update()
        mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(norms.GetOutputPort());act=vtk.vtkActor();act.SetMapper(mp)
        pr=act.GetProperty();pr.SetColor(*c);pr.SetOpacity(op);pr.SetAmbient(.29);pr.SetDiffuse(.68);pr.SetSpecular(.14);pr.SetSpecularPower(22);ren.AddActor(act)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(*size);win.SetMultiSamples(0);win.AddRenderer(ren)
    ca=ren.GetActiveCamera();ca.SetPosition(*cam);ca.SetFocalPoint(*focal);ca.SetViewUp(0,0,1);ca.ParallelProjectionOn();ca.SetParallelScale(scale);ren.ResetCameraClippingRange();win.Render()
    image=vtk.vtkWindowToImageFilter();image.SetInput(win);image.SetInputBufferTypeToRGB();image.ReadFrontBufferOff();image.Update()
    w=vtk.vtkPNGWriter();w.SetFileName(str(path));w.SetInputConnection(image.GetOutputPort());w.Write();win.Finalize()
from font_utils import local_font
def font(n,b=False):return local_font(n,b)
def panel(raw,path,title,subtitle,footer):
    im=Image.open(raw).convert('RGB');w,h=im.size;out=Image.new('RGB',(w,h+170),'#f6fafb');out.paste(im,(0,105));dr=ImageDraw.Draw(out)
    dr.text((32,18),title,font=font(31,True),fill='#173e4b');dr.text((32,62),subtitle,font=font(17),fill='#526e77')
    dr.text((32,h+126),footer,font=font(14),fill='#526e77');out.save(path)

