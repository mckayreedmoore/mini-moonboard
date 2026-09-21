"""Unselected end-angle layout with two relocated gusset bolts; no export."""
from dataclasses import replace

from . import backing_end_trial as end
from . import box_frame as b
from . import wide_frame as frame

SHIFT_N_MM = 45.
MOVED = ("timber_base_left_1", "timber_base_right_1")


def connections():
    return tuple(replace(c, start=c.start+b.normal()*SHIFT_N_MM,
                         product_status=c.product_status+"; unselected 45mm rear-normal relocation")
                 if c.name in MOVED else c for c in frame.connections())+tuple(end.screws())
