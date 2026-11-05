"""Rendering: Timeline of Shots -> frames -> ffmpeg (H.264).

    from engine.render import Timeline
    tl = Timeline(shots)                      # shots laid end to end
    tl.render('out.mp4', scale=0.5)           # 960x540 preview
    tl.render('out.mp4', t_start=10, t_end=14) # time range
    tl.still(12.3, 'frame.png', scale=1.0)    # single frame
CLI:  python -m engine.render scenes.act1 out.mp4 --scale 0.5 --start 0 --end 20 --jobs 2
"""
import os, sys, time, math, subprocess, importlib, tempfile, argparse
import multiprocessing as mp
import cairocffi as cairo
from .core import W, H, FPS
from . import transitions as TR

class Timeline:
    def __init__(self, shots, fps=FPS):
        self.shots = list(shots); self.fps = fps
        # Shots may pin a global start (shot.abs_start, e.g. a word-locked cut):
        # the previous shot is stretched/trimmed so the cut lands exactly there.
        for i, s in enumerate(self.shots):
            a = getattr(s, 'abs_start', None)
            if a is not None and i > 0:
                prev_start = sum(x.dur for x in self.shots[:i - 1])
                self.shots[i - 1].dur = max(1 / fps, a - prev_start)
        t = 0.0
        if self.shots and getattr(self.shots[0], 'abs_start', None):
            t = 0.0
        for s in self.shots:
            s.start = t; t += s.dur
        self.duration = t

    def shot_at(self, T):
        for i, s in enumerate(self.shots):
            if s.start <= T < s.start + s.dur: return i
        return len(self.shots) - 1

    def draw(self, ctx, T):
        """Draw global time T (seconds) into ctx (already scaled to design units)."""
        i = self.shot_at(T)
        cur = self.shots[i]
        nxt = self.shots[i + 1] if i + 1 < len(self.shots) else None
        lt = T - cur.start
        # transition into the next shot (its trans_in straddles the cut)
        if nxt is not None and nxt.trans_in:
            kind, d = TR.parse(nxt.trans_in)
            if lt > cur.dur - d / 2 and TR.straddles(kind):
                TR.draw(ctx, kind, d, cur, nxt, lt - cur.dur, lt, lt - cur.dur); return
        if cur.trans_in and i > 0:
            kind, d = TR.parse(cur.trans_in)
            if lt < d / 2 and TR.straddles(kind):
                prev = self.shots[i - 1]
                TR.draw(ctx, kind, d, prev, cur, lt, prev.dur + lt, lt); return
            if kind == 'flash' and lt < d:
                cur.render(ctx, lt); TR.flash(ctx, lt, d); return
        cur.render(ctx, lt)

    # ------------------------------------------------------------------ outputs
    def frame_surface(self, T, scale=1.0, surf=None):
        w, h = int(W * scale), int(H * scale)
        if surf is None: surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        ctx = cairo.Context(surf)
        ctx.set_source_rgb(0, 0, 0); ctx.paint()
        ctx.scale(scale, scale)
        self.draw(ctx, T)
        surf.flush()
        return surf

    def still(self, T, path, scale=1.0):
        s = self.frame_surface(T, scale)
        s.write_to_png(path); return path

    def render(self, out, scale=0.5, t_start=0.0, t_end=None, jobs=1, crf=20, preset='veryfast', quiet=True):
        t_end = self.duration if t_end is None else min(t_end, self.duration)
        n0 = int(round(t_start * self.fps)); n1 = int(round(t_end * self.fps))
        os.makedirs(os.path.dirname(os.path.abspath(out)) or '.', exist_ok=True)
        t0 = time.time()
        if jobs <= 1 or n1 - n0 < 60:
            _encode_range(self, n0, n1, out, scale, crf, preset)
        else:
            # split into contiguous chunks, one ffmpeg per worker, then concat (-c copy)
            tmpd = tempfile.mkdtemp(prefix='dtr_', dir=os.path.dirname(os.path.abspath(out)))
            edges = [n0 + (n1 - n0) * k // jobs for k in range(jobs + 1)]
            parts = [os.path.join(tmpd, f'p{k:02d}.mp4') for k in range(jobs)]
            ctxm = mp.get_context('fork')
            ps = [ctxm.Process(target=_encode_range, args=(self, edges[k], edges[k + 1], parts[k], scale, crf, preset))
                  for k in range(jobs)]
            for p in ps: p.start()
            for p in ps: p.join()
            lst = os.path.join(tmpd, 'list.txt')
            with open(lst, 'w') as f:
                for p in parts: f.write(f"file '{p}'\n")
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                            '-movflags', '+faststart', out], check=True)
            for p in parts: os.remove(p)
            os.remove(lst); os.rmdir(tmpd)
        dt = time.time() - t0
        n = n1 - n0
        if not quiet or True:
            print(f'rendered {n} frames ({n / self.fps:.1f}s) at {int(W*scale)}x{int(H*scale)} in {dt:.1f}s '
                  f'= {n / max(dt, 1e-6):.2f} fps -> {out}', file=sys.stderr)
        return n / max(dt, 1e-6)

def _encode_range(tl, n0, n1, out, scale, crf, preset):
    w, h = int(W * scale), int(H * scale)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{w}x{h}',
           '-r', str(tl.fps), '-i', '-', '-c:v', 'libx264', '-preset', preset, '-crf', str(crf),
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    stride = surf.get_stride()
    for n in range(n0, n1):
        tl.frame_surface(n / tl.fps, scale, surf)
        buf = bytes(surf.get_data())
        if stride != w * 4:
            buf = b''.join(buf[r * stride:r * stride + w * 4] for r in range(h))
        p.stdin.write(buf)
    p.stdin.close(); p.wait()

def load_scene_shots(modname, words=None):
    m = importlib.import_module(modname)
    return m.build(words)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('modules', nargs='+', help='scene modules (each exposes build(words)->[Shot]); last arg is output')
    ap.add_argument('--scale', type=float, default=0.5)
    ap.add_argument('--start', type=float, default=0.0)
    ap.add_argument('--end', type=float, default=None)
    ap.add_argument('--jobs', type=int, default=1)
    ap.add_argument('--words', default=None, help='words.json with word timings')
    ap.add_argument('--still', type=float, default=None, help='render one frame at this time to OUT (png)')
    a = ap.parse_args()
    *mods, out = a.modules
    words = None
    if a.words:
        import json; words = json.load(open(a.words))
    shots = []
    for m in mods: shots += load_scene_shots(m, words)
    tl = Timeline(shots)
    if a.still is not None: tl.still(a.still, out, a.scale)
    else: tl.render(out, a.scale, a.start, a.end, a.jobs)

if __name__ == '__main__':
    main()
