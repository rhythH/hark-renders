"""Ready-made shot builders for recurring house beats."""
import math
from .core import Shot, Camera, StaticCamera, K, W, H, PAL
from . import plates as P
from .ui import ChapterTitle
from .chars.orca import Orca, OrcaBelow

def chapter_shot(title, subtitle, n, total=6, dur=3.6, plate=None, background=None, icons=None, labels=None):
    """Chapter card: dip-to-black in (0.7 s), background acting out the title,
    title/subtitle/navigator overlay. `background` = list of Elements (world).
    Default background: an orca silhouette gliding overhead (from below)."""
    s = Shot(dur, plate=plate or P.Underwater(depth=0.35, surface=True), camera=Camera(push=0.6, drift=(6, 0)),
             name=f'chapter{n}', trans_in=('dip', 0.7))
    if background is None:
        background = [OrcaBelow(pos=K((0, (560, 150)), (dur, (980, 120), 'linear')), scale=1.55, rot=-5, layer='back')]
    for e in background: s.add(e)
    s.add(ChapterTitle(title, subtitle, n, total, icons=icons, labels=labels, t0=0.3))
    return s
