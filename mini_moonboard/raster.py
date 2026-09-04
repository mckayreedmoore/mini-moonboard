"""Deterministic orthographic CAD raster with per-pixel depth testing."""
import numpy as np
from PIL import Image


def render(solids, path, size=(1280,960)):
    """Render (shape, RGB) pairs without painter-order transparency artifacts."""
    camera=np.array([4.,4.5,0.6]); camera/=np.linalg.norm(camera)
    right=np.cross([0.,0.,1.],camera); right/=np.linalg.norm(right)
    up=np.cross(camera,right)
    matrix=np.array([right,up,camera]).T
    meshes=[]
    for shape,color in solids:
        vertices,triangles=shape.tessellate(.5)
        vertices=np.array([v.toTuple() for v in vertices])
        vertices[:,0]*=-1  # same climber-left convention as interactive viewer
        meshes.append((vertices@matrix,np.array(triangles),np.array(color)))
    all_vertices=np.concatenate([v for v,_,_ in meshes])
    low,high=all_vertices[:,:2].min(axis=0),all_vertices[:,:2].max(axis=0)
    width,height=size
    scale=min((width-120)/(high[0]-low[0]),(height-100)/(high[1]-low[1]))
    centre=(low+high)/2
    pixels=np.full((height,width,3),[244,241,234],dtype=np.uint8)
    depth=np.full((height,width),-np.inf)
    light=np.array([-.3,.6,1.]);light/=np.linalg.norm(light)
    for vertices,triangles,color in meshes:
        screen=vertices.copy()
        screen[:,0]=(vertices[:,0]-centre[0])*scale+width/2
        screen[:,1]=height/2-(vertices[:,1]-centre[1])*scale
        for tri in triangles:
            a,b,c=screen[tri]
            lo=np.maximum(np.floor(np.minimum.reduce([a[:2],b[:2],c[:2]])).astype(int),[0,0])
            hi=np.minimum(np.ceil(np.maximum.reduce([a[:2],b[:2],c[:2]])).astype(int),[width-1,height-1])
            if np.any(hi<lo):
                continue
            denom=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(denom)<1e-9:
                continue
            yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
            xx=xx+.5;yy=yy+.5
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denom
            v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denom
            w=1-u-v
            z=u*a[2]+v*b[2]+w*c[2]
            area=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
            mask=(u>=-1e-8)&(v>=-1e-8)&(w>=-1e-8)&(z>area)
            p,q,r=vertices[tri]
            n=np.cross(q-p,r-p)
            magnitude=np.linalg.norm(n)
            shade=.65+.35*abs(n@light/magnitude) if magnitude else 1
            pixels[lo[1]:hi[1]+1,lo[0]:hi[0]+1][mask]=(color*shade).astype(np.uint8)
            area[mask]=z[mask]
    Image.fromarray(pixels).save(path)
