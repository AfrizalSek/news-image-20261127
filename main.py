#!/usr/bin/env python3
"""THE WORLD -- Friday 27 November 2026.

One newspaper page summing up the day's world news, drawn in pure
standard-library Python. The bitmap, the serif type (a minimal TrueType
rasterizer over the bundled Liberation Serif fonts) and the PNG writer
are all hand-built, so two runs of the program produce byte-identical
output. 42 stories, 10 regions, 15 drawn scenes.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (253, 252, 247)
INK = (22, 22, 22)
SOFT = (92, 90, 82)
RED = (176, 30, 36)
BLUE = (28, 68, 138)
SKY = (212, 229, 238)
LAND = (214, 210, 194)
GOLD = (198, 148, 32)
GREEN = (38, 120, 70)
ORANGE = (214, 110, 30)
RULE = (180, 176, 166)
DARK = (32, 34, 44)
CREAM = (245, 240, 224)

buf = bytearray(W * H * 3)
for _i in range(W * H):
    buf[_i * 3] = PAPER[0]
    buf[_i * 3 + 1] = PAPER[1]
    buf[_i * 3 + 2] = PAPER[2]


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        o = (y * W + x) * 3
        buf[o] = c[0]
        buf[o + 1] = c[1]
        buf[o + 2] = c[2]


def fill(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        o = (yy * W + x0) * 3
        buf[o:o + len(row)] = row


def hbar(x, y, w, c, t=1):
    fill(x, y, w, t, c)


def vbar(x, y, h, c, t=1):
    fill(x, y, t, h, c)


def border(x, y, w, h, c, t=1):
    hbar(x, y, w, c, t)
    hbar(x, y + h - t, w, c, t)
    vbar(x, y, h, c, t)
    vbar(x + w - t, y, h, c, t)


def seg(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        put(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def dot(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        d = yy - cy
        if abs(d) > r:
            continue
        dx = int(math.sqrt(r * r - d * d))
        fill(cx - dx, yy, dx * 2 + 1, 1, c)


def circ(cx, cy, r, c):
    for a in range(360):
        t = a * math.pi / 180.0
        put(cx + int(r * math.cos(t)), cy + int(r * math.sin(t)), c)


def tri(x0, y0, x1, y1, x2, y2, c):
    pts = sorted([(y0, x0), (y1, x1), (y2, x2)])
    (ya, xa), (yb, xb), (yc, xc) = pts
    for y in range(ya, yc + 1):
        if y < yb:
            f = (y - ya) / (yb - ya) if yb != ya else 0.0
            xl = xa + (xb - xa) * f
            f2 = (y - ya) / (yc - ya) if yc != ya else 0.0
            xr = xa + (xc - xa) * f2
        else:
            f = (y - yb) / (yc - yb) if yc != yb else 0.0
            xl = xb + (xc - xb) * f
            f2 = (y - ya) / (yc - ya) if yc != ya else 0.0
            xr = xa + (xc - xa) * f2
        if xl > xr:
            xl, xr = xr, xl
        fill(int(xl), y, int(xr) - int(xl) + 1, 1, c)


def ngon(points, c):
    ys = [p[1] for p in points]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)


class TTFont:
    def __init__(self, path):
        self.data = open(path, 'rb').read()
        d = self.data
        n = struct.unpack('>H', d[4:6])[0]
        self.tabs = {}
        for i in range(n):
            off = 12 + i * 16
            tag = d[off:off + 4].decode('latin1')
            _chk, toff, tlen = struct.unpack('>III', d[off + 4:off + 16])
            self.tabs[tag] = (toff, tlen)
        o, _ = self.tabs['head']
        self.upm = struct.unpack('>H', d[o + 18:o + 20])[0]
        self.loc_fmt = struct.unpack('>h', d[o + 50:o + 52])[0]
        o, _ = self.tabs['maxp']
        self.num_glyphs = struct.unpack('>H', d[o + 4:o + 6])[0]
        o, _ = self.tabs['hhea']
        self.asc = struct.unpack('>h', d[o + 4:o + 6])[0]
        self.desc = struct.unpack('>h', d[o + 6:o + 8])[0]
        self.num_hm = struct.unpack('>H', d[o + 34:o + 36])[0]
        # OS/2 cap height
        self.cap_h = None
        if 'OS/2' in self.tabs:
            o, _ = self.tabs['OS/2']
            try:
                self.cap_h = struct.unpack('>h', d[o + 88:o + 90])[0]
            except struct.error:
                pass
        if not self.cap_h:
            self.cap_h = int(self.upm * 0.7)
        self._load_cmap()
        self._load_kern()
        self._glyph_cache = {}   # gid -> (contours, xMin, yMin, xMax, yMax)
        self._flat_cache = {}    # gid -> flat segments in font units

    # ---- cmap format 4 ----
    def _load_cmap(self):
        d = self.data
        o, _ = self.tabs['cmap']
        nsub = struct.unpack('>H', d[o + 2:o + 4])[0]
        sub = None
        for i in range(nsub):
            plat, enc, so = struct.unpack('>HHI', d[o + 4 + i * 8:o + 12 + i * 8])
            fmt = struct.unpack('>H', d[o + so:o + so + 2])[0]
            if fmt == 4 and (plat, enc) == (3, 1):
                sub = o + so
                break
        if sub is None:
            for i in range(nsub):
                plat, enc, so = struct.unpack('>HHI', d[o + 4 + i * 8:o + 12 + i * 8])
                fmt = struct.unpack('>H', d[o + so:o + so + 2])[0]
                if fmt == 4:
                    sub = o + so
                    break
        self.cmap = {}
        seg_count = struct.unpack('>H', d[sub + 6:sub + 8])[0] // 2
        end_off = sub + 14
        start_off = end_off + 2 * seg_count + 2
        delta_off = start_off + 2 * seg_count
        range_off = delta_off + 2 * seg_count
        for i in range(seg_count):
            end = struct.unpack('>H', d[end_off + 2 * i:end_off + 2 * i + 2])[0]
            start = struct.unpack('>H', d[start_off + 2 * i:start_off + 2 * i + 2])[0]
            delta = struct.unpack('>h', d[delta_off + 2 * i:delta_off + 2 * i + 2])[0]
            ro = struct.unpack('>H', d[range_off + 2 * i:range_off + 2 * i + 2])[0]
            if start == 0xFFFF and end == 0xFFFF:
                break
            for cp in range(start, end + 1):
                if ro == 0:
                    gid = (cp + delta) % 65536
                else:
                    addr = range_off + 2 * i + ro + 2 * (cp - start)
                    gid = struct.unpack('>H', d[addr:addr + 2])[0]
                    if gid:
                        gid = (gid + delta) % 65536
                if gid:
                    self.cmap[cp] = gid

    # ---- kern format 0 ----
    def _load_kern(self):
        self.kern = {}
        if 'kern' not in self.tabs:
            return
        d = self.data
        o, _ = self.tabs['kern']
        ntab = struct.unpack('>H', d[o + 2:o + 4])[0]
        p = o + 4
        for _ in range(ntab):
            _ver, length, fmt = struct.unpack('>HHH', d[p:p + 6])
            if fmt == 0:
                npairs = struct.unpack('>H', d[p + 6:p + 8])[0]
                q = p + 14
                for _i in range(npairs):
                    left, right, val = struct.unpack('>HHh', d[q:q + 6])
                    self.kern[(left, right)] = val
                    q += 6
            p += length

    def gid(self, ch):
        return self.cmap.get(ord(ch), 0)

    def advance(self, gid):
        d = self.data
        o, _ = self.tabs['hmtx']
        if gid < self.num_hm:
            return struct.unpack('>H', d[o + gid * 4:o + gid * 4 + 2])[0]
        return struct.unpack('>H', d[o + (self.num_hm - 1) * 4:o + (self.num_hm - 1) * 4 + 2])[0]

    def lsb(self, gid):
        d = self.data
        o, _ = self.tabs['hmtx']
        if gid < self.num_hm:
            return struct.unpack('>h', d[o + gid * 4 + 2:o + gid * 4 + 4])[0]
        extra = gid - self.num_hm
        return struct.unpack('>h', d[o + self.num_hm * 4 + extra * 2:o + self.num_hm * 4 + extra * 2 + 2])[0]

    def _glyph_off(self, gid):
        d = self.data
        o, _ = self.tabs['loca']
        if self.loc_fmt == 1:
            a = struct.unpack('>I', d[o + gid * 4:o + gid * 4 + 4])[0]
            b = struct.unpack('>I', d[o + (gid + 1) * 4:o + (gid + 1) * 4 + 4])[0]
        else:
            a = struct.unpack('>H', d[o + gid * 2:o + gid * 2 + 2])[0] * 2
            b = struct.unpack('>H', d[o + (gid + 1) * 2:o + (gid + 1) * 2 + 2])[0] * 2
        go, _ = self.tabs['glyf']
        return go + a, go + b

    def glyph(self, gid):
        """Return (contours, xMin, yMin, xMax, yMax).
        Contour: list of (x, y, on_curve) in font units, y up."""
        if gid in self._glyph_cache:
            return self._glyph_cache[gid]
        d = self.data
        a, b = self._glyph_off(gid)
        if b <= a:
            res = ([], 0, 0, 0, 0)
            self._glyph_cache[gid] = res
            return res
        ncont, x_min, y_min, x_max, y_max = struct.unpack('>hhhhh', d[a:a + 10])
        if ncont < 0:
            res = self._composite(a, x_min, y_min, x_max, y_max)
            self._glyph_cache[gid] = res
            return res
        p = a + 10
        ends = [struct.unpack('>H', d[p + 2 * i:p + 2 * i + 2])[0] for i in range(ncont)]
        p += 2 * ncont
        npts = ends[-1] + 1 if ends else 0
        instr_len = struct.unpack('>H', d[p:p + 2])[0]
        p += 2 + instr_len
        flags = []
        while len(flags) < npts:
            f = d[p]
            p += 1
            flags.append(f)
            if f & 0x08:
                rep = d[p]
                p += 1
                flags.extend([f] * rep)
        xs = []
        x = 0
        for f in flags:
            if f & 0x02:
                dx = d[p]
                p += 1
                if not (f & 0x10):
                    dx = -dx
            else:
                if f & 0x10:
                    dx = 0
                else:
                    dx = struct.unpack('>h', d[p:p + 2])[0]
                    p += 2
            x += dx
            xs.append(x)
        ys = []
        y = 0
        for f in flags:
            if f & 0x04:
                dy = d[p]
                p += 1
                if not (f & 0x20):
                    dy = -dy
            else:
                if f & 0x20:
                    dy = 0
                else:
                    dy = struct.unpack('>h', d[p:p + 2])[0]
                    p += 2
            y += dy
            ys.append(y)
        contours = []
        start = 0
        for end in ends:
            pts = [(xs[i], ys[i], bool(flags[i] & 0x01)) for i in range(start, end + 1)]
            contours.append(pts)
            start = end + 1
        res = (contours, x_min, y_min, x_max, y_max)
        self._glyph_cache[gid] = res
        return res

    def _composite(self, a, x_min, y_min, x_max, y_max):
        d = self.data
        p = a + 10
        contours = []
        while True:
            flags, comp_gid = struct.unpack('>HH', d[p:p + 4])
            p += 4
            if flags & 0x0001:  # args are words
                arg1, arg2 = struct.unpack('>hh', d[p:p + 4])
                p += 4
            else:
                arg1, arg2 = struct.unpack('>bb', d[p:p + 2])
                p += 2
            if flags & 0x0002:  # args are xy
                dx, dy = arg1, arg2
                match = None
            else:
                dx, dy = 0, 0
                match = (arg1, arg2)
            sx = sy = 1.0
            m01 = m10 = 0.0
            if flags & 0x0008:
                s = struct.unpack('>h', d[p:p + 2])[0] / 16384.0
                p += 2
                sx = sy = s
            elif flags & 0x0040:
                sx = struct.unpack('>h', d[p:p + 2])[0] / 16384.0
                sy = struct.unpack('>h', d[p + 2:p + 4])[0] / 16384.0
                p += 4
            elif flags & 0x0080:
                sx = struct.unpack('>h', d[p:p + 2])[0] / 16384.0
                m01 = struct.unpack('>h', d[p + 2:p + 4])[0] / 16384.0
                m10 = struct.unpack('>h', d[p + 4:p + 6])[0] / 16384.0
                sy = struct.unpack('>h', d[p + 6:p + 8])[0] / 16384.0
                p += 8
            sub, _sx0, _sy0, _sx1, _sy1 = self.glyph(comp_gid)
            if match is not None:
                # point matching: align component point to parent point; rare, ignore offset
                dx, dy = 0, 0
            for pts in sub:
                contours.append([(x * sx + y * m01 + dx, x * m10 + y * sy + dy, on)
                                 for (x, y, on) in pts])
            if not (flags & 0x0020):
                break
        return (contours, x_min, y_min, x_max, y_max)

    def flatten(self, gid):
        """Glyph outline as line segments in font units (y up). Cached."""
        if gid in self._flat_cache:
            return self._flat_cache[gid]
        contours, _, _, _, _ = self.glyph(gid)
        segs = []
        for pts in contours:
            if not pts:
                continue
            # build point list starting at an on-curve point
            n = len(pts)
            # find first on-curve
            start = 0
            for i, pt in enumerate(pts):
                if pt[2]:
                    start = i
                    break
            else:
                # all off-curve: implied on-curve midpoints
                ordered = []
                for i in range(n):
                    x1, y1, _ = pts[i]
                    x2, y2, _ = pts[(i + 1) % n]
                    ordered.append(((x1 + x2) / 2, (y1 + y2) / 2, True))
                    ordered.append(pts[(i + 1) % n])
                pts = ordered
                n = len(pts)
                start = 0
            seq = pts[start:] + pts[:start]
            # walk: cur on-curve -> next (off -> quad to following on, or line)
            cur = (seq[0][0], seq[0][1])
            i = 1
            while i < len(seq):
                p1 = seq[i]
                if p1[2]:
                    segs.append((cur, (p1[0], p1[1])))
                    cur = (p1[0], p1[1])
                    i += 1
                else:
                    if i + 1 < len(seq):
                        p2 = seq[i + 1]
                        end = (p2[0], p2[1]) if p2[2] else ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                    else:
                        end = (seq[0][0], seq[0][1])
                    # quadratic cur -> p1 -> end, subdivide
                    steps = 10
                    px, py = cur
                    for k in range(1, steps + 1):
                        t = k / steps
                        mt = 1 - t
                        qx = mt * mt * cur[0] + 2 * mt * t * p1[0] + t * t * end[0]
                        qy = mt * mt * cur[1] + 2 * mt * t * p1[1] + t * t * end[1]
                        segs.append(((px, py), (qx, qy)))
                        px, py = qx, qy
                    cur = end
                    i += 2 if (i + 1 < len(seq) and seq[i + 1][2]) else 1
                    if i < len(seq) and not seq[i][2]:
                        # consumed an implied midpoint; next loop handles it
                        pass
            # close contour
            if cur != (seq[0][0], seq[0][1]):
                segs.append((cur, (seq[0][0], seq[0][1])))
        self._flat_cache[gid] = segs
        return segs

    SS = 4  # supersample factor

    def render(self, gid, size):
        """Return (coverage, w, h, xoff, yoff, adv_px).
        coverage: bytes w*h, 0..16 per pixel (SS*SS). Origin: glyph origin
        at (0,0); bitmap's top-left ink at (xoff, yoff) in px, y down."""
        contours, x_min, y_min, x_max, y_max = self.glyph(gid)
        scale = size / self.upm
        adv = self.advance(gid) * scale
        if not contours or x_max <= x_min or y_max <= y_min:
            return (b'', 0, 0, 0, 0, adv)
        segs = self.flatten(gid)
        ss = self.SS
        # subpixel-space bbox
        fx0 = x_min * scale * ss
        fy0 = -y_max * scale * ss  # y down, top of bbox
        fw = max(1, int(math.ceil((x_max - x_min) * scale * ss)))
        fh = max(1, int(math.ceil((y_max - y_min) * scale * ss)))
        # edges in subpixel coords, relative to bbox origin
        edges = []
        for (ax, ay), (bx, by) in segs:
            x0 = ax * scale * ss - fx0
            y0 = -ay * scale * ss - fy0
            x1 = bx * scale * ss - fx0
            y1 = -by * scale * ss - fy0
            if y0 == y1:
                continue
            edges.append((x0, y0, x1, y1))
        # subpixel bitmap
        sub = bytearray(fw * fh)
        for row in range(fh):
            cy = row + 0.5
            xs = []
            for (x0, y0, x1, y1) in edges:
                if (y0 <= cy < y1) or (y1 <= cy < y0):
                    t = (cy - y0) / (y1 - y0)
                    xs.append((x0 + t * (x1 - x0), 1 if y1 > y0 else -1))
            if not xs:
                continue
            xs.sort()
            wind = 0
            prev = None
            for x, d in xs:
                if prev is not None and wind != 0:
                    a = max(0, int(math.ceil(prev)))
                    b = min(fw, int(math.floor(x)))
                    for xx in range(a, b):
                        sub[row * fw + xx] = 1
                wind += d
                prev = x
        # downsample to coverage 0..16
        w = max(1, int(math.ceil(fw / ss)))
        h = max(1, int(math.ceil(fh / ss)))
        cov = bytearray(w * h)
        for yy in range(h):
            for xx in range(w):
                s = 0
                for dy in range(ss):
                    sy = yy * ss + dy
                    if sy >= fh:
                        break
                    base = sy * fw + xx * ss
                    for dx in range(ss):
                        if xx * ss + dx < fw:
                            s += sub[base + dx]
                cov[yy * w + xx] = s
        xoff = int(math.floor(x_min * scale))
        yoff = int(math.floor(-y_max * scale))
        return (bytes(cov), w, h, xoff, yoff, adv)

    def text_width(self, s, size):
        scale = size / self.upm
        w = 0.0
        prev = None
        for ch in s:
            gid = self.gid(ch)
            w += self.advance(gid) * scale
            if prev is not None:
                w += self.kern.get((prev, gid), 0) * scale
            prev = gid
        return w

    def cap_px(self, size):
        return self.cap_h * size / self.upm


