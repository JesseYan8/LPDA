from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def crop(im):
    a=np.asarray(im.convert('RGB'));bg=np.array([246,249,250]);mask=np.max(abs(a.astype(int)-bg),axis=2)>28
    yy,xx=np.where(mask);return im.crop((max(0,xx.min()-22),max(0,yy.min()-22),min(im.width,xx.max()+23),min(im.height,yy.max()+23)))
from font_utils import local_font
def f(n,b=False):return local_font(n,b)
im=Image.new('RGB',(2100,1560),'#f5f9fa');dr=ImageDraw.Draw(im)
dr.text((45,22),'LPDA V1.3  /  HYBRID MOUNT',font=f(40,True),fill='#173c47')
dr.text((45,83),'Four nylon fasteners per PCB + retained lower support | Bambu Lab P2S',font=f(22),fill='#55727a')
for file,rect in [('assembly_raw.png',(25,190,1190,1370)),('sector_raw.png',(1245,135,2070,920)),('cassette_raw.png',(1245,1000,2070,1400))]:
    x0,y0,x1,y1=rect;s=crop(Image.open(ROOT/'preview'/file));s.thumbnail((x1-x0,y1-y0));im.paste(s,(x0+(x1-x0-s.width)//2,y0+(y1-y0-s.height)//2))
dr.text((1245,940),'Lower support stays; upper pressure clamp is replaced.',font=f(18),fill='#355b65')
dr.text((45,1450),'18 printed parts | Existing mast, base and lower clamps can be reused',font=f(24,True),fill='#224b56')
dr.text((45,1502),'PCB and cable models are illustrative, not measured. Real STL / STEP; physical first-fit and RF checks still required.',font=f(19),fill='#5c7880')
im.save(ROOT/'preview'/'LPDA_V1_3_overview.png')
