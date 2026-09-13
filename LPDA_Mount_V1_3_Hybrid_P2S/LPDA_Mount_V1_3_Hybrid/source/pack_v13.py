#!/usr/bin/env python3
from plate_utils import *
from shapely import affinity
from scipy.signal import fftconvolve
from scipy.ndimage import binary_dilation
from itertools import permutations
import random

def pack_raster(ids, tries=80):
    """Conservative 2-mm occupancy grid; exact polygons are checked at the end."""
    step=2.;N=123 # effective 246-mm square, starts at 5 mm
    cache={}
    for pid in set(ids):
        for a in (0,90,180,270):
            m=posed(load(pid),a,0,0);p=footprint(m).buffer(3.3)
            # Grid offset (4,4) inside each item footprint allocation.
            nx=math.ceil((m.bounds[1,0]+8)/step);ny=math.ceil((m.bounds[1,1]+8)/step)
            xx,yy=np.meshgrid(np.arange(nx)*step-4+1,np.arange(ny)*step-4+1)
            mask=shapely.intersects_xy(p,xx,yy)
            cache[(pid,a)]=(mask,m)
    best=None;bestn=0;rng=random.Random(713)
    for k in range(tries):
        order=list(ids)
        if k: rng.shuffle(order)
        occ=np.zeros((N,N),dtype=np.uint8);en=[]
        for pid in order:
            options=[]
            for a in (0,90,180,270):
                mask,m=cache[(pid,a)];ny,nx=mask.shape
                if ny>N or nx>N:continue
                costs=fftconvolve(occ.astype(float),mask[::-1,::-1].astype(float),mode='valid')
                ys,xs=np.where(costs<.25)
                if not len(xs):continue
                # Prefer compact placement with a variable sweep direction to avoid poor nesting.
                if k%3==0:scores=(ys+ny)*N + (xs+nx)
                elif k%3==1:scores=np.maximum(ys+ny,xs+nx)*N+ys+xs
                else:scores=(xs+nx)*N+ys+ny
                q=np.argmin(scores);x,y=int(xs[q]),int(ys[q]);options.append((float(scores[q]),a,x,y))
            if not options:break
            _,a,x,y=min(options);mask,m=cache[(pid,a)];ny,nx=mask.shape
            occ[y:y+ny,x:x+nx]|=mask.astype(np.uint8)
            # include the 4-mm raster padding at the outside, resulting true bound >=9 mm
            en.append((pid+f'_{sum(n.startswith(pid) for n,_ in en)+1}',posed(load(pid),a,5+x*step+4,5+y*step+4)))
        if len(en)>bestn:best,bestn=en,len(en)
        if len(en)==len(ids):return en
    print('raster best',bestn,'/',len(ids),flush=True);return None

def run():
    d=Hybrid(json.loads((ROOT/'source'/'parameters.json').read_text())).make()
    # Two small sacrificial fitting coupons are not load-bearing components.
    carrier=d.parts['P01_upper_carrier'].shape.intersect(box(62,132,-23,-17,4,38))
    p=Part('T03_carrier_fit','small carrier interface coupon',carrier,1,(('X',90),))
    cq.exporters.export(print_shape(p),str(ROOT/'STL'/'T03_carrier_fit.stl'))
    rec=json.loads((ROOT/'reference'/'v121_nesting.json').read_text())
    en=[]
    for i,key in enumerate(('first','second')):en.append(('P02_lower_half_'+str(i+1),posed(load('P02_lower_half'),rec[key+'_angle'],*rec[key+'_xy_mm'])))
    plates=[('FULL_01_LOWER_REUSED',en)]
    # Try to put both new upper halves and all four cassettes on one conservative plate.
    en=pack_raster(['P01_upper_carrier']*2+['P07_four_hole_cassette']*4,90)
    if en:
        plates.append(('FULL_02_UPPER_AND_CASSETTES',en))
    else:
        en=[]
        for i,key in enumerate(('first','second')):en.append(('P01_upper_carrier_'+str(i+1),posed(load('P01_upper_carrier'),rec[key+'_angle'],*rec[key+'_xy_mm'])))
        plates.append(('FULL_02_UPPER',en))
        en=[('P07_four_hole_cassette_'+str(i+1),posed(load('P07_four_hole_cassette'),0,6+124*(i%2),6+86*(i//2))) for i in range(4)]
        plates.append(('FULL_04_CASSETTES',en))
    en=[('P04_anchor_base_1',posed(load('P04_anchor_base'),0,6,6)),('P03_fixed_mast_1',posed(load('P03_fixed_mast'),0,125,125))]
    for i,(x,y) in enumerate(((7,7),(33,7),(103,7),(129,7)),1):en.append((f'P05_pressure_shoe_{i}',posed(load('P05_pressure_shoe'),0,x,y)))
    for i,(x,y) in enumerate(((225,29),(117,33),(147,33),(177,33)),1):en.append((f'P06_M4_knob_{i}',posed(load('P06_M4_knob'),0,x,y)))
    plates.append(('FULL_03_REUSED_MAST_BASE_SMALL',en))
    quick=[('P07_four_hole_cassette_1',posed(load('P07_four_hole_cassette'),0,8,8)),('T01_hole_pattern',posed(load('T01_hole_pattern'),0,140,8)),('T03_carrier_fit',posed(load('T03_carrier_fit'),0,8,106)),('T02_M4_slot_fit',posed(load('T02_M4_slot_fit'),0,140,78))]
    plates.append(('FIRST_FIT_CASSETTE_NOT_LOAD_TEST',quick))
    plates.append(('TINY_HOLE_PATTERN_ONLY',[('T01_hole_pattern',posed(load('T01_hole_pattern'),0,10,10))]))
    checks=[]
    for name,en in plates:
        checks.append(write3mf(ROOT/'plates'/f'{name}.3mf',en));draw_plate(ROOT/'preview'/f'{name}.png',en,name)
    formal=[p for p in checks if p['file'].startswith('FULL')]
    assert sum(p['objects'] for p in formal)==18
    (ROOT/'validation'/'plates.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
    print([(p['file'],p['objects'],p['min_footprint_gap_mm']) for p in checks],flush=True)

if __name__=='__main__':run()
