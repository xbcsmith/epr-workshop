#!/usr/bin/env python3
# Combined core concepts GIF generator
#
import math
import os

from PIL import Image, ImageDraw, ImageFont

OUT = "../images"
os.makedirs(OUT, exist_ok=True)

MONO_B = "DejaVuSansMono-Bold.ttf"
MONO = "DejaVuSansMono.ttf"
SANS_B = "Poppins-Bold.ttf"
SANS = "Poppins-Medium.ttf"


def ft(path, size):
    return ImageFont.truetype(path, size)


# ── colour palette ────────────────────────────────────────────────────────────
BG = (10, 12, 16)
SURFACE = (17, 19, 24)
BORDER = (30, 34, 48)
TEXT = (226, 232, 240)
MUTED = (100, 116, 139)
BLUE = (59, 130, 246)
CYAN = (6, 182, 212)
GREEN = (16, 185, 129)
AMBER = (245, 159, 11)
RED = (239, 68, 68)
PURPLE = (139, 92, 246)
PINK = (236, 72, 153)
L_BLUE = (147, 197, 253)
L_GREEN = (110, 231, 183)
L_RED = (252, 165, 165)
L_AMBER = (253, 230, 138)
L_PURP = (196, 181, 253)
L_CYAN = (103, 232, 249)
TEAL = (20, 184, 166)
L_TEAL = (153, 246, 228)
INDIGO = (99, 102, 241)
L_INDIGO = (165, 180, 252)

W, H = 800, 460


def new_frame():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def rounded_rect(d, box, r, fill, outline=None, width=2):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(
        [x0, y0, x1, y1], radius=r, fill=fill, outline=outline, width=width
    )


def label(d, text, cx, cy, font, color=TEXT, anchor="mm"):
    d.text((cx, cy), text, font=font, fill=color, anchor=anchor)