# --- text API. y is the TOP of the cap-height line; size is the em size
# in pixels. All strings are drawn exactly as stored (upper case, as in
# the newspaper data); only the letterforms changed from the old bitmap
# font to Liberation Serif. --------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
REG = TTFont(os.path.join(_HERE, 'fonts', 'LiberationSerif-Regular.ttf'))
BOLD = TTFont(os.path.join(_HERE, 'fonts', 'LiberationSerif-Bold.ttf'))

_glyph_cache = {}


def _render(font, gid, size):
    key = (id(font), gid, size)
    r = _glyph_cache.get(key)
    if r is None:
        r = font.render(gid, size)
        _glyph_cache[key] = r
    return r


def _blit(x, y, cov, w, h, c):
    for yy in range(h):
        py = y + yy
        if py < 0 or py >= H:
            continue
        base = yy * w
        for xx in range(w):
            a = cov[base + xx]
            if not a:
                continue
            px = x + xx
            if px < 0 or px >= W:
                continue
            o = (py * W + px) * 3
            if a >= 16:
                buf[o] = c[0]
                buf[o + 1] = c[1]
                buf[o + 2] = c[2]
            else:
                buf[o] = (a * c[0] + (16 - a) * buf[o]) // 16
                buf[o + 1] = (a * c[1] + (16 - a) * buf[o + 1]) // 16
                buf[o + 2] = (a * c[2] + (16 - a) * buf[o + 2]) // 16


