"""Fonts + text drawing (tracking, hard shadow, reveals)."""
import os, glob, shutil, subprocess, math
import cairocffi as cairo
from .core import hexc, set_col

_HERE = os.path.dirname(os.path.abspath(__file__))

def register_fonts():
    """Copy the renamed DT* fonts into ~/.fonts and refresh fontconfig once."""
    dst = os.path.expanduser('~/.fonts/dtengine')
    src = glob.glob(os.path.join(_HERE, 'fonts', 'dt', '*.ttf'))
    os.makedirs(dst, exist_ok=True)
    changed = False
    for f in src:
        d = os.path.join(dst, os.path.basename(f))
        if not os.path.exists(d) or os.path.getsize(d) != os.path.getsize(f):
            shutil.copy(f, d); changed = True
    if changed:
        subprocess.run(['fc-cache', '-f', dst], check=False, capture_output=True)

register_fonts()

# Font keys -> fontconfig families (renamed static instances, see fonts/dt)
FONTS = {
    'xb': 'DTRaleway ExtraBold',   # v2 titles, pills
    'black': 'DTRaleway Black',    # stamps, paper
    'bold': 'DTRaleway Bold',      # wide-tracked labels
    'semi': 'DTRaleway SemiBold',
    'reg': 'DTRaleway Regular',    # callout body
    'archivo': 'DTArchivo Black',  # v1 punchlines
    'poppins': 'DTPoppins Medium',
    'poppins_sb': 'DTPoppins SemiBold',
    'marker': 'DTMarker',          # polaroid captions
}

def set_font(ctx, font='xb', size=48):
    ctx.select_font_face(FONTS.get(font, font), cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)

def measure(ctx, s, font='xb', size=48, track=0.0):
    """Return (width, ascent, descent) of string with tracking (em units)."""
    set_font(ctx, font, size)
    fe = ctx.font_extents()
    if track == 0:
        w = ctx.text_extents(s)[4]
    else:
        w = sum(ctx.text_extents(ch)[4] for ch in s) + track * size * max(0, len(s) - 1)
    return w, fe[0], fe[1]

def cap_height(ctx, font='xb', size=48):
    set_font(ctx, font, size)
    return -ctx.text_extents('H')[1]

def text_path(ctx, s, x, y, font='xb', size=48, track=0.0, align='left'):
    """Add text outline to the current path. y is the BASELINE. align left|center|right."""
    w, _, _ = measure(ctx, s, font, size, track)
    if align == 'center': x -= w / 2
    elif align == 'right': x -= w
    if track == 0:
        ctx.move_to(x, y); ctx.text_path(s)
    else:
        cx = x
        for ch in s:
            ctx.move_to(cx, y); ctx.text_path(ch)
            cx += ctx.text_extents(ch)[4] + track * size
    return w

def draw_text(ctx, s, x, y, font='xb', size=48, color='#F2F0EB', track=0.0, align='left',
              shadow=True, shadow_off=None, shadow_col=(0, 0, 0, 0.55), alpha=1.0, outline=None):
    """Text with the house tight hard shadow. Returns width."""
    if shadow:
        so = shadow_off if shadow_off is not None else max(1.5, size * 0.045)
        ctx.new_path(); text_path(ctx, s, x + so * 0.6, y + so, font, size, track, align)
        c = hexc(shadow_col); ctx.set_source_rgba(c[0], c[1], c[2], c[3] * alpha); ctx.fill()
    ctx.new_path(); w = text_path(ctx, s, x, y, font, size, track, align)
    if outline:
        oc, ow = outline
        ctx.set_line_width(ow); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        set_col(ctx, oc, alpha); ctx.stroke_preserve()
    set_col(ctx, color, alpha); ctx.fill()
    return w

def draw_text_reveal(ctx, s, x, y, k, font='xb', size=48, color='#F2F0EB', track=0.0,
                     align='left', mode='letters', shadow=True):
    """Progressive reveal, k in 0..1. mode 'letters' = per-letter quick fade-in
    (chapter title letter reveal), 'wipe' = left-to-right mask wipe."""
    w, asc, desc = measure(ctx, s, font, size, track)
    x0 = x - (w / 2 if align == 'center' else w if align == 'right' else 0)
    if mode == 'wipe':
        ctx.save(); ctx.rectangle(x0 - 10, y - asc - 10, (w + 20) * k, asc + desc + 30); ctx.clip()
        draw_text(ctx, s, x0, y, font, size, color, track, 'left', shadow)
        ctx.restore(); return w
    n = len(s); cx = x0
    set_font(ctx, font, size)
    for i, ch in enumerate(s):
        a = max(0.0, min(1.0, k * (n + 2) - i))   # each letter fades over ~1/n of k
        adv = ctx.text_extents(ch)[4]
        if a > 0 and ch != ' ':
            draw_text(ctx, ch, cx, y + (1 - a) * size * 0.08, font, size, color, 0, 'left', shadow, alpha=a)
            set_font(ctx, font, size)
        cx += adv + track * size
    return w

def wrap(ctx, s, maxw, font='reg', size=28):
    words = s.split(); lines = []; cur = ''
    for wd in words:
        test = (cur + ' ' + wd).strip()
        if measure(ctx, test, font, size)[0] > maxw and cur:
            lines.append(cur); cur = wd
        else:
            cur = test
    if cur: lines.append(cur)
    return lines