def arrow(d, x0, y0, x1, y1, color, width=2, head=10):
    d.line([(x0, y0), (x1, y1)], fill=color, width=width)
    # arrowhead
    dx, dy = x1 - x0, y1 - y0
    length = max(math.hypot(dx, dy), 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    pts = [
        (x1, y1),
        (x1 - head * ux + head * 0.4 * px, y1 - head * uy + head * 0.4 * py),
        (x1 - head * ux - head * 0.4 * px, y1 - head * uy - head * 0.4 * py),
    ]
    d.polygon(pts, fill=color)


def dashed_arrow(d, x0, y0, x1, y1, color, seg=10, gap=6, width=2):
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    t = 0
    on = True
    while t < length:
        t2 = min(t + (seg if on else gap), length)
        if on:
            sx, sy = x0 + ux * t, y0 + uy * t
            ex, ey = x0 + ux * t2, y0 + uy * t2
            d.line([(sx, sy), (ex, ey)], fill=color, width=width)
        t = t2
        on = not on
    arrow(d, x1 - ux * 3, y1 - uy * 3, x1, y1, color, width=width, head=9)


def pulse(t, period=1.0, lo=0.4, hi=1.0):
    """0–1 oscillating value"""
    v = (math.sin(2 * math.pi * t / period) + 1) / 2
    return lo + v * (hi - lo)


def lerp(a, b, t):
    return a + (b - a) * t


def lerpC(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def alpha_color(base, alpha):
    """Blend base color onto BG with given alpha 0-1"""
    return lerpC(BG, base, max(0.0, min(alpha, 1.0)))


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def save_gif(frames, name, duration=85):
    path = f"{OUT}/{name}.gif"
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=duration,
        optimize=False,
    )
    kb = os.path.getsize(path) // 1024
    print(f"  ✓ {path}  ({len(frames)} frames, {kb}KB)")
    # Also save final frame as PNG for presentations
    png_path = f"{OUT}/{name}.png"
    frames[-1].save(png_path, "PNG")
    kb_png = os.path.getsize(png_path) // 1024
    print(f"  ✓ {png_path}  ({kb_png}KB)")


def phase_fn(phase_lengths):
    def get(f):
        acc = 0
        for i, pl in enumerate(phase_lengths):
            acc += pl
            if f < acc:
                raw = 1 - (acc - f) / pl
                return i, ease_in_out(raw)
        return len(phase_lengths) - 1, 1.0

    total = sum(phase_lengths)
    return get, total


def step_indicator(d, steps, ph, accent=BLUE, light=L_BLUE):
    f_tiny = ft(MONO, 7)
    f_step = ft(MONO, 9)
    rounded_rect(d, (20, 405, 780, 448), 8, SURFACE, BORDER, 1)
    n = len(steps)
    spacing = 740 // n
    for si, st in enumerate(steps):
        cx = 30 + si * spacing + spacing // 2
        if si < ph:
            d.ellipse(
                [(cx - 14, 415), (cx + 14, 435)], fill=(10, 35, 15), outline=GREEN
            )
            label(d, "✓", cx, 425, f_step, GREEN)
        elif si == ph:
            d.ellipse(
                [(cx - 14, 415), (cx + 14, 435)],
                fill=(12, 14, 22),
                outline=accent,
                width=2,
            )
            label(d, str(si), cx, 425, f_step, light)
        else:
            d.ellipse(
                [(cx - 14, 415), (cx + 14, 435)], fill=SURFACE, outline=BORDER, width=1
            )
            label(d, str(si), cx, 425, f_step, MUTED)
        col = GREEN if si < ph else (light if si == ph else MUTED)
        label(d, st[:9], cx, 442, f_tiny, col)


NFRAMES = 48  # frames per gif


# ══════════════════════════════════════════════════════════════════════════════
# 6. OUTBOX PATTERN
# ══════════════════════════════════════════════════════════════════════════════
def make_outbox():
    print("Generating outbox GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    # Phases: 0=idle, 1=begin_tx, 2=write_orders, 3=write_outbox, 4=commit,
    #         5=relay_poll, 6=publish, 7=mark_published, 8=done_pause
    PHASE_LEN = [6, 5, 5, 5, 5, 5, 6, 5, 8]
    total = sum(PHASE_LEN)
    frames = []

    def phase_of(f):
        acc = 0
        for i, pl in enumerate(PHASE_LEN):
            acc += pl
            if f < acc:
                return i, 1 - (acc - f) / pl  # phase index, progress 0→1
        return len(PHASE_LEN) - 1, 1.0

    # Layout constants
    APP_BOX = (40, 170, 175, 240)
    DB_BOX = (230, 80, 510, 360)
    ORD_BOX = (250, 110, 490, 195)
    OUTBOX_BOX = (250, 215, 490, 340)
    RELAY_BOX = (560, 240, 720, 305)
    BROKER_BOX = (560, 100, 720, 185)

    for fi in range(total):
        ph, prog = phase_of(fi)
        img, d = new_frame()

        # title bar
        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(d, "TRANSACTIONAL OUTBOX PATTERN", W // 2, 34, f_title, L_BLUE)
        rounded_rect(d, (680, 20, 770, 48), 5, (30, 58, 95), None)
        label(d, "RELIABILITY", 725, 34, f_badge, BLUE)

        # ── App Service ──
        app_col = lerpC(BORDER, BLUE, pulse(fi / 4)) if ph in (1, 2, 3, 4) else BORDER
        rounded_rect(d, APP_BOX, 10, (20, 30, 50), app_col, 2)
        label(d, "APP SERVICE", 107, 195, f_label, L_BLUE)
        label(d, "order_service", 107, 215, f_tiny, MUTED)

        # ── Postgres DB ──
        rounded_rect(d, DB_BOX, 12, SURFACE, BORDER, 1)
        label(d, "POSTGRES", 370, 100, f_label, MUTED)

        # orders table
        rounded_rect(d, ORD_BOX, 8, (22, 28, 46), BORDER, 1)
        rounded_rect(d, (250, 110, 490, 133), 8, (30, 58, 95), None)
        label(d, "orders", 370, 121, f_small, L_BLUE)
        rows = [("id", "uuid"), ("status", "varchar"), ("total", "decimal")]
        for ri, (k, v) in enumerate(rows):
            label(d, k, 270, 148 + ri * 16, f_tiny, MUTED)
            label(d, v, 440, 148 + ri * 16, f_tiny, (71, 85, 105))

        # outbox table — highlight during tx phases
        ob_col = (
            lerpC(BORDER, AMBER, min(prog, 1))
            if ph in (3, 4)
            else (AMBER if ph >= 4 else BORDER)
        )
        rounded_rect(d, OUTBOX_BOX, 8, (22, 28, 46), ob_col, 2 if ph >= 3 else 1)
        rounded_rect(
            d, (250, 215, 490, 238), 8, (61, 46, 16) if ph >= 3 else (20, 22, 30), None
        )
        label(d, "outbox_events", 370, 226, f_small, L_AMBER if ph >= 3 else MUTED)
        ob_rows = [
            ("id", "uuid"),
            ("event_type", "varchar"),
            ("payload", "jsonb"),
            ("published", "bool"),
            ("created_at", "timestamptz"),
        ]
        for ri, (k, v) in enumerate(ob_rows):
            vc = (
                L_AMBER
                if (k == "published" and ph >= 6)
                else (L_AMBER if k == "published" else (71, 85, 105))
            )
            label(d, k, 270, 253 + ri * 15, f_tiny, MUTED)
            label(d, v, 420, 253 + ri * 15, f_tiny, vc)

        # published flag status
        if ph >= 7:
            rounded_rect(d, (380, 320, 490, 338), 4, (10, 35, 15), None)
            label(d, "published=true ✓", 435, 329, f_tiny, GREEN)

        # ── Relay ──
        rel_col = (
            lerpC(BORDER, GREEN, min(prog, 1))
            if ph == 5
            else (GREEN if ph >= 5 else BORDER)
        )
        rounded_rect(d, RELAY_BOX, 8, (18, 32, 20), rel_col, 2)
        label(d, "OUTBOX RELAY", 640, 263, f_small, L_GREEN)
        label(d, "polls / CDC", 640, 282, f_tiny, (74, 222, 128))

        # ── Broker ──
        br_col = (
            lerpC(BORDER, PURPLE, min(prog, 1))
            if ph == 6
            else (PURPLE if ph >= 6 else BORDER)
        )
        rounded_rect(d, BROKER_BOX, 8, (20, 18, 40), br_col, 2)
        label(d, "MESSAGE BROKER", 640, 133, f_small, L_PURP)
        label(d, "Kafka / RabbitMQ", 640, 153, f_tiny, (124, 58, 237))

        # ── Animated arrows ──
        # Phase 1: App→DB begin tx (dashed blue)
        if ph >= 1:
            a = min(prog, 1) if ph == 1 else 1.0
            ex = int(lerp(175, 230, a))
            dashed_arrow(d, 175, 195, ex, 165, alpha_color(BLUE, a), width=2)
            label(d, "BEGIN TX", 200, 158, f_tiny, alpha_color(L_BLUE, a))

        # Phase 2: write orders row (solid)
        if ph >= 2:
            a = min(prog, 1) if ph == 2 else 1.0
            rounded_rect(
                d,
                (250, 148, 490, 163),
                3,
                alpha_color((30, 58, 95), a),
                alpha_color(BLUE, a * 0.5),
                1,
            )
            label(d, "ORDER #42 inserted", 370, 155, f_tiny, alpha_color(L_BLUE, a))

        # Phase 3: write outbox row (amber)
        if ph >= 3:
            a = min(prog, 1) if ph == 3 else 1.0
            ey = int(lerp(205, 256, a))
            arrow(d, 175, 210, 250, ey, alpha_color(AMBER, a), width=2)

        # Phase 4: COMMIT banner
        if ph >= 4:
            a = min(prog, 1) if ph == 4 else 1.0
            rounded_rect(d, (40, 252, 175, 272), 5, alpha_color((61, 46, 16), a), None)
            label(d, "COMMIT TX ✓", 107, 262, f_tiny, alpha_color(L_AMBER, a))

        # Phase 5: Relay polls (green, arrow from relay→outbox)
        if ph >= 5:
            a = min(prog, 1) if ph == 5 else 1.0
            ex = int(lerp(560, 492, a))
            arrow(d, 560, 272, ex, 272, alpha_color(GREEN, a), width=2)
            label(d, "POLL", 528, 263, f_tiny, alpha_color(GREEN, a))

        # Phase 6: Relay→Broker publish
        if ph >= 6:
            a = min(prog, 1) if ph == 6 else 1.0
            ey = int(lerp(240, 188, a))
            arrow(d, 640, 240, 640, ey, alpha_color(PURPLE, a), width=2)
            label(d, "PUBLISH", 656, 215, f_tiny, alpha_color(L_PURP, a))

        # Phase 7: mark published
        if ph >= 7:
            a = min(prog, 1) if ph == 7 else 1.0
            dashed_arrow(d, 560, 285, 492, 325, alpha_color(GREEN, a), width=1)
            label(d, "mark published", 510, 308, f_tiny, alpha_color(GREEN, a))

        # Step indicator at bottom
        steps = [
            "idle",
            "BEGIN TX",
            "write orders",
            "write outbox",
            "COMMIT",
            "relay polls",
            "publish",
            "mark published",
            "✓ done",
        ]
        rounded_rect(d, (20, 400, 780, 445), 8, SURFACE, BORDER, 1)
        for si, st in enumerate(steps):
            cx = 50 + si * 87
            col = GREEN if si < ph else (L_BLUE if si == ph else MUTED)
            if si < ph:
                d.ellipse(
                    [(cx - 18, 413), (cx + 18, 433)], fill=(10, 35, 15), outline=GREEN
                )
                label(d, "✓", cx, 423, f_tiny, GREEN)
            elif si == ph:
                d.ellipse(
                    [(cx - 18, 413), (cx + 18, 433)],
                    fill=(20, 30, 55),
                    outline=BLUE,
                    width=2,
                )
                label(d, str(si), cx, 423, f_tiny, L_BLUE)
            # tiny label below dot
            label(d, st[:9], cx, 438, ft(MONO, 7), col)

        frames.append(img)
    save_gif(frames, "06_outbox", duration=90)


# ══════════════════════════════════════════════════════════════════════════════
# 7. DEAD LETTER QUEUE
# ══════════════════════════════════════════════════════════════════════════════
def make_dlq():
    print("Generating DLQ GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    # Phases: 0=idle,1=msg_sent,2=consume_ok,3=fail1,4=fail2,5=fail3_dlq,
    #         6=ops_inspect,7=ops_replay,8=pause
    PHASE_LEN = [5, 5, 6, 5, 5, 6, 7, 6, 7]
    total = sum(PHASE_LEN)

    PROD_BOX = (30, 160, 160, 220)
    QUEUE_BOX = (200, 100, 480, 290)
    CONS_BOX = (530, 110, 720, 185)
    DLQ_BOX = (530, 220, 770, 360)
    OPS_BOX = (30, 280, 170, 370)

    def phase_of(f):
        acc = 0
        for i, pl in enumerate(PHASE_LEN):
            acc += pl
            if f < acc:
                return i, 1 - (acc - f) / pl
        return len(PHASE_LEN) - 1, 1.0

    retry_counts = {0: 0, 1: 0, 2: 0}  # msg slot: retry count
    dlq_msgs = []

    frames = []
    for fi in range(total):
        ph, prog = phase_of(fi)
        img, d = new_frame()

        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(d, "DEAD LETTER QUEUE (DLQ)", W // 2, 34, f_title, L_RED)
        rounded_rect(d, (660, 20, 770, 48), 5, (61, 21, 21), None)
        label(d, "ERROR HANDLING", 715, 34, f_badge, RED)

        # Producer
        pc = lerpC(BORDER, BLUE, pulse(fi / 3)) if ph == 1 else BORDER
        rounded_rect(d, PROD_BOX, 10, (20, 30, 50), pc, 2)
        label(d, "PRODUCER", 95, 183, f_label, L_BLUE)
        label(d, "publishes msgs", 95, 203, f_tiny, MUTED)

        # Main Queue
        rounded_rect(d, QUEUE_BOX, 10, SURFACE, BLUE, 2)
        rounded_rect(d, (200, 100, 480, 126), 8, (30, 58, 95), None)
        label(d, "MAIN QUEUE", 340, 113, f_label, L_BLUE)

        # Queue slot msgs
        slots = [
            ("msg_id: abc123", "OK", (26, 37, 64), (45, 78, 132)),
            ("msg_id: def456", "✗✗✗", (42, 16, 16), (77, 32, 32)),
            ("msg_id: ghi789", "OK", (26, 37, 64), (45, 78, 132)),
        ]
        for si, (txt, status, bg, brd) in enumerate(slots):
            bx0, by0 = 215, 135 + si * 45
            bx1, by1 = bx0 + 250, by0 + 30
            # highlight fail msg if ph>=3
            if si == 1 and ph >= 3:
                bg = (61, 16, 16)
                brd = (120, 32, 32)
            rounded_rect(d, (bx0, by0, bx1, by1), 5, bg, brd, 1)
            label(
                d,
                txt,
                bx0 + 125,
                by0 + 15,
                f_small,
                (150, 170, 210) if si != 1 else L_RED,
            )
            st_col = GREEN if status == "OK" else RED
            label(d, status, bx1 - 18, by0 + 15, f_small, st_col)

        # Retry counter on fail msg
        if ph >= 3:
            rc = min(ph - 2, 3)
            rounded_rect(d, (215, 220, 465, 240), 4, (61, 46, 16), None)
            label(
                d,
                f"def456 retry: {rc}/3{'  → DLQ' if rc >= 3 else ''}",
                340,
                230,
                f_tiny,
                L_AMBER,
            )

        # Consumer
        cc = (
            lerpC(BORDER, GREEN, pulse(fi / 3))
            if ph == 2
            else (lerpC(BORDER, RED, pulse(fi / 3)) if ph in (3, 4, 5) else BORDER)
        )
        rounded_rect(d, CONS_BOX, 10, (18, 32, 20), cc, 2)
        label(d, "CONSUMER", 625, 137, f_label, L_GREEN)
        label(d, "GROUP A", 625, 155, f_small, GREEN)
        status_txt = "processing…" if ph <= 2 else ("FAIL ✗" if ph <= 5 else "idle")
        status_col = MUTED if ph <= 2 else (RED if ph <= 5 else MUTED)
        label(d, status_txt, 625, 172, f_tiny, status_col)

        # DLQ box
        dlq_highlight = ph >= 5
        rounded_rect(
            d,
            DLQ_BOX,
            10,
            (26, 10, 10),
            RED if dlq_highlight else BORDER,
            3 if dlq_highlight else 1,
        )
        rounded_rect(
            d,
            (530, 220, 770, 246),
            8,
            (61, 21, 21) if dlq_highlight else (20, 22, 30),
            None,
        )
        label(
            d,
            "☠ DEAD LETTER QUEUE",
            650,
            233,
            f_label,
            L_RED if dlq_highlight else MUTED,
        )
        if ph >= 5:
            dlq_entries = [
                ("def456", "attempts: 3"),
                ("xyz999", "schema_err"),
                ("lmn000", "timeout ×5"),
            ]
            for ei, (mid, err) in enumerate(dlq_entries[: max(1, ph - 4)]):
                rounded_rect(
                    d,
                    (545, 255 + ei * 28, 765, 278 + ei * 28),
                    4,
                    (42, 16, 16),
                    (77, 32, 32),
                    1,
                )
                label(d, f"{mid}  ·  {err}", 655, 266 + ei * 28, f_tiny, L_RED)

        # Ops box
        ops_col = (
            lerpC(BORDER, PURPLE, min(prog, 1))
            if ph in (6, 7)
            else (PURPLE if ph >= 6 else BORDER)
        )
        rounded_rect(d, OPS_BOX, 10, (20, 18, 40), ops_col, 2)
        label(d, "OPS TEAM", 100, 303, f_label, L_PURP)
        label(d, "inspect / replay", 100, 323, f_small, PURPLE)
        label(d, "/ discard", 100, 340, f_small, PURPLE)

        # Animated arrows
        if ph >= 1:
            a = min(prog, 1) if ph == 1 else 1.0
            ex = int(lerp(160, 200, a))
            arrow(d, 160, 190, ex, 175, alpha_color(BLUE, a), width=2)
            label(d, "send", 178, 167, f_tiny, alpha_color(L_BLUE, a))

        if ph >= 2:
            a = min(prog, 1) if ph == 2 else 1.0
            ex = int(lerp(480, 530, a))
            arrow(d, 480, 150, ex, 147, alpha_color(GREEN, a), width=2)
            label(d, "consume", 502, 140, f_tiny, alpha_color(GREEN, a))

        if ph in (3, 4, 5):
            # fail arc back from consumer
            a = min(prog, 1)
            mid_x = int(lerp(530, 480, a))
            mid_y = 200
            dashed_arrow(d, 530, 155, mid_x, mid_y, alpha_color(RED, a), width=2)
            label(d, "FAIL", 548, 178, f_small, alpha_color(RED, a))

        if ph >= 5:
            a = min(prog, 1) if ph == 5 else 1.0
            arrow(d, 480, 200, 530, 255, alpha_color(RED, a), width=2)
            label(d, "→DLQ", 493, 228, f_tiny, alpha_color(RED, a))

        if ph >= 6:
            a = min(prog, 1) if ph == 6 else 1.0
            ex = int(lerp(170, 530, a))
            dashed_arrow(d, 170, 330, ex, 310, alpha_color(PURPLE, a), width=2)
            label(d, "inspect", 330, 323, f_tiny, alpha_color(L_PURP, a))

        if ph >= 7:
            a = min(prog, 1) if ph == 7 else 1.0
            ey = int(lerp(280, 165, a))
            dashed_arrow(d, 100, 280, 250, ey, alpha_color(AMBER, a), width=2)
            label(d, "replay", 140, 230, f_tiny, alpha_color(L_AMBER, a))

        # step indicator
        steps = [
            "idle",
            "send",
            "consume",
            "fail×1",
            "fail×2",
            "→DLQ",
            "inspect",
            "replay",
            "done",
        ]
        rounded_rect(d, (20, 400, 780, 445), 8, SURFACE, BORDER, 1)
        for si, st in enumerate(steps):
            cx = 50 + si * 87
            col = GREEN if si < ph else (L_RED if si == ph else MUTED)
            if si < ph:
                d.ellipse(
                    [(cx - 18, 413), (cx + 18, 433)], fill=(10, 35, 15), outline=GREEN
                )
                label(d, "✓", cx, 423, f_tiny, GREEN)
            elif si == ph:
                d.ellipse(
                    [(cx - 18, 413), (cx + 18, 433)],
                    fill=(35, 10, 10),
                    outline=RED,
                    width=2,
                )
                label(d, str(si), cx, 423, f_tiny, L_RED)
            label(d, st[:8], cx, 438, ft(MONO, 7), col)

        frames.append(img)
    save_gif(frames, "07_dlq", duration=95)


# ══════════════════════════════════════════════════════════════════════════════
# 1. EVENT SOURCING
# ══════════════════════════════════════════════════════════════════════════════
def make_event_sourcing():
    print("Generating Event Sourcing GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    EVENTS = [
        ("t=1", "OrderPlaced", "#42", "$150"),
        ("t=2", "ItemAdded", "shoe_01", "qty:2"),
        ("t=3", "PaymentOK", "tx_99", "stripe"),
        ("t=4", "Shipped", "UPS", "track#"),
    ]
    # Phases: show events one by one (4), then replay arrow, then projection, pause
    PHASE_LEN = [6, 6, 6, 6, 8, 8, 8]
    total = sum(PHASE_LEN)
    n_events = 4

    def phase_of(f):
        acc = 0
        for i, pl in enumerate(PHASE_LEN):
            acc += pl
            if f < acc:
                return i, 1 - (acc - f) / pl
        return len(PHASE_LEN) - 1, 1.0

    STATE_FIELDS = [
        ("order_id", "#42"),
        ("status", "SHIPPED"),
        ("amount", "$150"),
        ("items", "shoe_01 ×2"),
        ("payment", "stripe/tx_99"),
    ]

    frames = []
    for fi in range(total):
        ph, prog = phase_of(fi)
        img, d = new_frame()

        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(d, "EVENT SOURCING", W // 2, 34, f_title, L_PURP)
        rounded_rect(d, (660, 20, 770, 48), 5, (30, 26, 58), None)
        label(d, "STATE MGMT", 715, 34, f_badge, PURPLE)

        # Event store header
        rounded_rect(d, (20, 65, 780, 100), 8, (30, 26, 58), PURPLE, 2)
        label(d, "EVENT STORE  (append-only · immutable)", W // 2, 82, f_label, L_PURP)

        # Event cards
        EW, EH = 160, 90
        EY0 = 115
        for ei, (ts, name, val1, val2) in enumerate(EVENTS):
            ex0 = 25 + ei * (EW + 12)
            visible = ei < ph if ph < n_events else True
            a = min(prog, 1.0) if ph == ei else (1.0 if visible else 0.0)
            if a <= 0:
                continue
            ec = alpha_color(PURPLE, a * 0.9)
            rounded_rect(
                d,
                (ex0, EY0, ex0 + EW, EY0 + EH),
                8,
                alpha_color((28, 26, 46), a),
                ec,
                2,
            )
            # timestamp badge
            rounded_rect(
                d,
                (ex0, EY0, ex0 + EW, EY0 + 20),
                6,
                alpha_color((61, 46, 120), a),
                None,
            )
            label(
                d, ts, ex0 + EW // 2, EY0 + 10, f_tiny, alpha_color((109, 40, 217), a)
            )
            label(d, name, ex0 + EW // 2, EY0 + 38, f_small, alpha_color(L_PURP, a))
            label(d, val1, ex0 + EW // 2, EY0 + 56, f_tiny, alpha_color(TEXT, a))
            label(d, val2, ex0 + EW // 2, EY0 + 70, f_tiny, alpha_color(MUTED, a))

            # connecting arrow to next
            if ei < n_events - 1 and a > 0.5:
                next_visible = (ei + 1) < ph if ph < n_events else True
                na = 1.0 if next_visible else (min(prog, 1.0) if ph == ei + 1 else 0.0)
                arrow(
                    d,
                    ex0 + EW,
                    EY0 + EH // 2,
                    ex0 + EW + 10,
                    EY0 + EH // 2,
                    alpha_color(PURPLE, min(a, na)),
                    width=2,
                )

        # replay arrow (phase 4)
        if ph >= 4:
            a = min(prog, 1.0) if ph == 4 else 1.0
            ex = int(lerp(25, 25 + 4 * EW + 3 * 12, a))
            d.line([(25, 218), (ex, 218)], fill=alpha_color(PURPLE, a), width=2)
            # arrowhead only when near end
            if a > 0.9:
                arrow(d, ex - 4, 218, ex, 218, alpha_color(PURPLE, a), width=2, head=8)
            label(
                d,
                "← replay to rebuild state",
                W // 2,
                230,
                f_small,
                alpha_color((124, 58, 237), a),
            )

        # Current state projection (phase 5+)
        if ph >= 5:
            a = min(prog, 1.0) if ph == 5 else 1.0
            PX0, PY0, PX1, PY1 = 220, 255, 580, 390
            rounded_rect(
                d,
                (PX0, PY0, PX1, PY1),
                10,
                alpha_color(SURFACE, a),
                alpha_color(CYAN, a),
                2,
            )
            rounded_rect(
                d, (PX0, PY0, PX1, PY0 + 26), 8, alpha_color((12, 42, 48), a), None
            )
            label(
                d,
                "CURRENT STATE  (projection)",
                (PX0 + PX1) // 2,
                PY0 + 13,
                f_label,
                alpha_color(L_CYAN, a),
            )
            arrow(
                d,
                (PX0 + PX1) // 2,
                245,
                (PX0 + PX1) // 2,
                PY0 - 2,
                alpha_color(CYAN, a),
                width=2,
            )
            for ri, (k, v) in enumerate(STATE_FIELDS):
                ry = PY0 + 42 + ri * 24
                label(
                    d,
                    k + ":",
                    PX0 + 30,
                    ry,
                    f_small,
                    alpha_color(MUTED, a),
                    anchor="lm",
                )
                vc = GREEN if k == "status" else (alpha_color(TEXT, a))
                vc = alpha_color(vc, a) if isinstance(vc, tuple) else vc
                label(d, v, PX0 + 160, ry, f_small, vc, anchor="lm")

        # read models (phase 6)
        if ph >= 6:
            a = min(prog, 1.0) if ph == 6 else 1.0
            rounded_rect(
                d,
                (600, 255, 775, 390),
                8,
                alpha_color(SURFACE, a),
                alpha_color(BORDER, a),
                1,
            )
            label(d, "READ MODELS", 687, 272, f_small, alpha_color(MUTED, a))
            for ri, rm in enumerate(
                ["order_view", "analytics_db", "search_index", "audit_log"]
            ):
                label(
                    d,
                    "• " + rm,
                    687,
                    295 + ri * 22,
                    f_tiny,
                    alpha_color((100, 116, 139), a),
                )
            dashed_arrow(d, 580, 322, 598, 322, alpha_color(CYAN, a), width=1)

        # step indicator
        steps = ["idle", "t=1", "t=2", "t=3", "t=4", "replay", "project", "read models"]
        rounded_rect(d, (20, 400, 780, 445), 8, SURFACE, BORDER, 1)
        for si, st in enumerate(steps):
            cx = 50 + si * 100
            if si < ph:
                d.ellipse(
                    [(cx - 18, 413), (cx + 18, 433)], fill=(10, 35, 15), outline=GREEN
                )
                label(d, "✓", cx, 423, f_tiny, GREEN)
            elif si == ph:
                d.ellipse(
                    [(cx - 18, 413), (cx + 18, 433)],
                    fill=(20, 18, 38),
                    outline=PURPLE,
                    width=2,
                )
                label(d, str(si), cx, 423, f_tiny, L_PURP)
            col = GREEN if si < ph else (L_PURP if si == ph else MUTED)
            label(d, st[:9], cx, 438, ft(MONO, 7), col)

        frames.append(img)
    save_gif(frames, "01_event_sourcing", duration=100)


# ══════════════════════════════════════════════════════════════════════════════
# 8. SAGA PATTERN
# ══════════════════════════════════════════════════════════════════════════════
def make_saga():
    print("Generating Saga GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 11)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    SERVICES = [
        "ORDER\nSERVICE",
        "PAYMENT\nSERVICE",
        "INVENTORY\nSERVICE",
        "SHIPPING\nSERVICE",
    ]
    EVENTS_FW = ["OrderCreated", "PaymentDone", "StockReserved", "Dispatched"]
    EVENTS_BK = ["CancelOrder", "RefundPayment", "—"]
    SW = 135
    SH = 75
    SY = 110
    SXS = [30, 210, 390, 570]

    # Phases: 0-3 happy (each svc lights up), 4 happy complete,
    #         5 reset, 6-8 saga fail at inventory, 9 compensate payment, 10 compensate order, 11 done
    PHASE_LEN = [7, 7, 7, 7, 8, 6, 7, 7, 7, 7, 7, 8]
    total = sum(PHASE_LEN)

    def phase_of(f):
        acc = 0
        for i, pl in enumerate(PHASE_LEN):
            acc += pl
            if f < acc:
                return i, 1 - (acc - f) / pl
        return len(PHASE_LEN) - 1, 1.0

    frames = []
    for fi in range(total):
        ph, prog = phase_of(fi)
        img, d = new_frame()

        is_fail_saga = ph >= 6

        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(d, "SAGA PATTERN (Choreography)", W // 2, 34, f_title, L_GREEN)
        mode = "● COMPENSATION FLOW" if is_fail_saga else "● HAPPY PATH"
        mode_col = RED if is_fail_saga else GREEN
        label(d, mode, 650, 34, f_badge, mode_col)

        # Draw service boxes
        for si, svc in enumerate(SERVICES):
            sx0 = SXS[si]
            happy_active = (not is_fail_saga) and ph == si
            fail_active = is_fail_saga and ph == (si + 6)
            comp_active = is_fail_saga and (
                (si == 2 and ph == 8) or (si == 1 and ph == 9) or (si == 0 and ph == 10)
            )

            if si == 2 and is_fail_saga and ph >= 8:
                col = RED
                bg = (42, 10, 10)
            elif not is_fail_saga and ph > si:
                col = GREEN
                bg = (18, 32, 20)
            elif happy_active:
                col = lerpC(BORDER, GREEN, min(prog, 1))
                bg = (14, 28, 16)
            elif comp_active:
                col = lerpC(BORDER, AMBER, min(prog, 1))
                bg = (38, 28, 10)
            else:
                col = BORDER
                bg = SURFACE

            rounded_rect(d, (sx0, SY, sx0 + SW, SY + SH), 10, bg, col, 2)
            lines = svc.split("\n")
            label(
                d,
                lines[0],
                sx0 + SW // 2,
                SY + 22,
                f_label,
                L_GREEN
                if col == GREEN
                else (L_RED if col == RED else L_AMBER if comp_active else MUTED),
            )
            label(
                d,
                lines[1],
                sx0 + SW // 2,
                SY + 38,
                f_small,
                (
                    GREEN
                    if col == GREEN
                    else (RED if col == RED else AMBER if comp_active else MUTED)
                ),
            )

            # status line
            if not is_fail_saga and ph > si:
                label(d, "✓ DONE", sx0 + SW // 2, SY + 60, f_tiny, GREEN)
            elif si == 2 and is_fail_saga and ph >= 8:
                label(d, "✗ OUT OF STOCK", sx0 + SW // 2, SY + 60, f_tiny, RED)
            elif comp_active or (
                is_fail_saga and ((si == 1 and ph >= 9) or (si == 0 and ph >= 10))
            ):
                label(d, "↩ COMPENSATED", sx0 + SW // 2, SY + 60, f_tiny, AMBER)

        # Forward event arrows (happy path)
        if not is_fail_saga:
            for ai in range(min(ph, 3)):
                ax0 = SXS[ai] + SW
                ax1 = SXS[ai + 1]
                a = min(prog, 1.0) if ph == ai + 1 else 1.0
                ex = int(lerp(ax0, ax1, a))
                arrow(d, ax0, SY + 30, ex, SY + 30, alpha_color(GREEN, a), width=2)
                label(
                    d,
                    EVENTS_FW[ai],
                    (ax0 + ax1) // 2,
                    SY + 20,
                    f_tiny,
                    alpha_color(GREEN, a),
                )

        # Fail path forward arrows (up to inventory)
        if is_fail_saga:
            for ai in range(2):
                arrow(d, SXS[ai] + SW, SY + 30, SXS[ai + 1], SY + 30, GREEN, width=2)
                label(
                    d,
                    EVENTS_FW[ai],
                    (SXS[ai] + SW + SXS[ai + 1]) // 2,
                    SY + 20,
                    f_tiny,
                    GREEN,
                )
            # fail X on inventory
            if ph >= 8:
                a = min(prog, 1.0) if ph == 8 else 1.0
                cx = SXS[2] + SW // 2
                d.ellipse(
                    [(cx - 18, SY + SH + 8), (cx + 18, SY + SH + 34)],
                    fill=alpha_color((61, 20, 20), a),
                    outline=alpha_color(RED, a),
                    width=2,
                )
                label(d, "✗", cx, SY + SH + 21, f_label, alpha_color(RED, a))

            # Compensation arrow: inventory→payment
            if ph >= 9:
                a = min(prog, 1.0) if ph == 9 else 1.0
                ex = int(lerp(SXS[2], SXS[1] + SW, a))
                dashed_arrow(
                    d, SXS[2], SY + 55, ex, SY + 55, alpha_color(RED, a), width=2
                )
                label(
                    d,
                    EVENTS_BK[1],
                    (SXS[1] + SW + SXS[2]) // 2,
                    SY + 68,
                    f_tiny,
                    alpha_color(L_RED, a),
                )

            # Compensation arrow: payment→order
            if ph >= 10:
                a = min(prog, 1.0) if ph == 10 else 1.0
                ex = int(lerp(SXS[1], SXS[0] + SW, a))
                dashed_arrow(
                    d, SXS[1], SY + 60, ex, SY + 60, alpha_color(AMBER, a), width=2
                )
                label(
                    d,
                    EVENTS_BK[0],
                    (SXS[0] + SW + SXS[1]) // 2,
                    SY + 72,
                    f_tiny,
                    alpha_color(L_AMBER, a),
                )

        # Key concepts panel
        rounded_rect(d, (20, 230, 780, 385), 8, SURFACE, BORDER, 1)
        label(d, "KEY CONCEPTS", W // 2, 248, f_label, MUTED)
        concepts = [
            (
                GREEN,
                "Each service reacts to domain events autonomously — no distributed lock",
            ),
            (RED, "Compensating transactions restore consistency (not ACID rollback)"),
            (
                AMBER,
                "Eventual consistency — intermediate states are visible to observers",
            ),
            (CYAN, "Orchestrator variant uses central saga coordinator instead"),
            (PURPLE, "Idempotency keys prevent duplicate compensation on retry"),
        ]
        for ci, (col, txt) in enumerate(concepts):
            cy = 270 + ci * 22
            d.ellipse([(32, cy - 5), (42, cy + 5)], fill=col)
            label(d, txt, 55, cy, f_tiny, (180, 190, 200), anchor="lm")

        # step indicator
        steps = [
            "idle",
            "order",
            "payment",
            "inventory",
            "shipping",
            "happy!",
            "reset",
            "order",
            "pay",
            "stock✗",
            "↩pay",
            "↩ord",
            "done",
        ]
        rounded_rect(d, (20, 400, 780, 445), 8, SURFACE, BORDER, 1)
        for si, st in enumerate(steps[: min(ph + 2, len(steps))]):
            cx = 35 + si * 57
            col = (
                GREEN
                if si < ph and not is_fail_saga
                else (RED if si < ph and is_fail_saga else MUTED)
            )
            if si < ph:
                d.ellipse(
                    [(cx - 14, 413), (cx + 14, 433)],
                    fill=(10, 25, 10),
                    outline=GREEN,
                    width=1,
                )
                label(d, "✓", cx, 423, f_tiny, GREEN)
            elif si == ph:
                c = RED if is_fail_saga else BLUE
                d.ellipse(
                    [(cx - 14, 413), (cx + 14, 433)],
                    fill=(15, 10, 10) if is_fail_saga else (10, 20, 40),
                    outline=c,
                    width=2,
                )
                label(d, str(si), cx, 423, f_tiny, c)
            label(d, st[:6], cx, 438, ft(MONO, 7), col)

        frames.append(img)
    save_gif(frames, "08_saga", duration=100)


# ══════════════════════════════════════════════════════════════════════════════
# 3. CONSUMER GROUPS & PARTITIONS
# ══════════════════════════════════════════════════════════════════════════════
def make_consumer_groups():
    print("Generating Consumer Groups GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    # Layout
    TOPIC_X0, TOPIC_Y0, TOPIC_X1, TOPIC_Y1 = 155, 65, 545, 355
    PROD_BOX = (20, 180, 140, 240)
    CONS_XS = [580, 580, 580]
    CONS_YS = [90, 180, 270]
    CONS_W, CONS_H = 175, 75
    PARTS = 3
    P_HEIGHTS = [80, 80, 80]
    P_Y0S = [90, 180, 270]
    MSG_COUNT = [6, 5, 7]  # messages per partition

    # Phases: 0=idle, 1=producer_sends(6 sub), 2=consumers_assigned,
    #         3=consumers_reading(animated offsets), 4=rebalance_flash, 5=done
    PHASE_LEN = [5, 14, 6, 14, 8, 7]
    total = sum(PHASE_LEN)

    def phase_of(f):
        acc = 0
        for i, pl in enumerate(PHASE_LEN):
            acc += pl
            if f < acc:
                return i, 1 - (acc - f) / pl
        return len(PHASE_LEN) - 1, 1.0

    frames = []
    for fi in range(total):
        ph, prog = phase_of(fi)
        img, d = new_frame()

        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(d, "CONSUMER GROUPS & PARTITIONS (Kafka)", W // 2, 34, f_title, L_CYAN)
        rounded_rect(d, (660, 20, 770, 48), 5, (12, 40, 50), None)
        label(d, "SCALABILITY", 715, 34, f_badge, CYAN)

        # Topic border
        rounded_rect(d, (TOPIC_X0, TOPIC_Y0, TOPIC_X1, TOPIC_Y1), 10, SURFACE, CYAN, 2)
        rounded_rect(
            d, (TOPIC_X0, TOPIC_Y0, TOPIC_X1, TOPIC_Y0 + 28), 8, (12, 42, 48), None
        )
        label(
            d,
            "TOPIC: orders",
            (TOPIC_X0 + TOPIC_X1) // 2,
            TOPIC_Y0 + 14,
            f_label,
            L_CYAN,
        )

        # Partitions
        for pi in range(PARTS):
            py0 = TOPIC_Y0 + 35 + pi * 90
            py1 = py0 + 75
            rounded_rect(
                d,
                (TOPIC_X0 + 15, py0, TOPIC_X1 - 15, py1),
                6,
                (15, 26, 38),
                (21, 92, 117),
                1,
            )
            label(d, f"P{pi}", TOPIC_X0 + 30, py0 + 20, f_label, L_CYAN)

            # Message slots
            n_msg = MSG_COUNT[pi]
            slot_w = 44
            slot_h = 24
            slot_y = py0 + 10
            # how many msgs to show
            shown = n_msg if ph >= 1 else 0
            if ph == 1:
                # animate one by one
                shown = min(n_msg, int(prog * n_msg * 1.2))

            committed_offset = 0
            if ph >= 3:
                # progress through reading
                committed_offset = int(prog * (n_msg - 1))

            for mi in range(n_msg):
                mx0 = TOPIC_X0 + 50 + mi * (slot_w + 4)
                if mi >= shown:
                    break
                is_consumed = ph >= 3 and mi <= committed_offset
                is_current = ph >= 3 and mi == committed_offset + 1
                bg = (
                    (18, 40, 18)
                    if is_consumed
                    else ((30, 58, 95) if not is_consumed else (18, 30, 50))
                )
                brd = (
                    (16, 185, 129)
                    if is_consumed
                    else ((245, 159, 11) if is_current else (45, 78, 132))
                )
                rounded_rect(
                    d, (mx0, slot_y, mx0 + slot_w, slot_y + slot_h), 3, bg, brd, 1
                )
                label(
                    d,
                    str(mi),
                    mx0 + slot_w // 2,
                    slot_y + slot_h // 2,
                    f_tiny,
                    (74, 222, 128) if is_consumed else L_BLUE,
                )

            # offset marker
            if ph >= 3:
                ox = TOPIC_X0 + 50 + committed_offset * (slot_w + 4) + slot_w
                label(d, "↑ offset", ox, slot_y + slot_h + 12, f_tiny, AMBER)

            label(d, f"offset →", TOPIC_X0 + 50, py0 + 52, f_tiny, (71, 85, 105))

        # Producer
        p_col = lerpC(BORDER, BLUE, pulse(fi / 3)) if ph == 1 else BORDER
        rounded_rect(d, PROD_BOX, 10, (20, 30, 50), p_col, 2)
        label(d, "PRODUCER", 80, 203, f_label, L_BLUE)
        label(d, "key→partition", 80, 222, f_tiny, MUTED)

        # Arrows producer→topic
        if ph >= 1:
            a = min(prog * 3, 1.0)
            arrow(d, 140, 205, TOPIC_X0, P_Y0S[0] + 35, alpha_color(BLUE, a), width=2)
            arrow(
                d,
                140,
                210,
                TOPIC_X0,
                P_Y0S[1] + 35,
                alpha_color(BLUE, a * 0.85),
                width=2,
            )
            arrow(
                d,
                140,
                215,
                TOPIC_X0,
                P_Y0S[2] + 35,
                alpha_color(BLUE, a * 0.7),
                width=2,
            )

        # Consumer Group
        CG_X0, CG_Y0, CG_X1, CG_Y1 = 575, 65, 765, 355
        rounded_rect(d, (CG_X0, CG_Y0, CG_X1, CG_Y1), 10, SURFACE, PURPLE, 2)
        rounded_rect(d, (CG_X0, CG_Y0, CG_X1, CG_Y0 + 28), 8, (30, 26, 58), None)
        label(d, "GROUP: analytics", (CG_X0 + CG_X1) // 2, CG_Y0 + 14, f_label, L_PURP)

        CONS_NAMES = ["Consumer A", "Consumer B", "Consumer C"]
        CONS_PARTS = ["P0", "P1", "P2"]
        for ci in range(PARTS):
            cy0 = CG_Y0 + 35 + ci * 90
            cy1 = cy0 + 70
            a = min((fi - sum(PHASE_LEN[:2])) / 5, 1.0) if ph >= 2 else 0.0
            a = max(0.0, min(a, 1.0))
            c_active = ph == 3 and True
            rounded_rect(
                d,
                (CG_X0 + 10, cy0, CG_X1 - 10, cy1),
                6,
                alpha_color((28, 26, 46), a),
                alpha_color(PURPLE, a),
                1,
            )
            label(
                d,
                CONS_NAMES[ci],
                (CG_X0 + CG_X1) // 2,
                cy0 + 18,
                f_label,
                alpha_color(L_PURP, a),
            )
            label(
                d,
                f"assigned: {CONS_PARTS[ci]}",
                (CG_X0 + CG_X1) // 2,
                cy0 + 34,
                f_small,
                alpha_color(PURPLE, a),
            )
            lag = [1, 2, 1][ci]
            lag_col = GREEN if lag <= 1 else RED
            if ph >= 3:
                offset_shown = int(prog * (MSG_COUNT[ci] - 1))
                label(
                    d,
                    f"committed: {offset_shown}",
                    (CG_X0 + CG_X1) // 2,
                    cy0 + 50,
                    f_tiny,
                    alpha_color(TEXT, a),
                )
                label(
                    d,
                    f"lag: {max(0, MSG_COUNT[ci] - 1 - offset_shown)}",
                    (CG_X0 + CG_X1) // 2,
                    cy0 + 62,
                    f_tiny,
                    alpha_color(lag_col, a),
                )

            # Arrow topic→consumer
            if ph >= 2:
                arrow(
                    d,
                    TOPIC_X1 + 2,
                    P_Y0S[ci] + 35,
                    CG_X0 + 8,
                    cy0 + 35,
                    alpha_color(PURPLE, a),
                    width=2,
                )

        # Rebalance flash
        if ph == 4:
            a = min(prog, 1.0)
            rounded_rect(
                d,
                (150, 370, 630, 395),
                8,
                alpha_color((30, 26, 58), a),
                alpha_color(RED, a),
                2,
            )
            label(
                d,
                "⚡ REBALANCE — consumer joined/left, reassigning partitions",
                390,
                382,
                f_small,
                alpha_color(L_RED, a),
            )

        # step indicator
        steps = ["idle", "producing", "assigned", "consuming", "rebalance", "✓ done"]
        rounded_rect(d, (20, 400, 780, 445), 8, SURFACE, BORDER, 1)
        for si, st in enumerate(steps):
            cx = 70 + si * 127
            col = CYAN if si == ph else (GREEN if si < ph else MUTED)
            if si < ph:
                d.ellipse(
                    [(cx - 18, 413), (cx + 18, 433)], fill=(10, 35, 15), outline=GREEN
                )
                label(d, "✓", cx, 423, f_tiny, GREEN)
            elif si == ph:
                d.ellipse(
                    [(cx - 18, 413), (cx + 18, 433)],
                    fill=(10, 28, 38),
                    outline=CYAN,
                    width=2,
                )
                label(d, str(si), cx, 423, f_tiny, L_CYAN)
            label(d, st[:10], cx, 438, ft(MONO, 7), col)

        frames.append(img)
    save_gif(frames, "03_consumer_groups", duration=90)


# ══════════════════════════════════════════════════════════════════════════════
# 9. CIRCUIT BREAKER
# ══════════════════════════════════════════════════════════════════════════════
def make_circuit_breaker():
    print("Generating Circuit Breaker GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 13)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    # State machine animation:
    # 0 idle/closed, 1 requests flowing (ok), 2 failures building,
    # 3 TRIP to OPEN, 4 OPEN (fast fail), 5 timeout→half-open, 6 probe,
    # 7 probe success→close, 8 pause
    PHASE_LEN = [5, 8, 8, 5, 8, 5, 6, 6, 7]
    total = sum(PHASE_LEN)

    CLOSED_C = (120, 260)
    OPEN_C = (390, 145)
    HALF_C = (620, 300)
    R = 75

    def phase_of(f):
        acc = 0
        for i, pl in enumerate(PHASE_LEN):
            acc += pl
            if f < acc:
                return i, 1 - (acc - f) / pl
        return len(PHASE_LEN) - 1, 1.0

    def draw_state_circle(d, cx, cy, r, state, active, progress, phase):
        if state == "CLOSED":
            col = GREEN if active else lerpC(BORDER, (30, 80, 30), 0.3)
            bg = (10, 30, 10) if active else (12, 16, 20)
            txt_col = L_GREEN if active else MUTED
            status = "requests flow" if active else "monitoring"
        elif state == "OPEN":
            col = RED if active else lerpC(BORDER, (80, 20, 20), 0.3)
            bg = (30, 8, 8) if active else (14, 10, 10)
            txt_col = L_RED if active else MUTED
            status = "fast fail ⚡" if active else "—"
        else:  # HALF
            col = AMBER if active else lerpC(BORDER, (70, 60, 10), 0.3)
            bg = (28, 22, 6) if active else (14, 12, 8)
            txt_col = L_AMBER if active else MUTED
            status = "probing…" if active else "—"

        d.ellipse(
            [(cx - r, cy - r), (cx + r, cy + r)],
            fill=bg,
            outline=col,
            width=3 if active else 1,
        )
        label(d, state, cx, cy - 12, f_label, txt_col)
        label(d, status, cx, cy + 8, f_small, col if active else MUTED)

    frames = []
    for fi in range(total):
        ph, prog = phase_of(fi)
        img, d = new_frame()

        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(d, "CIRCUIT BREAKER PATTERN", W // 2, 34, f_title, (251, 146, 60))
        rounded_rect(d, (660, 20, 770, 48), 5, (42, 26, 10), None)
        label(d, "RESILIENCE", 715, 34, f_badge, (251, 146, 60))

        # Draw the three state circles
        is_closed = ph in (0, 1, 2, 7, 8)
        is_open = ph in (3, 4, 5)
        is_half = ph in (5, 6)
        if ph == 5:
            is_open = True
            is_half = True

        draw_state_circle(d, *CLOSED_C, R, "CLOSED", is_closed, prog, ph)
        draw_state_circle(d, *OPEN_C, R, "OPEN", is_open, prog, ph)
        draw_state_circle(d, *HALF_C, R, "HALF-OPEN", is_half, prog, ph)

        # Failure counter inside closed state
        if ph in (1, 2):
            count = 0 if ph == 1 else int(prog * 5)
            col = GREEN if count < 3 else (AMBER if count < 5 else RED)
            label(d, f"failures: {count}/5", CLOSED_C[0], CLOSED_C[1] + 28, f_tiny, col)

        # Transition arrows
        # CLOSED → OPEN (trip)
        if ph >= 3:
            a = min(prog, 1.0) if ph == 3 else 1.0
            ax0 = CLOSED_C[0] + R
            ay0 = CLOSED_C[1] - 20
            ax1 = OPEN_C[0] - R
            ay1 = OPEN_C[1] + 20
            ex = int(lerp(ax0, ax1, a))
            ey = int(lerp(ay0, ay1, a))
            arrow(d, ax0, ay0, ex, ey, alpha_color(RED, a), width=3)
            mid_x = (ax0 + ax1) // 2
            mid_y = (ay0 + ay1) // 2
            rounded_rect(
                d,
                (mid_x - 50, mid_y - 22, mid_x + 50, mid_y - 2),
                4,
                alpha_color((61, 15, 15), a),
                None,
            )
            label(d, "failures≥5  TRIP", mid_x, mid_y - 12, f_tiny, alpha_color(RED, a))

        # OPEN → HALF-OPEN (timeout)
        if ph >= 5:
            a = min(prog, 1.0) if ph == 5 else 1.0
            ax0 = OPEN_C[0] + 50
            ay0 = OPEN_C[1] + R
            ax1 = HALF_C[0] - R + 10
            ay1 = HALF_C[1] - 30
            ex = int(lerp(ax0, ax1, a))
            ey = int(lerp(ay0, ay1, a))
            arrow(d, ax0, ay0, ex, ey, alpha_color(AMBER, a), width=2)
            rounded_rect(
                d,
                (ax0 + 30, ay0 + 20, ax0 + 140, ay0 + 40),
                4,
                alpha_color((42, 34, 6), a),
                None,
            )
            label(
                d, "timeout expires", ax0 + 85, ay0 + 30, f_tiny, alpha_color(AMBER, a)
            )

        # HALF-OPEN → CLOSED (success)
        if ph >= 7:
            a = min(prog, 1.0) if ph == 7 else 1.0
            ax0 = HALF_C[0] - 60
            ay0 = HALF_C[1] + R - 10
            ax1 = CLOSED_C[0] + 40
            ay1 = CLOSED_C[1] + R - 10
            # curve via bottom
            pts = [
                (
                    int(lerp(ax0, ax1, t)),
                    int(lerp(ay0, ay1, t) + 40 * math.sin(math.pi * t)),
                )
                for t in [i / 20 for i in range(21)]
            ]
            visible_pts = pts[: max(2, int(a * 20))]
            if len(visible_pts) >= 2:
                d.line(visible_pts, fill=alpha_color(GREEN, a), width=2)
            if a > 0.9:
                arrow(
                    d,
                    ax1 + 5,
                    ay1 - 5,
                    ax1,
                    ay1,
                    alpha_color(GREEN, a),
                    width=2,
                    head=8,
                )
            label(
                d,
                "probe success  RESET",
                (ax0 + ax1) // 2,
                ay0 + 70,
                f_tiny,
                alpha_color(GREEN, a),
            )

        # Fast fail visualization in OPEN state
        if ph == 4:
            n = int(prog * 6)
            for xi in range(n):
                bx = 50 + xi * 60
                rounded_rect(
                    d, (bx, 350, bx + 50, 375), 5, (35, 10, 10), (120, 30, 30), 1
                )
                label(d, "FAIL", bx + 25, 362, f_tiny, RED)
                # arrow to caller
                arrow(d, bx + 25, 350, bx + 25, 330, RED, width=1, head=6)
            if n > 0:
                label(
                    d,
                    "caller gets fast-fail (no downstream call)",
                    W // 2,
                    390,
                    f_small,
                    L_RED,
                )

        # Probe visualization in HALF-OPEN
        if ph == 6:
            a = min(prog, 1.0)
            bx = HALF_C[0]
            by = HALF_C[1] + R + 10
            rounded_rect(
                d,
                (bx - 55, by, bx + 55, by + 24),
                5,
                alpha_color((20, 30, 20), a),
                alpha_color(GREEN, a),
                1,
            )
            label(d, "probe request →", bx, by + 12, f_small, alpha_color(GREEN, a))

        # Status description
        status_msgs = {
            0: "CLOSED: Normal operation, counting failures",
            1: "CLOSED: Requests flowing to downstream service",
            2: "CLOSED: Failures accumulating… threshold approaching",
            3: "TRIPPING: Failure threshold breached — opening circuit",
            4: "OPEN: All requests rejected immediately (fast fail)",
            5: "OPEN→HALF-OPEN: Reset timeout expired, allowing probe",
            6: "HALF-OPEN: Single probe request sent to test health",
            7: "HALF-OPEN→CLOSED: Probe succeeded — resetting circuit",
            8: "CLOSED: Circuit reset, normal operation resumed ✓",
        }
        rounded_rect(d, (20, 400, 780, 445), 8, SURFACE, BORDER, 1)
        msg = status_msgs.get(ph, "")
        col = [GREEN, GREEN, AMBER, RED, RED, AMBER, AMBER, GREEN, GREEN][ph]
        label(d, msg, W // 2, 422, f_small, col)

        frames.append(img)
    save_gif(frames, "09_circuit_breaker", duration=95)


# ══════════════════════════════════════════════════════════════════════════════
# 10. CQRS
# ══════════════════════════════════════════════════════════════════════════════
def make_cqrs():
    print("Generating CQRS GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    # Phases:
    # 0=idle  1=client_sends_cmd  2=cmd_handler_writes  3=event_emitted
    # 4=projections_update  5=client_sends_query  6=query_reads  7=response  8=pause
    PHASES = [5, 6, 6, 6, 7, 6, 6, 6, 7]
    get_phase, total = phase_fn(PHASES)

    # Layout
    CLIENT_BOX = (20, 175, 140, 245)
    CMD_BOX = (185, 80, 345, 155)
    WRITE_DB = (185, 195, 345, 285)
    EVENT_BUS = (185, 305, 345, 370)
    PROJ_BOXES = [(390, 80, 530, 145), (390, 165, 530, 230), (390, 250, 530, 315)]
    READ_DB = (390, 340, 530, 395)
    QUERY_BOX = (575, 80, 745, 155)
    RESP_BOX = (575, 195, 745, 265)

    frames = []
    for fi in range(total):
        ph, prog = get_phase(fi)
        img, d = new_frame()

        # Title
        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(
            d,
            "CQRS  —  Command Query Responsibility Segregation",
            W // 2,
            34,
            f_title,
            L_INDIGO,
        )
        rounded_rect(d, (670, 20, 770, 48), 5, (20, 20, 50), None)
        label(d, "SEPARATION", 720, 34, f_badge, INDIGO)

        # ── Write side label ──
        rounded_rect(d, (175, 60, 360, 400), 10, (12, 12, 20), (40, 40, 80), 1)
        label(d, "WRITE SIDE", 267, 75, f_tiny, (80, 80, 160))

        # ── Read side label ──
        rounded_rect(d, (380, 60, 545, 400), 10, (10, 20, 15), (30, 70, 50), 1)
        label(d, "READ SIDE", 462, 75, f_tiny, (50, 130, 80))

        # ── Client ──
        c_act = ph in (1, 5)
        cc = lerpC(BORDER, INDIGO, pulse(fi / 4)) if c_act else BORDER
        rounded_rect(d, CLIENT_BOX, 10, (18, 18, 40), cc, 2)
        label(d, "CLIENT", 80, 200, f_label, L_INDIGO)
        label(d, "app / API", 80, 218, f_tiny, MUTED)
        if ph < 5:
            label(
                d,
                "→ COMMAND",
                80,
                234,
                f_tiny,
                alpha_color(
                    L_INDIGO, min(prog, 1) if ph == 1 else (1 if ph > 1 else 0.0)
                ),
            )
        else:
            label(
                d,
                "→ QUERY",
                80,
                234,
                f_tiny,
                alpha_color(
                    L_GREEN, min(prog, 1) if ph == 5 else (1 if ph > 5 else 0.0)
                ),
            )

        # ── Command Handler ──
        ch_a = min(prog, 1) if ph == 2 else (1 if ph > 2 else 0.0)
        rounded_rect(
            d, CMD_BOX, 8, alpha_color((20, 18, 48), ch_a), alpha_color(INDIGO, ch_a), 2
        )
        label(d, "COMMAND HANDLER", 265, 105, f_small, alpha_color(L_INDIGO, ch_a))
        label(d, "validate + execute", 265, 122, f_tiny, alpha_color(MUTED, ch_a))
        label(d, "PlaceOrderCmd", 265, 138, f_tiny, alpha_color((109, 40, 217), ch_a))

        # ── Write DB ──
        wd_a = min(prog, 1) if ph == 2 else (1 if ph > 2 else 0.0)
        rounded_rect(
            d,
            WRITE_DB,
            8,
            alpha_color(SURFACE, wd_a),
            alpha_color(INDIGO, wd_a * 0.7),
            2,
        )
        rounded_rect(d, (185, 195, 345, 218), 6, alpha_color((30, 26, 60), wd_a), None)
        label(d, "WRITE DB", 265, 207, f_small, alpha_color(L_INDIGO, wd_a))
        label(d, "orders (normalized)", 265, 228, f_tiny, alpha_color(MUTED, wd_a))
        label(
            d, "strong consistency", 265, 244, f_tiny, alpha_color((80, 70, 140), wd_a)
        )
        label(
            d,
            "optimized for writes",
            265,
            260,
            f_tiny,
            alpha_color((60, 55, 110), wd_a),
        )

        # ── Event Bus ──
        eb_a = min(prog, 1) if ph == 3 else (1 if ph > 3 else 0.0)
        rounded_rect(
            d,
            EVENT_BUS,
            8,
            alpha_color((20, 14, 34), eb_a),
            alpha_color(PURPLE, eb_a),
            2,
        )
        label(d, "EVENT BUS", 265, 328, f_small, alpha_color(L_PURP, eb_a))
        label(d, "OrderPlaced event", 265, 348, f_tiny, alpha_color(PURPLE, eb_a))

        # ── Projections ──
        PROJ_NAMES = ["OrderListView", "DashboardProj", "SearchIndex"]
        PROJ_COLORS = [CYAN, GREEN, TEAL]
        PROJ_L = [L_CYAN, L_GREEN, L_TEAL]
        for pi, (pbox, pname, pc, plc) in enumerate(
            zip(PROJ_BOXES, PROJ_NAMES, PROJ_COLORS, PROJ_L)
        ):
            pa = min(prog, 1) if ph == 4 else (1 if ph > 4 else 0.0)
            delay = pi * 0.25
            pa = max(0, min((pa - delay) / 0.6, 1.0)) if ph == 4 else pa
            rounded_rect(
                d, pbox, 6, alpha_color((10, 22, 18), pa), alpha_color(pc, pa), 1
            )
            label(
                d,
                pname,
                (pbox[0] + pbox[2]) // 2,
                (pbox[1] + pbox[3]) // 2 - 8,
                f_tiny,
                alpha_color(plc, pa),
            )
            label(
                d,
                "projection",
                (pbox[0] + pbox[2]) // 2,
                (pbox[1] + pbox[3]) // 2 + 8,
                ft(MONO, 8),
                alpha_color(pc, pa),
            )

        # ── Read DB ──
        rd_a = min(prog, 1) if ph == 4 else (1 if ph > 4 else 0.0)
        rounded_rect(
            d, READ_DB, 8, alpha_color(SURFACE, rd_a), alpha_color(GREEN, rd_a * 0.8), 2
        )
        rounded_rect(d, (390, 340, 530, 360), 6, alpha_color((12, 30, 18), rd_a), None)
        label(d, "READ DB", 460, 352, f_small, alpha_color(L_GREEN, rd_a))
        label(d, "denormalized views", 460, 372, f_tiny, alpha_color(MUTED, rd_a))

        # ── Query Handler ──
        qh_a = min(prog, 1) if ph == 6 else (1 if ph > 6 else 0.0)
        rounded_rect(
            d,
            QUERY_BOX,
            8,
            alpha_color((12, 26, 18), qh_a),
            alpha_color(GREEN, qh_a),
            2,
        )
        label(d, "QUERY HANDLER", 660, 105, f_small, alpha_color(L_GREEN, qh_a))
        label(d, "read-only", 660, 122, f_tiny, alpha_color(MUTED, qh_a))
        label(d, "GetOrdersQuery", 660, 138, f_tiny, alpha_color(GREEN, qh_a))

        # ── Response ──
        rsp_a = min(prog, 1) if ph == 7 else (1 if ph > 7 else 0.0)
        rounded_rect(
            d,
            RESP_BOX,
            8,
            alpha_color((12, 26, 18), rsp_a),
            alpha_color(TEAL, rsp_a),
            2,
        )
        label(d, "RESPONSE", 660, 218, f_small, alpha_color(L_TEAL, rsp_a))
        label(d, "[{id:42, status:..}]", 660, 238, f_tiny, alpha_color(L_GREEN, rsp_a))

        # ── Animated arrows ──
        # 1: Client → Command Handler
        if ph >= 1:
            a = min(prog, 1) if ph == 1 else 1.0
            ex = int(lerp(140, 185, a))
            arrow(d, 140, 195, ex, 117, alpha_color(INDIGO, a), width=2)
            label(d, "Command", 160, 148, f_tiny, alpha_color(L_INDIGO, a))

        # 2: CMD → Write DB
        if ph >= 2:
            a = min(prog, 1) if ph == 2 else 1.0
            ey = int(lerp(155, 195, a))
            arrow(d, 265, 155, 265, ey, alpha_color(INDIGO, a), width=2)

        # 3: Write DB → Event Bus
        if ph >= 3:
            a = min(prog, 1) if ph == 3 else 1.0
            ey = int(lerp(285, 305, a))
            arrow(d, 265, 285, 265, ey, alpha_color(PURPLE, a), width=2)
            label(d, "emit", 278, 295, f_tiny, alpha_color(L_PURP, a))

        # 4: Event Bus → Projections (fan out)
        if ph >= 4:
            a = min(prog, 1) if ph == 4 else 1.0
            for pi, pbox in enumerate(PROJ_BOXES):
                delay = pi * 0.25
                pa = max(0, min((a - delay) / 0.6, 1.0))
                py = (pbox[1] + pbox[3]) // 2
                ex = int(lerp(345, pbox[0], pa))
                arrow(d, 345, 337, ex, py, alpha_color(PROJ_COLORS[pi], pa), width=2)

        # Projection → Read DB
        if ph >= 4:
            a = min(prog, 1) if ph == 4 else 1.0
            arrow(d, 460, 315, 460, 340, alpha_color(GREEN, a), width=1)

        # 5: Client → Query Handler
        if ph >= 5:
            a = min(prog, 1) if ph == 5 else 1.0
            ex = int(lerp(140, 575, a))
            ey = int(lerp(205, 117, a))
            arrow(d, 140, 205, ex, ey, alpha_color(GREEN, a), width=2)
            label(d, "Query", 360, 148, f_tiny, alpha_color(L_GREEN, a))

        # 6: Query Handler → Read DB
        if ph >= 6:
            a = min(prog, 1) if ph == 6 else 1.0
            ex = int(lerp(575, 530, a))
            arrow(d, 575, 130, ex, 368, alpha_color(GREEN, a), width=2)
            label(d, "read", 555, 250, f_tiny, alpha_color(GREEN, a))

        # 7: Response back to client
        if ph >= 7:
            a = min(prog, 1) if ph == 7 else 1.0
            ex = int(lerp(575, 140, a))
            ey = int(lerp(230, 220, a))
            dashed_arrow(d, 575, 230, ex, ey, alpha_color(TEAL, a), width=2)
            label(d, "response ✓", 360, 215, f_tiny, alpha_color(L_TEAL, a))

        # Concepts panel
        rounded_rect(d, (550, 280, 775, 400), 8, SURFACE, BORDER, 1)
        label(d, "KEY INSIGHT", 662, 296, f_small, MUTED)
        insights = [
            (INDIGO, "Commands: mutate state"),
            (GREEN, "Queries: never mutate"),
            (PURPLE, "Separate models per side"),
            (TEAL, "Scale reads independently"),
        ]
        for ii, (ic, it) in enumerate(insights):
            d.ellipse([(560, 310 + ii * 22 - 4), (568, 310 + ii * 22 + 4)], fill=ic)
            label(d, it, 572, 310 + ii * 22, f_tiny, (180, 190, 210), anchor="lm")

        step_indicator(
            d,
            [
                "idle",
                "cmd→",
                "write",
                "emit",
                "project",
                "query→",
                "read",
                "respond",
                "done",
            ],
            ph,
            INDIGO,
            L_INDIGO,
        )
        frames.append(img)

    save_gif(frames, "10_cqrs", duration=90)


# ══════════════════════════════════════════════════════════════════════════════
# 5. IDEMPOTENT MESSAGING
# ══════════════════════════════════════════════════════════════════════════════
def make_idempotent():
    print("Generating Idempotent Messaging GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    # Phases:
    # 0=idle  1=msg1_send  2=msg1_process  3=msg1_ack  4=msg1_duplicate_arrives
    # 5=idempotency_check  6=duplicate_dropped  7=msg2_new  8=msg2_process  9=pause
    PHASES = [5, 6, 6, 5, 6, 6, 6, 6, 6, 7]
    get_phase, total = phase_fn(PHASES)

    PROD_BOX = (25, 175, 145, 245)
    BROKER_BOX = (195, 100, 355, 340)
    CHECK_BOX = (410, 140, 590, 250)
    STORE_BOX = (410, 275, 590, 370)
    CONS_BOX = (635, 155, 775, 275)
    DB_BOX = (635, 300, 775, 390)

    def msg_chip(d, x, y, msg_id, key, color, alpha=1.0, duplicate=False):
        bg = alpha_color((40, 12, 12) if duplicate else (20, 35, 20), alpha)
        bc = alpha_color(RED if duplicate else color, alpha)
        rounded_rect(d, (x, y, x + 160, y + 38), 6, bg, bc, 2)
        label(
            d,
            f"id: {msg_id}",
            x + 80,
            y + 12,
            f_tiny,
            alpha_color(L_RED if duplicate else TEXT, alpha),
        )
        label(
            d,
            f"key: {key}",
            x + 80,
            y + 26,
            ft(MONO, 8),
            alpha_color(RED if duplicate else MUTED, alpha),
        )
        if duplicate:
            label(d, "DUPLICATE", x + 130, y + 8, ft(MONO, 8), alpha_color(RED, alpha))

    frames = []
    for fi in range(total):
        ph, prog = get_phase(fi)
        img, d = new_frame()

        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(d, "IDEMPOTENT MESSAGING", W // 2, 34, f_title, L_GREEN)
        rounded_rect(d, (660, 20, 770, 48), 5, (10, 40, 20), None)
        label(d, "EXACTLY-ONCE", 715, 34, f_badge, GREEN)

        # Producer
        p_act = ph in (1, 7)
        pc = lerpC(BORDER, BLUE, pulse(fi / 4)) if p_act else BORDER
        rounded_rect(d, PROD_BOX, 10, (18, 26, 44), pc, 2)
        label(d, "PRODUCER", 85, 198, f_label, L_BLUE)
        label(d, "payment_svc", 85, 216, f_tiny, MUTED)
        label(d, "at-least-once", 85, 232, f_tiny, (60, 90, 140))

        # Broker / Queue
        rounded_rect(d, BROKER_BOX, 10, SURFACE, BLUE, 1)
        rounded_rect(d, (195, 100, 355, 124), 8, (28, 44, 80), None)
        label(d, "MESSAGE BROKER", 275, 112, f_small, L_BLUE)

        # Messages in queue
        msgs_in_queue = []
        if ph >= 1:
            msgs_in_queue.append(("msg-001", "payment#42", GREEN, False))
        if ph >= 4:
            msgs_in_queue.append(("msg-001", "payment#42", RED, True))
        if ph >= 7:
            msgs_in_queue.append(("msg-002", "payment#43", CYAN, False))

        for mi, (mid, key, mc, is_dup) in enumerate(msgs_in_queue):
            my = 135 + mi * 55
            a = (
                min(prog, 1)
                if (
                    (ph == 1 and mi == 0)
                    or (ph == 4 and mi == 1)
                    or (ph == 7 and mi == 2)
                )
                else 1.0
            )
            msg_chip(d, 202, my, mid, key, mc, a, is_dup)

        # Idempotency Check box
        ic_a = min(prog, 1) if ph == 5 else (1 if ph >= 5 else 0.0)
        rounded_rect(
            d, CHECK_BOX, 10, alpha_color(SURFACE, ic_a), alpha_color(AMBER, ic_a), 2
        )
        rounded_rect(d, (410, 140, 590, 163), 8, alpha_color((50, 40, 10), ic_a), None)
        label(d, "IDEMPOTENCY CHECK", 500, 152, f_small, alpha_color(L_AMBER, ic_a))
        label(d, "seen_ids store", 500, 178, f_tiny, alpha_color(MUTED, ic_a))

        # Show check result
        if ph == 5:
            label(d, f'lookup "msg-001"', 500, 198, f_tiny, alpha_color(L_AMBER, prog))
        elif ph == 6:
            rounded_rect(
                d,
                (420, 190, 580, 238),
                6,
                alpha_color((40, 14, 14), prog),
                alpha_color(RED, prog),
                1,
            )
            label(d, "FOUND in seen_ids", 500, 207, f_small, alpha_color(L_RED, prog))
            label(d, "→ DROP duplicate ✗", 500, 224, f_small, alpha_color(RED, prog))
        elif ph >= 7:
            rounded_rect(d, (420, 190, 580, 238), 6, (12, 30, 15), (20, 100, 40), 1)
            label(d, "msg-001: seen ✓", 500, 207, f_small, (74, 222, 128))
            label(d, "msg-002: NEW → process", 500, 224, f_small, L_GREEN)

        # Seen IDs store
        st_a = min(prog, 1) if ph == 3 else (1 if ph >= 3 else 0.0)
        rounded_rect(
            d,
            STORE_BOX,
            8,
            alpha_color((14, 24, 18), st_a),
            alpha_color(GREEN, st_a),
            2,
        )
        rounded_rect(d, (410, 275, 590, 296), 6, alpha_color((16, 40, 22), st_a), None)
        label(d, "SEEN IDs STORE", 500, 286, f_small, alpha_color(L_GREEN, st_a))
        entries = []
        if ph >= 3:
            entries.append(("msg-001", "payment#42", GREEN))
        if ph >= 8:
            entries.append(("msg-002", "payment#43", CYAN))
        for ei, (eid, ekey, ec) in enumerate(entries):
            ea = (
                min(prog, 1)
                if ((ph == 3 and ei == 0) or (ph == 8 and ei == 1))
                else 1.0
            )
            rounded_rect(
                d,
                (420, 300 + ei * 28, 580, 323 + ei * 28),
                4,
                alpha_color((16, 34, 20), ea),
                alpha_color(ec, ea * 0.5),
                1,
            )
            label(
                d,
                f"{eid}  ·  {ekey}",
                500,
                311 + ei * 28,
                f_tiny,
                alpha_color(TEXT, ea),
            )

        # Consumer
        cs_a = min(prog, 1) if ph == 2 else (1 if ph >= 2 else 0.0)
        cc = (
            lerpC(BORDER, GREEN, pulse(fi / 4))
            if ph in (2, 8)
            else (GREEN if ph > 2 else BORDER)
        )
        rounded_rect(
            d, CONS_BOX, 10, alpha_color((16, 30, 18), cs_a), alpha_color(cc, cs_a), 2
        )
        label(d, "CONSUMER", 705, 190, f_label, alpha_color(L_GREEN, cs_a))
        label(d, "payment_processor", 705, 208, f_tiny, alpha_color(MUTED, cs_a))
        if ph in (2, 8):
            label(d, "processing…", 705, 226, f_tiny, alpha_color(GREEN, min(prog, 1)))
        elif ph >= 3:
            label(d, "processed ✓", 705, 226, f_tiny, alpha_color(GREEN, cs_a))

        # DB
        db_a = min(prog, 1) if ph == 3 else (1 if ph >= 3 else 0.0)
        rounded_rect(
            d, DB_BOX, 8, alpha_color(SURFACE, db_a), alpha_color(CYAN, db_a * 0.7), 2
        )
        label(d, "PAYMENTS DB", 705, 330, f_small, alpha_color(L_CYAN, db_a))
        if ph >= 3:
            label(d, "payment#42 written ✓", 705, 350, f_tiny, alpha_color(GREEN, db_a))
        if ph >= 8:
            label(
                d,
                "payment#43 written ✓",
                705,
                367,
                f_tiny,
                alpha_color(GREEN, min(prog, 1)),
            )

        # Animated arrows
        if ph >= 1:
            a = min(prog, 1) if ph == 1 else 1.0
            ex = int(lerp(145, 195, a))
            arrow(d, 145, 210, ex, 160, alpha_color(BLUE, a), width=2)

        if ph >= 2:
            a = min(prog, 1) if ph == 2 else 1.0
            ex = int(lerp(355, 410, a))
            arrow(d, 355, 160, ex, 175, alpha_color(GREEN, a), width=2)
            label(d, "consume", 382, 155, f_tiny, alpha_color(GREEN, a))

        if ph == 3:
            a = min(prog, 1)
            arrow(
                d, 635, 200, int(lerp(635, 590, a)), 195, alpha_color(GREEN, a), width=1
            )
            arrow(
                d, 705, 275, 705, int(lerp(275, 300, a)), alpha_color(CYAN, a), width=1
            )

        if ph >= 4:
            a = min(prog, 1) if ph == 4 else 1.0
            ex = int(lerp(145, 195, a))
            arrow(d, 145, 220, ex, 195, alpha_color(RED, a), width=2)
            label(d, "duplicate!", 168, 210, f_tiny, alpha_color(RED, a))

        if ph >= 5:
            a = min(prog, 1) if ph == 5 else 1.0
            ex = int(lerp(355, 410, a))
            arrow(d, 355, 195, ex, 185, alpha_color(AMBER, a), width=2)
            label(d, "check?", 382, 180, f_tiny, alpha_color(AMBER, a))

        if ph == 6:
            a = min(prog, 1)
            # X mark over duplicate msg
            xc, yc = 282, 163
            d.line(
                [(xc - 12, yc - 8), (xc + 12, yc + 8)],
                fill=alpha_color(RED, a),
                width=3,
            )
            d.line(
                [(xc + 12, yc - 8), (xc - 12, yc + 8)],
                fill=alpha_color(RED, a),
                width=3,
            )
            label(d, "DROPPED", 282, 175, f_tiny, alpha_color(RED, a))

        if ph >= 7:
            a = min(prog, 1) if ph == 7 else 1.0
            ex = int(lerp(145, 195, a))
            arrow(d, 145, 225, ex, 215, alpha_color(CYAN, a), width=2)

        if ph >= 8:
            a = min(prog, 1) if ph == 8 else 1.0
            ex = int(lerp(355, 410, a))
            arrow(d, 355, 220, ex, 195, alpha_color(GREEN, a), width=2)

        step_indicator(
            d,
            [
                "idle",
                "send",
                "consume",
                "ack+store",
                "dup arrives",
                "check",
                "drop!",
                "new msg",
                "process",
                "done",
            ],
            ph,
            GREEN,
            L_GREEN,
        )
        frames.append(img)

    save_gif(frames, "05_idempotent", duration=88)


# ══════════════════════════════════════════════════════════════════════════════
# 2. SCHEMA REGISTRY
# ══════════════════════════════════════════════════════════════════════════════
def make_schema_registry():
    print("Generating Schema Registry GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    # Phases:
    # 0=idle  1=producer_registers_v1  2=registry_stores  3=producer_publishes_v1
    # 4=consumer_fetches_schema  5=consumer_deserializes  6=schema_evolves_v2
    # 7=backwards_compat_check  8=consumer_reads_v2_with_v1  9=pause
    PHASES = [5, 6, 6, 6, 6, 6, 7, 6, 6, 7]
    get_phase, total = phase_fn(PHASES)

    PROD_BOX = (20, 150, 155, 250)
    REG_BOX = (220, 60, 560, 390)
    BROKER = (220, 290, 560, 390)
    CONS_BOX = (615, 150, 770, 280)

    frames = []
    for fi in range(total):
        ph, prog = get_phase(fi)
        img, d = new_frame()

        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(d, "SCHEMA REGISTRY", W // 2, 34, f_title, (251, 146, 60))
        rounded_rect(d, (660, 20, 770, 48), 5, (42, 26, 10), None)
        label(d, "COMPATIBILITY", 715, 34, f_badge, AMBER)

        # Producer
        p_act = ph in (1, 3, 6)
        pc = lerpC(BORDER, BLUE, pulse(fi / 4)) if p_act else BORDER
        rounded_rect(d, PROD_BOX, 10, (18, 26, 44), pc, 2)
        label(d, "PRODUCER", 87, 178, f_label, L_BLUE)
        label(d, "order_service", 87, 196, f_tiny, MUTED)
        if ph >= 6:
            label(
                d,
                "schema v2",
                87,
                215,
                f_tiny,
                alpha_color(AMBER, min(prog, 1) if ph == 6 else 1.0),
            )
        elif ph >= 1:
            label(
                d,
                "schema v1",
                87,
                215,
                f_tiny,
                alpha_color(GREEN, min(prog, 1) if ph == 1 else 1.0),
            )

        # Schema Registry box
        rounded_rect(d, REG_BOX, 12, SURFACE, AMBER, 2)
        rounded_rect(d, (220, 60, 560, 88), 8, (50, 34, 10), None)
        label(d, "SCHEMA REGISTRY", 390, 74, f_label, L_AMBER)

        # Schema v1 entry
        v1_a = min(prog, 1) if ph == 2 else (1 if ph >= 2 else 0.0)
        rounded_rect(
            d,
            (235, 96, 548, 185),
            8,
            alpha_color((18, 26, 14), v1_a),
            alpha_color(GREEN, v1_a),
            2,
        )
        rounded_rect(d, (235, 96, 548, 116), 6, alpha_color((20, 42, 16), v1_a), None)
        label(
            d,
            "subject: order-value  /  version: 1  /  id: 42",
            391,
            106,
            f_tiny,
            alpha_color(L_GREEN, v1_a),
        )
        schema_v1 = [
            '{ "type":"record",',
            '  "name":"Order",',
            '  "fields":[',
            '    {"name":"id",    "type":"string"},',
            '    {"name":"amount","type":"double"}',
            "  ]",
            "}",
        ]
        for li, line in enumerate(schema_v1):
            label(
                d,
                line,
                245,
                126 + li * 10,
                ft(MONO, 8),
                alpha_color((150, 200, 120), v1_a),
                anchor="lm",
            )

        # Schema v2 entry (evolved)
        v2_a = min(prog, 1) if ph == 6 else (1 if ph >= 6 else 0.0)
        rounded_rect(
            d,
            (235, 192, 548, 285),
            8,
            alpha_color((26, 20, 10), v2_a),
            alpha_color(AMBER, v2_a),
            2,
        )
        rounded_rect(d, (235, 192, 548, 212), 6, alpha_color((46, 32, 8), v2_a), None)
        label(
            d,
            "subject: order-value  /  version: 2  /  id: 43",
            391,
            202,
            f_tiny,
            alpha_color(L_AMBER, v2_a),
        )
        schema_v2 = [
            '{ "type":"record",',
            '  "name":"Order",',
            '  "fields":[',
            '    {"name":"id",      "type":"string"},',
            '    {"name":"amount",  "type":"double"},',
            '    {"name":"currency","type":"string",  ← NEW FIELD',
            '     "default":"USD"}  ✓ backwards-compat',
            "}",
        ]
        for li, line in enumerate(schema_v2):
            col = AMBER if ("NEW" in line or "compat" in line) else (150, 200, 120)
            label(
                d,
                line,
                245,
                220 + li * 9,
                ft(MONO, 8),
                alpha_color(col, v2_a),
                anchor="lm",
            )

        # Compatibility check badge
        if ph == 7:
            a = min(prog, 1)
            rounded_rect(
                d,
                (245, 258, 548, 282),
                6,
                alpha_color((10, 35, 10), a),
                alpha_color(GREEN, a),
                2,
            )
            label(
                d,
                "✓ BACKWARDS_COMPATIBLE  —  safe to publish",
                396,
                270,
                f_tiny,
                alpha_color(GREEN, a),
            )
        elif ph >= 7:
            rounded_rect(d, (245, 258, 548, 282), 6, (10, 35, 10), (20, 100, 40), 2)
            label(
                d, "✓ BACKWARDS_COMPATIBLE  —  safe to publish", 396, 270, f_tiny, GREEN
            )

        # Broker
        rounded_rect(d, BROKER, 8, (14, 18, 30), BLUE, 1)
        rounded_rect(d, (220, 290, 560, 308), 6, (24, 36, 60), None)
        label(d, "TOPIC: orders", 390, 299, f_small, L_BLUE)

        # Messages in broker
        msgs = []
        if ph >= 3:
            msgs.append(("id:42  v1", GREEN))
        if ph >= 8:
            msgs.append(("id:43  v2", AMBER))
        for mi, (mt, mc) in enumerate(msgs):
            ma = (
                min(prog, 1)
                if ((ph == 3 and mi == 0) or (ph == 8 and mi == 1))
                else 1.0
            )
            rounded_rect(
                d,
                (235 + mi * 165, 312, 390 + mi * 165, 338),
                5,
                alpha_color((14, 28, 14), ma),
                alpha_color(mc, ma),
                1,
            )
            label(d, mt, 312 + mi * 165, 325, f_tiny, alpha_color(mc, ma))

        # Consumer
        c_act = ph in (4, 5, 8)
        cc = lerpC(BORDER, CYAN, pulse(fi / 4)) if c_act else BORDER
        rounded_rect(d, CONS_BOX, 10, (12, 28, 36), cc, 2)
        label(d, "CONSUMER", 692, 185, f_label, L_CYAN)
        label(d, "analytics_svc", 692, 204, f_tiny, MUTED)

        if ph == 4:
            label(
                d,
                "fetching schema…",
                692,
                224,
                f_tiny,
                alpha_color(AMBER, min(prog, 1)),
            )
        elif ph == 5:
            label(
                d,
                "deserializing v1",
                692,
                224,
                f_tiny,
                alpha_color(GREEN, min(prog, 1)),
            )
            label(d, "✓ OK", 692, 240, f_small, alpha_color(GREEN, min(prog, 1)))
        elif ph >= 5 and ph < 8:
            label(d, "reads v1 ✓", 692, 224, f_tiny, GREEN)
        elif ph == 8:
            label(d, "reads v2 ✓", 692, 224, f_tiny, alpha_color(GREEN, min(prog, 1)))
            label(
                d, "(v1 schema ok!)", 692, 240, f_tiny, alpha_color(AMBER, min(prog, 1))
            )

        # Animated arrows
        # 1: Producer → Registry (register)
        if ph >= 1:
            a = min(prog, 1) if ph == 1 else 1.0
            ex = int(lerp(155, 220, a))
            arrow(d, 155, 175, ex, 130, alpha_color(GREEN, a), width=2)
            label(d, "register v1", 185, 143, f_tiny, alpha_color(L_GREEN, a))

        # 2: Registry ack
        if ph >= 2:
            a = min(prog, 1) if ph == 2 else 1.0
            dashed_arrow(
                d, 220, 140, int(lerp(220, 155, a)), 185, alpha_color(GREEN, a), width=1
            )
            label(d, "id: 42", 185, 167, f_tiny, alpha_color(GREEN, a))

        # 3: Producer → Broker (publish with schema id embedded)
        if ph >= 3:
            a = min(prog, 1) if ph == 3 else 1.0
            ey = int(lerp(220, 310, a))
            arrow(d, 120, 250, 120, ey, alpha_color(BLUE, a), width=2)
            arrow(d, 120, ey, 220, 325, alpha_color(BLUE, a), width=2)
            label(d, "publish+schemaId:42", 175, 268, f_tiny, alpha_color(L_BLUE, a))

        # 4: Consumer fetches schema
        if ph >= 4:
            a = min(prog, 1) if ph == 4 else 1.0
            ex = int(lerp(615, 560, a))
            arrow(d, 615, 190, ex, 140, alpha_color(AMBER, a), width=2)
            label(
                d,
                "GET /schemas/42",
                590,
                163,
                f_tiny,
                alpha_color(AMBER, a),
                anchor="rm",
            )

        # 5: Consumer reads broker
        if ph >= 5:
            a = min(prog, 1) if ph == 5 else 1.0
            arrow(
                d, 615, 210, int(lerp(615, 560, a)), 325, alpha_color(CYAN, a), width=1
            )

        # 6: Producer registers v2
        if ph >= 6:
            a = min(prog, 1) if ph == 6 else 1.0
            ex = int(lerp(155, 220, a))
            arrow(d, 155, 195, ex, 230, alpha_color(AMBER, a), width=2)
            label(d, "register v2", 185, 213, f_tiny, alpha_color(L_AMBER, a))

        # 8: consumer reads v2
        if ph >= 8:
            a = min(prog, 1) if ph == 8 else 1.0
            arrow(
                d, 615, 220, int(lerp(615, 560, a)), 330, alpha_color(GREEN, a), width=1
            )

        step_indicator(
            d,
            [
                "idle",
                "reg v1",
                "ack",
                "publish",
                "fetch",
                "deser",
                "evolve v2",
                "compat?",
                "consume v2",
                "done",
            ],
            ph,
            AMBER,
            L_AMBER,
        )
        frames.append(img)

    save_gif(frames, "02_schema_registry", duration=92)


# ══════════════════════════════════════════════════════════════════════════════
# 4. RETRY STRATEGIES
# ══════════════════════════════════════════════════════════════════════════════
def make_retry_strategies():
    print("Generating Retry Strategies GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO, 10)
    f_tiny = ft(MONO, 9)
    f_badge = ft(MONO_B, 9)

    # We'll animate 3 strategies side-by-side, each with their retry timeline:
    # Immediate, Linear backoff, Exponential backoff + jitter
    # Then show final comparison chart
    # Phases: 0=idle  1=attempt1(all fail)  2=retry1  3=retry2  4=retry3  5=retry4
    #         6=exp_succeeds  7=chart  8=pause

    PHASES = [5, 7, 7, 7, 7, 7, 7, 10, 8]
    get_phase, total = phase_fn(PHASES)

    # Three strategy lanes, stacked
    STRAT = [
        {
            "name": "IMMEDIATE RETRY",
            "col": RED,
            "lc": L_RED,
            "bg": (30, 8, 8),
            "delays": [0, 0, 0, 0, 0],
            "y0": 80,
        },
        {
            "name": "LINEAR BACKOFF",
            "col": AMBER,
            "lc": L_AMBER,
            "bg": (32, 22, 6),
            "delays": [0, 2, 4, 6, 8],
            "y0": 195,
        },
        {
            "name": "EXP + JITTER",
            "col": GREEN,
            "lc": L_GREEN,
            "bg": (8, 28, 16),
            "delays": [0, 1, 3, 7, 8],
            "y0": 310,
        },
    ]
    SH = 95  # strategy lane height

    # Timeline x positions for attempts
    T_START = 110
    T_END = 680
    T_W = T_END - T_START

    def attempt_x(attempt, max_delay_sum, strategy_delays):
        # cumulative time position
        cumulative = sum(strategy_delays[:attempt]) + attempt
        total_time = sum(strategy_delays) + len(strategy_delays)
        return int(T_START + (cumulative / total_time) * T_W)

    frames = []
    for fi in range(total):
        ph, prog = get_phase(fi)
        img, d = new_frame()

        rounded_rect(d, (20, 16, 780, 52), 8, SURFACE, BORDER, 1)
        label(d, "RETRY STRATEGIES", W // 2, 34, f_title, (251, 146, 60))
        rounded_rect(d, (660, 20, 770, 48), 5, (42, 26, 10), None)
        label(d, "RESILIENCE", 715, 34, f_badge, (251, 146, 60))

        # Time axis header
        rounded_rect(d, (T_START, 62, T_END, 74), 3, BORDER, None)
        label(d, "TIME →", T_START + 10, 68, ft(MONO, 8), MUTED, anchor="lm")
        label(d, "T=0", T_START, 56, ft(MONO, 8), MUTED)
        label(d, "T=max", T_END, 56, ft(MONO, 8), MUTED)

        for si, strat in enumerate(STRAT):
            sy0 = strat["y0"]
            sy1 = sy0 + SH
            sc = strat["col"]
            slc = strat["lc"]
            sbg = strat["bg"]
            delays = strat["delays"]
            n_attempts = 5

            # Lane background
            rounded_rect(d, (20, sy0, 780, sy1), 8, sbg, sc, 1)
            label(d, strat["name"], 65, sy0 + 18, f_small, slc, anchor="lm")

            # Description
            descs = [
                "retry immediately — hammers the service",
                "wait N×base between attempts (e.g. 2s, 4s, 6s…)",
                "wait 2ⁿ + random jitter — prevents thundering herd",
            ]
            label(d, descs[si], 65, sy0 + 32, ft(MONO, 8), MUTED, anchor="lm")

            # Timeline rail
            rail_y = sy0 + 62
            d.line([(T_START, rail_y), (T_END, rail_y)], fill=BORDER, width=1)

            # Calculate positions
            cum = 0
            positions = []
            for ai in range(n_attempts):
                positions.append(cum)
                cum += delays[ai] + 1
            total_t = cum

            # Draw attempts based on phase
            n_shown = min(ph, n_attempts) if ph < 8 else n_attempts
            # Which attempt succeeds? exp+jitter succeeds at retry 3, others fail all
            SUCCESS_AT = {
                0: None,
                1: None,
                2: 3,
            }  # strategy index: attempt index (0-based)

            for ai in range(n_shown):
                ax = T_START + int((positions[ai] / max(total_t, 1)) * T_W)
                is_success = SUCCESS_AT[si] == ai
                fail = not is_success

                if ph < 8:
                    # animate current attempt arriving
                    if ai == ph - 1:
                        ax_anim = T_START + int(
                            (positions[ai] / max(total_t, 1)) * T_W * prog
                        )
                        # travelling dot
                        for tx in range(T_START, ax_anim, 8):
                            d.ellipse(
                                [(tx - 2, rail_y - 2), (tx + 2, rail_y + 2)],
                                fill=alpha_color(sc, 0.3),
                            )
                        ax = ax_anim

                # Draw attempt marker
                mk_col = GREEN if is_success else sc
                mk_bg = (8, 30, 10) if is_success else sbg
                d.ellipse(
                    [(ax - 12, rail_y - 12), (ax + 12, rail_y + 12)],
                    fill=mk_bg,
                    outline=mk_col,
                    width=2,
                )
                label(
                    d,
                    "✓" if is_success else "✗",
                    ax,
                    rail_y,
                    f_small,
                    GREEN if is_success else sc,
                )
                label(d, f"t{ai + 1}", ax, rail_y + 22, ft(MONO, 8), MUTED)

                # Draw delay gap label between attempts
                if ai < n_shown - 1 and ai < n_attempts - 1 and ph < 8:
                    next_ax = T_START + int((positions[ai + 1] / max(total_t, 1)) * T_W)
                    gap = delays[ai + 1]
                    if gap > 0 and next_ax > ax + 20:
                        mid = (ax + next_ax) // 2
                        d.line(
                            [(ax + 14, rail_y), (next_ax - 14, rail_y)],
                            fill=alpha_color(sc, 0.4),
                            width=1,
                        )
                        label(
                            d,
                            f"+{gap}s",
                            mid,
                            rail_y - 14,
                            ft(MONO, 8),
                            alpha_color(slc, 0.7),
                        )

        # Thundering herd warning for immediate
        if ph >= 3:
            a = min(prog, 1) if ph == 3 else 1.0
            rounded_rect(
                d,
                (T_END + 5, STRAT[0]["y0"] + 10, 775, STRAT[0]["y0"] + 80),
                6,
                alpha_color((40, 8, 8), a),
                alpha_color(RED, a),
                1,
            )
            label(
                d,
                "⚠ THUNDERING",
                T_END + 40,
                STRAT[0]["y0"] + 28,
                f_tiny,
                alpha_color(L_RED, a),
            )
            label(
                d,
                "HERD RISK",
                T_END + 40,
                STRAT[0]["y0"] + 43,
                f_tiny,
                alpha_color(RED, a),
            )
            label(
                d,
                "all clients retry",
                T_END + 40,
                STRAT[0]["y0"] + 58,
                ft(MONO, 8),
                alpha_color(MUTED, a),
            )
            label(
                d,
                "at same time!",
                T_END + 40,
                STRAT[0]["y0"] + 69,
                ft(MONO, 8),
                alpha_color(RED, a),
            )

        # Jitter explanation
        if ph >= 5:
            a = min(prog, 1) if ph == 5 else 1.0
            rounded_rect(
                d,
                (T_END + 5, STRAT[2]["y0"] + 10, 775, STRAT[2]["y0"] + 80),
                6,
                alpha_color((8, 30, 12), a),
                alpha_color(GREEN, a),
                1,
            )
            label(
                d,
                "✓ JITTER",
                T_END + 40,
                STRAT[2]["y0"] + 28,
                f_tiny,
                alpha_color(L_GREEN, a),
            )
            label(
                d,
                "spreads load",
                T_END + 40,
                STRAT[2]["y0"] + 43,
                f_tiny,
                alpha_color(GREEN, a),
            )
            label(
                d,
                "avoids spikes",
                T_END + 40,
                STRAT[2]["y0"] + 58,
                ft(MONO, 8),
                alpha_color(GREEN, a),
            )
            label(
                d,
                "± random offset",
                T_END + 40,
                STRAT[2]["y0"] + 69,
                ft(MONO, 8),
                alpha_color(MUTED, a),
            )

        # Comparison summary panel (phase 7)
        if ph >= 7:
            a = min(prog, 1) if ph == 7 else 1.0
            rounded_rect(
                d,
                (20, 405, 780, 455),
                8,
                alpha_color(SURFACE, a),
                alpha_color(BORDER, a),
                1,
            )
            cols_data = [
                (
                    RED,
                    "Immediate",
                    "Fastest retry",
                    "Thundering herd",
                    "✗ not recommended",
                ),
                (
                    AMBER,
                    "Linear",
                    "Predictable",
                    "Still bunches up",
                    "~ okay for low RPS",
                ),
                (
                    GREEN,
                    "Exp+Jitter",
                    "Best spread",
                    "Higher latency",
                    "✓ production default",
                ),
            ]
            for ci, (cc, cname, pro, con, verdict) in enumerate(cols_data):
                cx = 130 + ci * 200
                label(d, cname, cx, 415, f_small, alpha_color(cc, a))
                label(d, f"+ {pro}", cx, 428, ft(MONO, 8), alpha_color(MUTED, a))
                label(d, f"- {con}", cx, 438, ft(MONO, 8), alpha_color(MUTED, a))
                label(d, verdict, cx, 450, ft(MONO, 8), alpha_color(cc, a))
        else:
            step_indicator(
                d,
                [
                    "idle",
                    "t1",
                    "retry1",
                    "retry2",
                    "retry3",
                    "retry4",
                    "success",
                    "summary",
                    "done",
                ],
                ph,
                AMBER,
                L_AMBER,
            )

        frames.append(img)

    save_gif(frames, "04_retry_strategies", duration=95)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    make_event_sourcing()
    make_schema_registry()
    make_consumer_groups()
    make_retry_strategies()
    make_idempotent()
    make_outbox()
    make_dlq()
    make_saga()
    make_circuit_breaker()
    make_cqrs()
    print("\n✓ All 10 core concepts generated!")
    print("  - 10 animated GIFs for viewing/sharing")
    print("  - 10 static PNGs for slide presentations")
