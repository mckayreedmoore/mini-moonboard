import cadquery as cq
from PIL import Image

from mini_moonboard.raster import render


def test_raster_occlusion_does_not_depend_on_part_order(tmp_path):
    far=cq.Workplane("XY").box(20,20,20).val()
    near=far.translate((-40,45,6))
    shapes=[(far,(0,0,255)),(near,(255,0,0))]
    first,second=tmp_path/"first.png",tmp_path/"second.png"
    render(shapes,first,size=(240,200))
    render(shapes[::-1],second,size=(240,200))
    assert first.read_bytes()==second.read_bytes()
    red,green,blue=Image.open(first).getpixel((120,100))
    assert red>0 and green==blue==0