def text(x, y, s, size, c=INK, bold=False):
    font = BOLD if bold else REG
    s = str(s).upper()
    pen = float(x)
    base = y + font.cap_px(size)
    prev = None
    for ch in s:
        gid = font.gid(ch)
        if prev is not None:
            pen += font.kern.get((prev, gid), 0) * size / font.upm
        cov, w, h, xoff, yoff, adv = _render(font, gid, size)
        if cov:
            _blit(int(round(pen)) + xoff, int(round(base)) + yoff, cov, w, h, c)
        pen += adv
        prev = gid
    return int(round(pen))


def text_w(s, size, bold=False):
    font = BOLD if bold else REG
    return font.text_width(str(s).upper(), size)


def text_c(cx, y, s, size, c=INK, bold=False):
    text(cx - text_w(s, size, bold) / 2, y, s, size, c, bold)


def wrap(s, size, maxw, bold=False):
    words = str(s).upper().split(' ')
    lines, cur = [], ''
    for wd in words:
        trial = wd if not cur else cur + ' ' + wd
        if text_w(trial, size, bold) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def tag(x, y, s, c):
    w = int(text_w(s, 10, True)) + 10
    fill(x, y, w, 13, c)
    text(x + 5, y + 3, s, 10, (255, 255, 255), True)
    return w


# --- drawn scenes. Each fills its box (x, y, w, h). ----------------------
def sc_ballot(x, y, w, h):
    fill(x, y, w, h, CREAM)
    # ballot box, left
    bx, by = x + 6, y + h // 2 - 6
    fill(bx, by, 26, 18, INK)
    # ballot slot, kept inside the box so it never crosses the text above
    fill(bx + 8, by + 3, 10, 5, (255, 255, 255))
    # 130-seat bar: coalition 65 blue, rest grey, 66-seat mark
    bar_y = y + h - 16
    bar_w = w - 16
    fill(x + 8, bar_y, bar_w // 2, 8, BLUE)
    fill(x + 8 + bar_w // 2, bar_y, bar_w - bar_w // 2, 8, (150, 148, 142))
    mx = x + 8 + int(bar_w * 66 / 130)
    vbar(mx, bar_y - 3, 14, RED, 2)
    text(x + 8, y + 4, 'NATIONAL 40  LABOUR 36', 10, INK)
    text(x + 8, y + 14, 'COALITION 65  -  MAJORITY 66', 10, RED)
    text_c(mx, bar_y - 12, '66', 10, RED)


def sc_cart(x, y, w, h):
    fill(x, y, w, h, (250, 238, 220))
    # shelf + boxes
    fill(x + 4, y + 6, w - 8, 4, GOLD)
    for i, cc in enumerate((RED, BLUE, GREEN, ORANGE)):
        fill(x + 8 + i * (w // 5), y + 12, w // 6, 12, cc)
    # cart body
    cx, cy = x + w // 2 - 22, y + h // 2
    tri(cx, cy, cx + 44, cy, cx + 38, cy + 20, INK)
    fill(cx + 2, cy + 2, 40, 16, (200, 200, 198))
    fill(cx + 8, cy + 5, 10, 8, RED)
    fill(cx + 22, cy + 5, 10, 8, BLUE)
    seg(cx - 8, cy - 6, cx, cy + 4, INK)
    dot(cx + 8, cy + 24, 3, INK)
    dot(cx + 34, cy + 24, 3, INK)
    # price tag
    fill(x + w - 46, y + h - 20, 42, 14, (255, 255, 255))
    border(x + w - 46, y + h - 20, 42, 14, RED, 1)
    text_c(x + w - 25, y + h - 17, '$149', 10, RED)


def sc_market(x, y, w, h):
    fill(x, y, w, h, (245, 244, 238))
    text(x + 6, y + 3, 'KOSPI +2.9%', 10, GREEN)
    vals = [0.30, 0.45, 0.40, 0.62, 0.55, 0.85, 0.95]
    bw = (w - 12) // 7
    for i, v in enumerate(vals):
        bh = int(v * (h - 22))
        cc = GREEN if i not in (2,) else RED
        fill(x + 6 + i * bw, y + h - 6 - bh, bw - 2, bh, cc)
    seg(x + 8, y + h - 12, x + w - 10, y + 12, RED)
    tri(x + w - 10, y + 12, x + w - 20, y + 10, x + w - 12, y + 20, RED)


def sc_cpi(x, y, w, h):
    fill(x, y, w, h, (245, 244, 238))
    cx, cy = x + w // 2, y + h - 10
    r = min(w, h) // 2 - 4
    for a in range(180, 361, 3):
        t = a * math.pi / 180.0
        put(cx + int(r * math.cos(t)), cy + int(r * math.sin(t)), INK)
        put(cx + int((r - 4) * math.cos(t)), cy + int((r - 4) * math.sin(t)), INK)
    for f in (0.0, 0.25, 0.5, 0.75, 1.0):
        a = (180 + f * 180) * math.pi / 180.0
        seg(cx + int((r - 7) * math.cos(a)), cy + int((r - 7) * math.sin(a)),
            cx + int(r * math.cos(a)), cy + int(r * math.sin(a)), INK)
    na = (180 + 0.58 * 180) * math.pi / 180.0
    seg(cx, cy, cx + int((r - 8) * math.cos(na)), cy + int((r - 8) * math.sin(na)), RED)
    dot(cx, cy, 3, RED)
    text_c(cx, y + 2, '2.9%', 14, RED, True)


def sc_blackout(x, y, w, h):
    fill(x, y, w, h, DARK)
    dot(x + w - 14, y + 10, 6, (240, 238, 220))
    for i in range(6):
        put(x + (i * 41) % w, y + (i * 17) % (h // 3), (255, 255, 255))
    # skyline, mostly dark, two lit windows
    base = y + h
    for i, bh in enumerate((26, 34, 22, 38, 28)):
        bx = x + 4 + i * (w // 5)
        fill(bx, base - bh, w // 5 - 4, bh, (52, 54, 64))
    fill(x + 4 + (w // 5) + 4, base - 26, 4, 5, GOLD)
    fill(x + 4 + 3 * (w // 5) + 6, base - 30, 4, 5, GOLD)
    fill(x + 4 + 4 * (w // 5) + 2, base - 20, 4, 5, GOLD)
    text(x + 5, y + 4, '2-14H', 10, (255, 255, 255))


def sc_talks(x, y, w, h):
    fill(x, y, w, h, (238, 236, 228))
    fill(x + 6, y + h * 2 // 3, w - 12, 5, (120, 90, 60))
    fill(x + 10, y + h * 2 // 3 + 5, 4, h // 4, (120, 90, 60))
    fill(x + w - 14, y + h * 2 // 3 + 5, 4, h // 4, (120, 90, 60))
    for sx, cc in ((x + w // 4, RED), (x + w * 3 // 4, BLUE)):
        dot(sx, y + h // 3, 7, cc)
        tri(sx, y + h // 3 + 7, sx - 10, y + h * 2 // 3 - 2, sx + 10, y + h * 2 // 3 - 2, cc)
    fill(x + w // 2 - 8, y + h // 2 - 2, 16, 10, (255, 255, 255))
    border(x + w // 2 - 8, y + h // 2 - 2, 16, 10, INK, 1)
    text_c(x + w // 2, y + h // 2 + 1, '19', 9, RED, True)


def sc_warning(x, y, w, h):
    fill(x, y, w, h, (250, 235, 215))
    mx, my = x + w // 3, y + h // 2
    tri(mx, my - 12, mx, my + 12, mx + 26, my + 4, RED)
    fill(mx - 8, my - 5, 10, 10, INK)
    fill(mx + 26, my - 8, 4, 16, INK)
    for r in (12, 20, 28):
        for a in range(-50, 51, 6):
            t = a * math.pi / 180.0
            put(mx + 30 + int(r * math.cos(t)), my + int(r * math.sin(t)), ORANGE)
    text(x + w - 30, y + 4, '1M', 14, RED, True)


def sc_fleet(x, y, w, h):
    fill(x, y, w, h, SKY)
    fill(x, y + h * 3 // 4, w, h // 4, (150, 190, 210))
    for k in range(3):
        hbar(x + 3, y + h * 3 // 4 + 3 + k * 4, w - 6, (240, 244, 248), 1)
    # two ships heading right, then a turn-back arrow
    for sx in (x + 8, x + w // 2 - 6):
        fill(sx, y + h // 2, 34, 8, (60, 60, 64))
        fill(sx + 24, y + h // 2 - 10, 6, 10, (240, 240, 238))
    seg(x + w - 14, y + 8, x + w - 30, y + 8, RED)
    seg(x + w - 30, y + 8, x + w - 30, y + h // 3, RED)
    tri(x + w - 30, y + h // 3, x + w - 36, y + h // 3 - 8, x + w - 24, y + h // 3 - 8, RED)


def sc_meeting(x, y, w, h):
    fill(x, y, w, h, SKY)
    for fx, cols in ((x + w // 4, (RED, (255, 255, 255), BLUE)),
                     (x + w * 3 // 4 - 14, ((20, 20, 20), (255, 255, 255), GREEN))):
        vbar(fx, y + 6, h // 2, INK, 3)
        for i, cc in enumerate(cols):
            fill(fx + 3, y + 8 + i * 8, 24, 8, cc)
    fill(x + 8, y + h * 2 // 3, w - 16, 5, (120, 90, 60))
    fill(x + 12, y + h * 2 // 3 + 5, 4, h // 4, (120, 90, 60))
    fill(x + w - 16, y + h * 2 // 3 + 5, 4, h // 4, (120, 90, 60))


def sc_court(x, y, w, h):
    fill(x, y, w, h, (238, 236, 228))
    tri(x + w // 2, y + 4, x + 4, y + h // 3, x + w - 4, y + h // 3, INK)
    for i in range(3):
        fill(x + 8 + i * (w // 3), y + h // 3 + 3, 5, h // 2, INK)
    fill(x + 3, y + h - 10, w - 6, 6, INK)
    fill(x + w // 2 - 5, y + h // 2 + 6, 10, h // 4, (120, 90, 60))


def sc_burglary(x, y, w, h):
    fill(x, y, w, h, DARK)
    dot(x + w - 12, y + 8, 5, (240, 238, 220))
    hx, hy = x + w // 2 - 20, y + h // 3
    fill(hx, hy, 40, 24, (150, 120, 80))
    tri(hx - 4, hy, hx + 20, hy - 14, hx + 44, hy, RED)
    fill(hx + 16, hy + 10, 8, 14, INK)
    fill(hx + 4, hy + 6, 8, 8, GOLD)
    fill(hx + 28, hy + 6, 8, 8, GOLD)
    for i in range(6):
        fill(x + i * (w // 6), y + h - 12, w // 12, 6, GOLD if i % 2 == 0 else INK)
    text(x + 4, y + 4, 'POLICE', 10, GOLD)


def sc_oil(x, y, w, h):
    fill(x, y, w, h, SKY)
    for k in range(3):
        dot(x + w // 3 + k * 8, y + h // 4 - k * 3, 4, (150, 148, 142))
    seg(x + w // 4, y + h - 4, x + w // 2, y + 8, INK)
    seg(x + w * 3 // 4, y + h - 4, x + w // 2, y + 8, INK)
    hbar(x + w // 4, y + h // 2, w // 2, INK, 2)
    hbar(x + w // 4 + 6, y + h // 3, w // 2 - 12, INK, 2)
    fill(x + w * 3 // 4 - 4, y + h // 3, 8, h * 2 // 3, (110, 108, 102))
    dot(x + w * 3 // 4, y + h // 4, 5, ORANGE)
    tri(x + w * 3 // 4, y + h // 4 - 9, x + w * 3 // 4 - 7, y + h // 4 + 4,
        x + w * 3 // 4 + 7, y + h // 4 + 4, RED)


def sc_mine(x, y, w, h):
    fill(x, y, w, h, (238, 232, 220))
    fill(x, y + h * 2 // 3, w, h // 3, (120, 100, 70))
    fill(x + w // 2 - 10, y + h // 4, 20, h // 2, (60, 55, 50))
    fill(x + w // 2 - 10, y + h // 4, 20, 6, INK)
    seg(x + w // 2, y + h // 4, x + w // 2 + 14, y + 4, INK)
    dot(x + w // 4, y + h * 2 // 3 - 6, 6, GOLD)
    fill(x + w // 4 - 8, y + h * 2 // 3 - 2, 16, 4, GOLD)
    for k in range(3):
        hbar(x + 4, y + h - 6 - k * 5, w - 8, (90, 140, 190), 2)
    text(x + 4, y + 4, '13', 14, RED, True)


def sc_ban(x, y, w, h):
    fill(x, y, w, h, (238, 236, 228))
    px, py = x + w // 2 - 16, y + 8
    fill(px, py, 32, 40, (255, 255, 255))
    border(px, py, 32, 40, INK, 1)
    for k in range(4):
        hbar(px + 5, py + 8 + k * 7, 22, SOFT, 1)
    seg(px + 2, py + 2, px + 30, py + 38, RED)
    seg(px + 30, py + 2, px + 2, py + 38, RED)
    circ(x + w // 2, y + h - 12, 9, RED)


def sc_clinic(x, y, w, h):
    fill(x, y, w, h, (238, 236, 228))
    fill(x + w // 2 - 18, y + h // 3, 36, h // 2, (255, 255, 255))
    border(x + w // 2 - 18, y + h // 3, 36, h // 2, INK, 1)
    fill(x + w // 2 - 3, y + h // 3 + 5, 6, 16, RED)
    fill(x + w // 2 - 8, y + h // 3 + 10, 16, 6, RED)
    fill(x + w // 2 - 5, y + h * 2 // 3 + 4, 10, h // 5, (120, 90, 60))
    for i in range(5):
        vbar(x + 4 + i * (w // 5), y + h - 10, 8, INK, 2)
    dot(x + 8, y + 10, 6, GREEN)
    fill(x + 7, y + 14, 2, 10, (90, 70, 40))


SCENES = {
    'ballot': sc_ballot, 'cart': sc_cart, 'market': sc_market,
    'cpi': sc_cpi, 'blackout': sc_blackout, 'talks': sc_talks,
    'warning': sc_warning, 'fleet': sc_fleet, 'meeting': sc_meeting,
    'court': sc_court, 'burglary': sc_burglary, 'oil': sc_oil,
    'mine': sc_mine, 'ban': sc_ban, 'clinic': sc_clinic,
}


# --- the day's stories. Only 27 Nov 2026, verified against the sources
# named in SOURCES.md. SURE: REPORTED / CLAIM / CONFIRMED / OFFICIAL. -----
HEROES = [
    dict(n=1, region='OCEANIA', icon='ballot',
         head='NEW ZEALAND HUNG: 65-65 DEADLOCK',
         body=('FINAL COUNT LEAVES LUXON ONE SEAT SHORT; OPPORTUNITY, '
               'WITH SEVEN SEATS, HOLDS THE BALANCE.'),
         why='FIRST HUNG PARLIAMENT IN YEARS; A NEWCOMER DECIDES THE GOVERNMENT.',
         src='REUTERS', sure='OFFICIAL'),
    dict(n=2, region='N. AMERICA', icon='cart',
         head='BLACK FRIDAY LIVE: $149 AIRPODS',
         body=("SHOPPERS QUEUE FOR THE BIGGEST SALE: AIRPODS PRO 3 $149, "
               'MACBOOK AIR M5 $989, TVS $228.'),
         why='BIGGEST TEST OF THE US CONSUMER AFTER A YEAR OF TARIFF FEARS.',
         src='BENZINGA', sure='REPORTED'),
    dict(n=3, region='E. ASIA', icon='market',
         head='ASIAN STOCKS RALLY, BITCOIN $61,869',
         body=('KOSPI JUMPS 2.9%, NIKKEI UP 1.4% AS TECH REBOUNDS. GOLD '
               '$3,565; OIL NEARS $86.'),
         why='TECH REBOUND AFTER THE NASDAQ BEAR-MARKET SCARE; WALL ST REOPENS FOR A HALF DAY.',
         src='FINNHUB', sure='REPORTED'),
]

MEDIUM = [
    dict(n=4, region='E. ASIA', icon='cpi',
         head='TOKYO PRICES RISE 2.9%',
         body=('TOKYO CORE INFLATION HIT 2.9% IN NOVEMBER, JUST BELOW '
               'THE 3.0% FORECAST.'),
         src='TOSCALE', sure='REPORTED'),
    dict(n=5, region='RUSSIA-UKRAINE', icon='blackout',
         head='UKRAINE FACES 14-HOUR BLACKOUTS',
         body=('UKRENERGO SETS ROUND-THE-CLOCK OUTAGES AFTER STRIKES '
               'ON ENERGY SITES.'),
         src='UKRENERGO', sure='REPORTED'),
    dict(n=6, region='MIDDLE EAST', icon='talks',
         head='HAMAS WEIGHS RESPONSE TO KILLINGS',
         body=('HAMAS CONSULTS FACTIONS AFTER STRIKES KILLED SENIOR '
               'OFFICIALS.'),
         src='AP', sure='REPORTED'),
    dict(n=7, region='MIDDLE EAST', icon='warning',
         head='ISRAEL WARNS: MOVE 1M IN GAZA',
         body=("MINISTER WARNS A MILLION PALESTINIANS MAY BE MOVED IF "
               "HAMAS WON'T DISARM."),
         src='LM', sure='REPORTED'),
    dict(n=8, region='AFRICA', icon='fleet',
         head='RUSSIAN FLEET TURNS BACK IN MED',
         body=("MOSCOW'S NAVAL GROUP TURNS BACK IN THE MED AFTER "
               "UKRAINE'S LIBYA STRIKES."),
         src='LM', sure='REPORTED'),
    dict(n=9, region='EUROPE', icon='meeting',
         head='UK PM MEETS JORDAN KING',
         body=('LEADERS DISCUSS BILATERAL TIES AND MIDDLE EAST '
               'TENSIONS IN LONDON.'),
         src='LM', sure='REPORTED'),
    dict(n=10, region='EUROPE', icon='court',
         head='BERLIN SPY TRIAL OPENS',
         body=('GERMANY TRIES A MAN ACCUSED OF SPYING FOR RUSSIAN '
               'INTELLIGENCE.'),
         src='LM', sure='REPORTED'),
    dict(n=11, region='EUROPE', icon='burglary',
         head='BURGLARY ARRESTS AT ROYAL HOME',
         body=('TWO HELD OVER A BURGLARY AT THE COUNTRY HOME OF PRINCE '
               'WILLIAM AND KATE.'),
         src='LM', sure='REPORTED'),
    dict(n=12, region='MIDDLE EAST', icon='oil',
         head='BAGHDAD-ERBIL TALK FEDERALISM',
         body=('TALKS AIM TO DEFUSE THE BAGHDAD-ERBIL DISPUTE OVER '
               'FEDERALISM AND OIL.'),
         src='LM', sure='REPORTED'),
    dict(n=13, region='S. ASIA', icon='mine',
         head='INDONESIA MINE RESCUE GOES ON',
         body=('RESCUERS RACE TO REACH 13 TRAPPED MINERS AFTER A FLOOD '
               'HIT A GOLD MINE.'),
         src='LM', sure='REPORTED'),
    dict(n=14, region='S. AMERICA', icon='ban',
         head='COSTA RICA BARS UN RAPPORTEUR',
         body=("SAN JOSE DENIES ENTRY TO UN'S FRANCESCA ALBANESE OVER "
               'ALLEGED TERROR LINKS.'),
         src='LM', sure='REPORTED'),
    dict(n=15, region='SUB-SAHARAN', icon='clinic',
         head='KENYA COURT HALTS EBOLA SITE',
         body=('A COURT STOPS A US-BACKED EBOLA FACILITY OVER LACK OF '
               'PUBLIC CONSULTATION.'),
         src='JG', sure='REPORTED'),
]

COMPACT = [
    (16, 'US OKAYS $621.9M MILITARY AID FOR UKRAINE', 'LM', 'REPORTED'),
    (17, 'RUSSIAN GENERAL GREKHOV DETAINED IN MOSCOW', 'JG', 'REPORTED'),
    (18, 'ZELENSKYY THANKS US ON THANKSGIVING', 'IS', 'REPORTED'),
    (19, 'OPERATION SANTA AIDS CIVILIANS UNDER OCCUPATION', 'LM', 'REPORTED'),
    (20, 'MOSCOW HIDES DEMOGRAPHIC DATA', 'IS', 'REPORTED'),
    (21, 'TRUMP UNSURE PUTIN WILL COME TO G20', 'IS', 'REPORTED'),
    (22, 'KUSHNER: PUTIN NOT INTERESTED IN CEASEFIRE', 'LM', 'REPORTED'),
    (23, 'WALL STREET REOPENS FOR A HALF DAY', 'TF', 'REPORTED'),
    (24, "SPAIN'S FAR RIGHT EYES ELECTION GAINS", 'LM', 'REPORTED'),
    (25, 'FRANCE PRODUCER PRICES UP 9.6%', 'IS', 'REPORTED'),
    (26, 'GERMANY PLANS BIGGER SYRIA RETURN SCHEME', 'IS', 'REPORTED'),
    (27, 'DEPARDIEU ORDERED TO FACE TRIAL', 'IS', 'REPORTED'),
    (28, 'STUBB URGES HOLIDAY TRUCE FOR UKRAINE', 'JG', 'REPORTED'),
    (29, 'UK CALLS UP 100,000 RESERVISTS', 'LM', 'REPORTED'),
    (30, "UK CONDEMNS MOSCOW'S 'NAZI' RHETORIC", 'IS', 'REPORTED'),
    (31, 'DRONE BRIEFLY ENTERS LATVIAN AIRSPACE', 'IS', 'REPORTED'),
    (32, '17 CREW IN DISTRESS OFF ICELAND', 'LM', 'REPORTED'),
    (33, 'ARMENIA TO DROP RUSSIAN BORDER GUARDS', 'JG', 'REPORTED'),
    (34, 'GEORGIA: RUSSIA PLANS TO ANNEX ABKHAZIA', 'IS', 'CLAIM'),
    (35, 'DRONE SETS 727 KM/H SPEED RECORD', 'LM', 'REPORTED'),
    (36, 'IRAQ-TURKEY EYE 2027 DEVELOPMENT ROAD', 'LM', 'REPORTED'),
    (37, 'KREMLIN WARNS TALLINN OVER BORDER CURBS', 'LM', 'REPORTED'),
    (38, 'PAKISTAN COURT DEFERS ALEEMA KHAN VERDICT', 'LM', 'REPORTED'),
    (39, 'ROHINGYA: WHAT NEXT AFTER ICJ RULING', 'IS', 'REPORTED'),
    (40, 'JAPAN TO TEST 1,000-KM MISSILES IN INDIA', 'JG', 'REPORTED'),
    (41, 'SEOUL CHIEF JUSTICE FACES IMPEACHMENT', 'LM', 'REPORTED'),
    (42, 'XI URGES STRICT PARTY RULE', 'JG', 'REPORTED'),
]

CHIPS = [('N. AMERICA', 4), ('S. AMERICA', 1), ('EUROPE', 16),
         ('RUSSIA-UKRAINE', 6), ('MIDDLE EAST', 4), ('AFRICA', 1),
         ('SUB-SAHARAN', 1), ('S. ASIA', 3), ('E. ASIA', 5),
         ('OCEANIA', 1)]

NUMBERS = [
    ('65', 'SEATS: NZ COALITION', 'ONE SHORT OF MAJORITY'),
    ('$149', 'AIRPODS PRO 3', 'BLACK FRIDAY PRICE'),
    ('+2.9%', 'KOSPI IN SEOUL', 'FRIDAY RALLY'),
    ('$61,869', 'BITCOIN', '07:22 UTC, +2.2%'),
    ('$3,565', 'GOLD PER OUNCE', 'FRIDAY TRADE'),
    ('$85.78', 'WTI CRUDE OIL', 'SUPPLY FEARS LIFT IT'),
]

PINS = {
    1: (174.8, -41.3), 2: (-74.0, 40.7), 3: (127.0, 37.5),
    4: (139.7, 35.7), 5: (30.5, 50.4), 6: (34.5, 31.5),
    7: (35.2, 31.8), 8: (20.1, 32.1), 9: (-0.1, 51.5),
    10: (13.4, 52.5), 11: (-0.3, 51.4), 12: (44.4, 33.3),
    13: (120.0, -1.0), 14: (-84.1, 9.9), 15: (36.8, -1.3),
    16: (-77.0, 38.9), 17: (37.6, 55.7), 18: (30.7, 50.5),
    19: (30.3, 50.3), 20: (37.8, 55.8), 21: (-80.2, 25.8),
    22: (-77.2, 39.0), 23: (-74.2, 40.8), 24: (-3.7, 40.4),
    25: (2.3, 48.9), 26: (13.6, 52.6), 27: (2.5, 48.8),
    28: (25.0, 60.2), 29: (-0.2, 51.6), 30: (0.0, 51.4),
    31: (24.1, 56.9), 32: (-21.9, 64.1), 33: (44.5, 40.2),
    34: (41.7, 41.7), 35: (13.2, 52.4), 36: (32.9, 39.9),
    37: (24.7, 59.4), 38: (73.1, 33.7), 39: (4.3, 52.1),
    40: (139.9, 35.6), 41: (127.2, 37.6), 42: (116.4, 39.9),
}

CONTINENTS = [
    [(-168, 66), (-140, 70), (-120, 72), (-95, 78), (-80, 70), (-65, 60),
     (-55, 47), (-65, 42), (-75, 35), (-81, 26), (-90, 21), (-97, 16),
     (-105, 20), (-115, 30), (-125, 40), (-125, 49), (-140, 60),
     (-160, 58)],
    [(-80, 10), (-77, 4), (-80, -5), (-75, -15), (-70, -25), (-65, -40),
     (-70, -52), (-66, -55), (-62, -40), (-55, -30), (-48, -25),
     (-40, -20), (-35, -8), (-45, -3), (-50, 0), (-60, 8), (-70, 11)],
    [(-10, 36), (-9, 43), (-2, 48), (-4, 50), (0, 51), (5, 53), (8, 57),
     (10, 59), (18, 56), (21, 55), (28, 60), (30, 68), (40, 68),
     (35, 55), (30, 50), (28, 45), (23, 40), (19, 42), (12, 44),
     (8, 44), (3, 42), (0, 39), (-2, 37), (-6, 36)],
    [(-6, 35), (10, 37), (20, 32), (30, 31), (32, 31), (35, 28),
     (40, 15), (43, 12), (48, 11), (51, 10), (44, 0), (40, -10),
     (36, -18), (32, -26), (28, -33), (20, -35), (17, -29), (14, -17),
     (12, -6), (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 15), (-16, 20),
     (-14, 28), (-10, 31)],
    [(30, 62), (40, 68), (50, 69), (60, 69), (70, 72), (80, 73),
     (100, 77), (110, 76), (130, 72), (150, 70), (160, 66), (170, 66),
     (178, 65), (170, 60), (162, 56), (158, 52), (142, 50), (140, 45),
     (135, 43), (130, 38), (127, 35), (122, 38), (120, 32), (115, 23),
     (109, 18), (105, 10), (100, 8), (98, 12), (92, 16), (88, 22),
     (80, 15), (77, 8), (75, 12), (72, 20), (66, 25), (62, 25),
     (57, 26), (54, 26), (52, 28), (50, 30), (48, 30), (44, 29),
     (40, 31), (36, 36), (33, 36), (30, 36), (27, 37), (26, 40),
     (23, 40), (26, 45), (28, 45), (30, 46)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33),
     (129, -32), (132, -32), (135, -35), (137, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
     (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
     (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)],
    [(167, -45), (170, -43), (173, -41), (175, -38), (177, -38),
     (178, -37), (174, -42), (170, -46), (167, -46)],
]

UTC_LINE_1 = ('00:04 HAMAS CONSULTS FACTIONS  -  01:46 NZ FINAL COUNT OUT  -  '
              '05:34 BLACK FRIDAY LIVE  -  07:22 BITCOIN $61,869')
UTC_LINE_2 = ('18:00 WALL ST CLOSES EARLY  -  TONIGHT: FOREST V CHELSEA, '
              'BREMEN V GLADBACH, LAKERS AT SPURS')


def build():
    MX = 24
    PW = W - 2 * MX
    fill(0, 0, W, 6, INK)
    text_c(W // 2, 10, 'THE WORLD', 71, INK, True)
    hbar(MX, 64, PW, INK, 2)
    text_c(W // 2, 68, 'FRIDAY 27 NOVEMBER 2026', 20, INK, True)
    text_c(W // 2, 86, "THE DAY'S WORLD NEWS IN ONE PAGE  -  42 STORIES  -  10 REGIONS",
           11, SOFT)
    hbar(MX, 96, PW, INK, 1)

    # region chips
    cx = MX
    for name, cnt in CHIPS:
        label = '%s %d' % (name, cnt)
        w = int(text_w(label, 10, True)) + 14
        fill(cx, 100, w, 16, INK)
        text(cx + 7, 104, label, 10, (255, 255, 255), True)
        cx += w + 6

    # numbers strip, on top (winner pattern)
    text(MX, 122, 'THE DAY IN NUMBERS', 11, RED, True)
    hbar(MX, 133, PW, INK, 1)
    bw = (PW - 5 * 6) // 6
    for i, (big, l1, l2) in enumerate(NUMBERS):
        bx = MX + i * (bw + 6)
        border(bx, 136, bw, 40, RULE, 1)
        text_c(bx + bw // 2, 138, big, 30, RED, True)
        text_c(bx + bw // 2, 159, l1, 10, INK, True)
        text_c(bx + bw // 2, 167, l2, 10, SOFT)

    # three heroes
    hy = 182
    hw = (PW - 2 * 8) // 3
    hh = 172
    for i, st in enumerate(HEROES):
        hx = MX + i * (hw + 8)
        border(hx, hy, hw, hh, INK, 1)
        SCENES[st['icon']](hx + 1, hy + 1, hw - 2, 56)
        tw_ = tag(hx + 8, hy + 62, st['region'], RED)
        text(hx + 8 + tw_ + 8, hy + 65, str(st['n']), 10, RED, True)
        yy = hy + 78
        for ln in wrap(st['head'], 20, hw - 16, True)[:2]:
            text(hx + 8, yy, ln, 20, INK, True)
            yy += 16
        yy = hy + 112
        for ln in wrap(st['body'], 10, hw - 16)[:2]:
            text(hx + 8, yy, ln, 10, SOFT)
            yy += 11
        yy = hy + 134
        for ln in wrap('WHY IT MATTERS: ' + st['why'], 10, hw - 16)[:2]:
            text(hx + 8, yy, ln, 10, INK)
            yy += 11
        text(hx + 8, hy + hh - 12, 'SOURCE: ' + st['src'] + '  -  ' + st['sure'],
             10, BLUE)

    # medium grid, 3 x 4
    gy = 360
    text(MX, gy, 'THE WORLD IN BRIEF', 11, RED, True)
    hbar(MX, gy + 11, PW, INK, 1)
    cw = (PW - 2 * 8) // 3
    ch = 84
    for idx, st in enumerate(MEDIUM):
        r, ccol = divmod(idx, 3)
        x = MX + ccol * (cw + 8)
        y = gy + 16 + r * (ch + 6)
        border(x, y, cw, ch, RULE, 1)
        SCENES[st['icon']](x + 6, y + 20, 68, 60)
        tw_ = tag(x + 6, y + 5, st['region'], INK)
        text(x + 6 + tw_ + 8, y + 8, str(st['n']), 10, RED, True)
        tx = x + 80
        tw = cw - 88
        yy = y + 20
        for ln in wrap(st['head'], 18, tw, True)[:2]:
            text(tx, yy, ln, 18, INK, True)
            yy += 15
        yy = y + 54
        for ln in wrap(st['body'], 9.5, tw)[:2]:
            text(tx, yy, ln, 9.5, SOFT)
            yy += 11
        text(tx, y + ch - 8, st['src'] + ' - ' + st['sure'], 10, BLUE)

    # compact list, 3 columns x 9 rows
    ay = 736
    text(MX, ay, 'ALSO TODAY', 11, RED, True)
    hbar(MX, ay + 11, PW, INK, 1)
    cols = [COMPACT[i * 9:(i + 1) * 9] for i in range(3)]
    for ci, col in enumerate(cols):
        x = MX + ci * (cw + 8)
        yy = ay + 16
        for n, head, src, sure in col:
            mark = 'CLAIM' if sure == 'CLAIM' else src
            avail = cw - text_w(mark, 10, True) - 8
            prefix = '%d. ' % n
            while text_w(prefix + head, 10) > avail and len(head) > 4:
                head = head[:-1]
            text(x, yy, prefix + head, 10, INK)
            text(x + cw - text_w(mark, 10, True), yy, mark, 10,
                 RED if sure == 'CLAIM' else BLUE, True)
            yy += 11

    # map
    my = 857
    text(MX, my, 'WHERE IT HAPPENED  -  PINNED BY STORY NUMBER', 11, RED, True)
    hbar(MX, my + 11, PW, INK, 1)
    map_y = my + 16
    map_h = 58
    fill(MX, map_y, PW, map_h, SKY)
    for cont in CONTINENTS:
        pts = []
        for lon, lat in cont:
            px_ = MX + int((lon + 180) / 360 * PW)
            py_ = map_y + int((75 - lat) / 130 * map_h)
            pts.append((px_, py_))
        ngon(pts, LAND)
    border(MX, map_y, PW, map_h, INK, 1)
    for n, (lon, lat) in sorted(PINS.items()):
        px_ = MX + int((lon + 180) / 360 * PW)
        py_ = map_y + int((75 - lat) / 130 * map_h)
        dot(px_, py_, 6, RED)
        circ(px_, py_, 6, (255, 255, 255))
        s = str(n)
        text_c(px_, py_ - 3, s, 9, (255, 255, 255), True)

    # UTC strip
    uy = 937
    text(MX, uy, 'THE DAY IN UTC', 10, RED, True)
    text(MX + text_w('THE DAY IN UTC', 10, True) + 10, uy, UTC_LINE_1, 10, INK)
    text(MX, uy + 10, UTC_LINE_2, 10, INK)

    # footer: date check + how sure + sources
    fy = 959
    hbar(MX, fy, PW, INK, 2)
    text(MX, fy + 6,
         'DATE CHECK: EVERY STORY ABOVE HAPPENED OR WAS FIRST REPORTED '
         'ON 27 NOV 2026.', 9, INK)
    text(MX, fy + 14,
         'LEFT OUT (OTHER DAYS): TRUMP TARIFFS 25-26 NOV - GAZA STRIKES '
         '26 NOV - KYIV MISSILES 26 NOV - EGYPT TUNNEL FIRE 26 NOV - '
         'BANGKOK BLAST 26 NOV', 9, SOFT)
    text(MX, fy + 22,
         'EBOLA 12,000 IN CONGO 26 NOV - UK MIGRATION LOW 26 NOV - MACY '
         'PARADE PUT OFF 26 NOV - UCL: BARCA 4-1 SABAH 25 NOV - MERKURY '
         'SUNK 22 NOV - NEPTUNE HIT MARINOVKA 26 NOV', 9, SOFT)
    text(MX, fy + 30,
         'HOW SURE: REPORTED = NAMED OUTLET, UNCONFIRMED - CLAIM = ONE '
         'SIDE, UNVERIFIED - CONFIRMED = RECORDS OR COURT - OFFICIAL = '
         'GOVERNMENT OR ELECTION BODY', 9, INK)
    text(MX, fy + 38,
         'SOURCES: REUTERS (RE) - AP - BENZINGA (BZ) - FINNHUB (FH) - '
         'FINBROOKS (FB) - TRADERFACTOR (TF) - TOSCALE (TS) - UKRENERGO '
         '(UK)', 9, SOFT)
    text(MX, fy + 46,
         'ONE TURN (OT) - CNN (CN) - LAMEDITERRANEE (LM) - '
         'INVESTSOLUTIONS (IS) - JOYOFGREEN (JG) - KPODGTM (KP)', 9, SOFT)
    text_c(W // 2, fy + 54, 'DRAWN BY HAND IN CODE. NO PHOTOS. THE WORLD, 27 NOV 2026.',
           9, SOFT)
    return fy + 61


def png_bytes():
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        return out

    ihdr = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', comp) + chunk(b'IEND', b''))


def main():
    build()
    data = png_bytes()
    out = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'entry.png'), 'wb') as f:
        f.write(data)


if __name__ == '__main__':
    main()
