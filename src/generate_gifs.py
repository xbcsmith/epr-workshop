#!/usr/bin/env python3
# 
from PIL import Image, ImageDraw, ImageFont
import math, os

OUT = "./outputs/gifs"
os.makedirs(OUT, exist_ok=True)

MONO_B = "DejaVuSansMono-Bold.ttf"
MONO   = "DejaVuSansMono.ttf"
SANS_B = "Poppins-Bold.ttf"
SANS   = "Poppins-Medium.ttf"

def ft(path, size):
    return ImageFont.truetype(path, size)

BG      = (10,  12,  16)
SURFACE = (17,  19,  24)
BORDER  = (30,  34,  48)
TEXT    = (226, 232, 240)
MUTED   = (100, 116, 139)
BLUE    = (59,  130, 246)
CYAN    = (6,   182, 212)
GREEN   = (16,  185, 129)
AMBER   = (245, 159, 11)
RED     = (239, 68,  68)
PURPLE  = (139, 92,  246)
PINK    = (236, 72,  153)
L_BLUE  = (147, 197, 253)
L_GREEN = (110, 231, 183)
L_RED   = (252, 165, 165)
L_AMBER = (253, 230, 138)
L_PURP  = (196, 181, 253)
L_CYAN  = (103, 232, 249)
TEAL    = (20,  184, 166)
L_TEAL  = (153, 246, 228)
INDIGO  = (99,  102, 241)
L_INDIGO= (165, 180, 252)

W, H = 800, 460

def new_frame():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)

def rounded_rect(d, box, r, fill, outline=None, width=2):
    x0,y0,x1,y1 = box
    d.rounded_rectangle([x0,y0,x1,y1], radius=r, fill=fill, outline=outline, width=width)

def label(d, text, cx, cy, font, color=TEXT, anchor="mm"):
    d.text((cx, cy), text, font=font, fill=color, anchor=anchor)

def arrow(d, x0, y0, x1, y1, color, width=2, head=10):
    d.line([(x0,y0),(x1,y1)], fill=color, width=width)
    dx, dy = x1-x0, y1-y0
    length = max(math.hypot(dx, dy), 1)
    ux, uy = dx/length, dy/length
    px, py = -uy, ux
    pts = [(x1,y1),
           (x1-head*ux+head*0.4*px, y1-head*uy+head*0.4*py),
           (x1-head*ux-head*0.4*px, y1-head*uy-head*0.4*py)]
    d.polygon(pts, fill=color)

def dashed_arrow(d, x0, y0, x1, y1, color, seg=10, gap=6, width=2):
    dx, dy = x1-x0, y1-y0
    length = math.hypot(dx, dy)
    if length == 0: return
    ux, uy = dx/length, dy/length
    t, on = 0, True
    while t < length:
        t2 = min(t + (seg if on else gap), length)
        if on:
            d.line([(x0+ux*t, y0+uy*t),(x0+ux*t2, y0+uy*t2)], fill=color, width=width)
        t, on = t2, not on
    arrow(d, x1-ux*3, y1-uy*3, x1, y1, color, width=width, head=9)

def pulse(t, period=1.0, lo=0.4, hi=1.0):
    v = (math.sin(2*math.pi*t/period)+1)/2
    return lo + v*(hi-lo)

def lerp(a, b, t): return a + (b-a)*t
def lerpC(c1, c2, t): return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))
def alpha_color(base, alpha): return lerpC(BG, base, max(0.0, min(alpha, 1.0)))

def ease_in_out(t): return t*t*(3-2*t)

def save_gif(frames, name, duration=85):
    path = f"{OUT}/{name}.gif"
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   loop=0, duration=duration, optimize=False)
    kb = os.path.getsize(path)//1024
    print(f"  ✓ {path}  ({len(frames)} frames, {kb}KB)")

def phase_fn(phase_lengths):
    def get(f):
        acc = 0
        for i, pl in enumerate(phase_lengths):
            acc += pl
            if f < acc:
                raw = 1 - (acc - f) / pl
                return i, ease_in_out(raw)
        return len(phase_lengths)-1, 1.0
    total = sum(phase_lengths)
    return get, total

def step_indicator(d, steps, ph, accent=BLUE, light=L_BLUE):
    f_tiny = ft(MONO, 7)
    f_step = ft(MONO, 9)
    rounded_rect(d, (20,405,780,448), 8, SURFACE, BORDER, 1)
    n = len(steps)
    spacing = 740 // n
    for si, st in enumerate(steps):
        cx = 30 + si * spacing + spacing // 2
        if si < ph:
            d.ellipse([(cx-14,415),(cx+14,435)], fill=(10,35,15), outline=GREEN)
            label(d, "✓", cx, 425, f_step, GREEN)
        elif si == ph:
            d.ellipse([(cx-14,415),(cx+14,435)], fill=(12,14,22), outline=accent, width=2)
            label(d, str(si), cx, 425, f_step, light)
        else:
            d.ellipse([(cx-14,415),(cx+14,435)], fill=SURFACE, outline=BORDER, width=1)
            label(d, str(si), cx, 425, f_step, MUTED)
        col = GREEN if si < ph else (light if si == ph else MUTED)
        label(d, st[:9], cx, 442, f_tiny, col)


# ══════════════════════════════════════════════════════════════════════════════
# 07. CQRS
# ══════════════════════════════════════════════════════════════════════════════
def make_cqrs():
    print("Generating CQRS GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO,   10)
    f_tiny  = ft(MONO,    9)
    f_badge = ft(MONO_B,  9)

    # Phases:
    # 0=idle  1=client_sends_cmd  2=cmd_handler_writes  3=event_emitted
    # 4=projections_update  5=client_sends_query  6=query_reads  7=response  8=pause
    PHASES = [5, 6, 6, 6, 7, 6, 6, 6, 7]
    get_phase, total = phase_fn(PHASES)

    # Layout
    CLIENT_BOX  = (20,  175, 140, 245)
    CMD_BOX     = (185, 80,  345, 155)
    WRITE_DB    = (185, 195, 345, 285)
    EVENT_BUS   = (185, 305, 345, 370)
    PROJ_BOXES  = [(390, 80,  530, 145),
                   (390, 165, 530, 230),
                   (390, 250, 530, 315)]
    READ_DB     = (390, 340, 530, 395)
    QUERY_BOX   = (575, 80,  745, 155)
    RESP_BOX    = (575, 195, 745, 265)

    frames = []
    for fi in range(total):
        ph, prog = get_phase(fi)
        img, d = new_frame()

        # Title
        rounded_rect(d, (20,16,780,52), 8, SURFACE, BORDER, 1)
        label(d, "CQRS  —  Command Query Responsibility Segregation", W//2, 34, f_title, L_INDIGO)
        rounded_rect(d, (670,20,770,48), 5, (20,20,50), None)
        label(d, "SEPARATION", 720, 34, f_badge, INDIGO)

        # ── Write side label ──
        rounded_rect(d, (175,60,360,400), 10, (12,12,20), (40,40,80), 1)
        label(d, "WRITE SIDE", 267, 75, f_tiny, (80,80,160))

        # ── Read side label ──
        rounded_rect(d, (380,60,545,400), 10, (10,20,15), (30,70,50), 1)
        label(d, "READ SIDE", 462, 75, f_tiny, (50,130,80))

        # ── Client ──
        c_act = ph in (1,5)
        cc = lerpC(BORDER, INDIGO, pulse(fi/4)) if c_act else BORDER
        rounded_rect(d, CLIENT_BOX, 10, (18,18,40), cc, 2)
        label(d, "CLIENT", 80, 200, f_label, L_INDIGO)
        label(d, "app / API", 80, 218, f_tiny, MUTED)
        if ph < 5:
            label(d, "→ COMMAND", 80, 234, f_tiny, alpha_color(L_INDIGO, min(prog,1) if ph==1 else (1 if ph>1 else 0.0)))
        else:
            label(d, "→ QUERY", 80, 234, f_tiny, alpha_color(L_GREEN, min(prog,1) if ph==5 else (1 if ph>5 else 0.0)))

        # ── Command Handler ──
        ch_a = min(prog,1) if ph==2 else (1 if ph>2 else 0.0)
        rounded_rect(d, CMD_BOX, 8, alpha_color((20,18,48),ch_a), alpha_color(INDIGO,ch_a), 2)
        label(d, "COMMAND HANDLER", 265, 105, f_small, alpha_color(L_INDIGO, ch_a))
        label(d, "validate + execute", 265, 122, f_tiny, alpha_color(MUTED, ch_a))
        label(d, "PlaceOrderCmd", 265, 138, f_tiny, alpha_color((109,40,217), ch_a))

        # ── Write DB ──
        wd_a = min(prog,1) if ph==2 else (1 if ph>2 else 0.0)
        rounded_rect(d, WRITE_DB, 8, alpha_color(SURFACE, wd_a), alpha_color(INDIGO, wd_a*0.7), 2)
        rounded_rect(d, (185,195,345,218), 6, alpha_color((30,26,60),wd_a), None)
        label(d, "WRITE DB", 265, 207, f_small, alpha_color(L_INDIGO, wd_a))
        label(d, "orders (normalized)", 265, 228, f_tiny, alpha_color(MUTED, wd_a))
        label(d, "strong consistency", 265, 244, f_tiny, alpha_color((80,70,140), wd_a))
        label(d, "optimized for writes", 265, 260, f_tiny, alpha_color((60,55,110), wd_a))

        # ── Event Bus ──
        eb_a = min(prog,1) if ph==3 else (1 if ph>3 else 0.0)
        rounded_rect(d, EVENT_BUS, 8, alpha_color((20,14,34),eb_a), alpha_color(PURPLE,eb_a), 2)
        label(d, "EVENT BUS", 265, 328, f_small, alpha_color(L_PURP, eb_a))
        label(d, "OrderPlaced event", 265, 348, f_tiny, alpha_color(PURPLE, eb_a))

        # ── Projections ──
        PROJ_NAMES  = ["OrderListView", "DashboardProj", "SearchIndex"]
        PROJ_COLORS = [CYAN, GREEN, TEAL]
        PROJ_L      = [L_CYAN, L_GREEN, L_TEAL]
        for pi, (pbox, pname, pc, plc) in enumerate(zip(PROJ_BOXES, PROJ_NAMES, PROJ_COLORS, PROJ_L)):
            pa = min(prog,1) if ph==4 else (1 if ph>4 else 0.0)
            delay = pi * 0.25
            pa = max(0, min((pa - delay) / 0.6, 1.0)) if ph==4 else pa
            rounded_rect(d, pbox, 6, alpha_color((10,22,18),pa), alpha_color(pc,pa), 1)
            label(d, pname, (pbox[0]+pbox[2])//2, (pbox[1]+pbox[3])//2 - 8, f_tiny, alpha_color(plc,pa))
            label(d, "projection", (pbox[0]+pbox[2])//2, (pbox[1]+pbox[3])//2 + 8, ft(MONO,8), alpha_color(pc,pa))

        # ── Read DB ──
        rd_a = min(prog,1) if ph==4 else (1 if ph>4 else 0.0)
        rounded_rect(d, READ_DB, 8, alpha_color(SURFACE,rd_a), alpha_color(GREEN,rd_a*0.8), 2)
        rounded_rect(d, (390,340,530,360), 6, alpha_color((12,30,18),rd_a), None)
        label(d, "READ DB", 460, 352, f_small, alpha_color(L_GREEN, rd_a))
        label(d, "denormalized views", 460, 372, f_tiny, alpha_color(MUTED, rd_a))

        # ── Query Handler ──
        qh_a = min(prog,1) if ph==6 else (1 if ph>6 else 0.0)
        rounded_rect(d, QUERY_BOX, 8, alpha_color((12,26,18),qh_a), alpha_color(GREEN,qh_a), 2)
        label(d, "QUERY HANDLER", 660, 105, f_small, alpha_color(L_GREEN, qh_a))
        label(d, "read-only", 660, 122, f_tiny, alpha_color(MUTED, qh_a))
        label(d, "GetOrdersQuery", 660, 138, f_tiny, alpha_color(GREEN, qh_a))

        # ── Response ──
        rsp_a = min(prog,1) if ph==7 else (1 if ph>7 else 0.0)
        rounded_rect(d, RESP_BOX, 8, alpha_color((12,26,18),rsp_a), alpha_color(TEAL,rsp_a), 2)
        label(d, "RESPONSE", 660, 218, f_small, alpha_color(L_TEAL, rsp_a))
        label(d, "[{id:42, status:..}]", 660, 238, f_tiny, alpha_color(L_GREEN, rsp_a))

        # ── Animated arrows ──
        # 1: Client → Command Handler
        if ph >= 1:
            a = min(prog,1) if ph==1 else 1.0
            ex = int(lerp(140, 185, a))
            arrow(d, 140, 195, ex, 117, alpha_color(INDIGO,a), width=2)
            label(d, "Command", 160, 148, f_tiny, alpha_color(L_INDIGO,a))

        # 2: CMD → Write DB
        if ph >= 2:
            a = min(prog,1) if ph==2 else 1.0
            ey = int(lerp(155, 195, a))
            arrow(d, 265, 155, 265, ey, alpha_color(INDIGO,a), width=2)

        # 3: Write DB → Event Bus
        if ph >= 3:
            a = min(prog,1) if ph==3 else 1.0
            ey = int(lerp(285, 305, a))
            arrow(d, 265, 285, 265, ey, alpha_color(PURPLE,a), width=2)
            label(d, "emit", 278, 295, f_tiny, alpha_color(L_PURP,a))

        # 4: Event Bus → Projections (fan out)
        if ph >= 4:
            a = min(prog,1) if ph==4 else 1.0
            for pi, pbox in enumerate(PROJ_BOXES):
                delay = pi * 0.25
                pa = max(0, min((a - delay) / 0.6, 1.0))
                py = (pbox[1]+pbox[3])//2
                ex = int(lerp(345, pbox[0], pa))
                arrow(d, 345, 337, ex, py, alpha_color(PROJ_COLORS[pi], pa), width=2)

        # Projection → Read DB
        if ph >= 4:
            a = min(prog,1) if ph==4 else 1.0
            arrow(d, 460, 315, 460, 340, alpha_color(GREEN,a), width=1)

        # 5: Client → Query Handler
        if ph >= 5:
            a = min(prog,1) if ph==5 else 1.0
            ex = int(lerp(140, 575, a))
            ey = int(lerp(205, 117, a))
            arrow(d, 140, 205, ex, ey, alpha_color(GREEN,a), width=2)
            label(d, "Query", 360, 148, f_tiny, alpha_color(L_GREEN,a))

        # 6: Query Handler → Read DB
        if ph >= 6:
            a = min(prog,1) if ph==6 else 1.0
            ex = int(lerp(575, 530, a))
            arrow(d, 575, 130, ex, 368, alpha_color(GREEN,a), width=2)
            label(d, "read", 555, 250, f_tiny, alpha_color(GREEN,a))

        # 7: Response back to client
        if ph >= 7:
            a = min(prog,1) if ph==7 else 1.0
            ex = int(lerp(575, 140, a))
            ey = int(lerp(230, 220, a))
            dashed_arrow(d, 575, 230, ex, ey, alpha_color(TEAL,a), width=2)
            label(d, "response ✓", 360, 215, f_tiny, alpha_color(L_TEAL,a))

        # Concepts panel
        rounded_rect(d, (550, 280, 775, 400), 8, SURFACE, BORDER, 1)
        label(d, "KEY INSIGHT", 662, 296, f_small, MUTED)
        insights = [
            (INDIGO,"Commands: mutate state"),
            (GREEN, "Queries: never mutate"),
            (PURPLE,"Separate models per side"),
            (TEAL,  "Scale reads independently"),
        ]
        for ii, (ic, it) in enumerate(insights):
            d.ellipse([(560,310+ii*22-4),(568,310+ii*22+4)], fill=ic)
            label(d, it, 572, 310+ii*22, f_tiny, (180,190,210), anchor="lm")

        step_indicator(d,
            ["idle","cmd→","write","emit","project","query→","read","respond","done"],
            ph, INDIGO, L_INDIGO)
        frames.append(img)

    save_gif(frames, "07_cqrs", duration=90)


# ══════════════════════════════════════════════════════════════════════════════
# 08. IDEMPOTENT MESSAGING
# ══════════════════════════════════════════════════════════════════════════════
def make_idempotent():
    print("Generating Idempotent Messaging GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO,   10)
    f_tiny  = ft(MONO,    9)
    f_badge = ft(MONO_B,  9)

    # Phases:
    # 0=idle  1=msg1_send  2=msg1_process  3=msg1_ack  4=msg1_duplicate_arrives
    # 5=idempotency_check  6=duplicate_dropped  7=msg2_new  8=msg2_process  9=pause
    PHASES = [5, 6, 6, 5, 6, 6, 6, 6, 6, 7]
    get_phase, total = phase_fn(PHASES)

    PROD_BOX    = (25,  175, 145, 245)
    BROKER_BOX  = (195, 100, 355, 340)
    CHECK_BOX   = (410, 140, 590, 250)
    STORE_BOX   = (410, 275, 590, 370)
    CONS_BOX    = (635, 155, 775, 275)
    DB_BOX      = (635, 300, 775, 390)

    def msg_chip(d, x, y, msg_id, key, color, alpha=1.0, duplicate=False):
        bg = alpha_color((40,12,12) if duplicate else (20,35,20), alpha)
        bc = alpha_color(RED if duplicate else color, alpha)
        rounded_rect(d, (x,y,x+160,y+38), 6, bg, bc, 2)
        label(d, f"id: {msg_id}", x+80, y+12, f_tiny, alpha_color(L_RED if duplicate else TEXT, alpha))
        label(d, f"key: {key}", x+80, y+26, ft(MONO,8), alpha_color(RED if duplicate else MUTED, alpha))
        if duplicate:
            label(d, "DUPLICATE", x+130, y+8, ft(MONO,8), alpha_color(RED, alpha))

    frames = []
    for fi in range(total):
        ph, prog = get_phase(fi)
        img, d = new_frame()

        rounded_rect(d, (20,16,780,52), 8, SURFACE, BORDER, 1)
        label(d, "IDEMPOTENT MESSAGING", W//2, 34, f_title, L_GREEN)
        rounded_rect(d, (660,20,770,48), 5, (10,40,20), None)
        label(d, "EXACTLY-ONCE", 715, 34, f_badge, GREEN)

        # Producer
        p_act = ph in (1,7)
        pc = lerpC(BORDER, BLUE, pulse(fi/4)) if p_act else BORDER
        rounded_rect(d, PROD_BOX, 10, (18,26,44), pc, 2)
        label(d, "PRODUCER", 85, 198, f_label, L_BLUE)
        label(d, "payment_svc", 85, 216, f_tiny, MUTED)
        label(d, "at-least-once", 85, 232, f_tiny, (60,90,140))

        # Broker / Queue
        rounded_rect(d, BROKER_BOX, 10, SURFACE, BLUE, 1)
        rounded_rect(d, (195,100,355,124), 8, (28,44,80), None)
        label(d, "MESSAGE BROKER", 275, 112, f_small, L_BLUE)

        # Messages in queue
        msgs_in_queue = []
        if ph >= 1: msgs_in_queue.append(("msg-001","payment#42", GREEN, False))
        if ph >= 4: msgs_in_queue.append(("msg-001","payment#42", RED, True))
        if ph >= 7: msgs_in_queue.append(("msg-002","payment#43", CYAN, False))

        for mi, (mid, key, mc, is_dup) in enumerate(msgs_in_queue):
            my = 135 + mi*55
            a = min(prog,1) if ((ph==1 and mi==0) or (ph==4 and mi==1) or (ph==7 and mi==2)) else 1.0
            msg_chip(d, 202, my, mid, key, mc, a, is_dup)

        # Idempotency Check box
        ic_a = min(prog,1) if ph==5 else (1 if ph>=5 else 0.0)
        rounded_rect(d, CHECK_BOX, 10, alpha_color(SURFACE,ic_a), alpha_color(AMBER,ic_a), 2)
        rounded_rect(d, (410,140,590,163), 8, alpha_color((50,40,10),ic_a), None)
        label(d, "IDEMPOTENCY CHECK", 500, 152, f_small, alpha_color(L_AMBER,ic_a))
        label(d, "seen_ids store", 500, 178, f_tiny, alpha_color(MUTED,ic_a))

        # Show check result
        if ph == 5:
            label(d, f'lookup "msg-001"', 500, 198, f_tiny, alpha_color(L_AMBER, prog))
        elif ph == 6:
            rounded_rect(d, (420,190,580,238), 6, alpha_color((40,14,14),prog), alpha_color(RED,prog), 1)
            label(d, "FOUND in seen_ids", 500, 207, f_small, alpha_color(L_RED, prog))
            label(d, "→ DROP duplicate ✗", 500, 224, f_small, alpha_color(RED, prog))
        elif ph >= 7:
            rounded_rect(d, (420,190,580,238), 6, (12,30,15), (20,100,40), 1)
            label(d, "msg-001: seen ✓", 500, 207, f_small, (74,222,128))
            label(d, "msg-002: NEW → process", 500, 224, f_small, L_GREEN)

        # Seen IDs store
        st_a = min(prog,1) if ph==3 else (1 if ph>=3 else 0.0)
        rounded_rect(d, STORE_BOX, 8, alpha_color((14,24,18),st_a), alpha_color(GREEN,st_a), 2)
        rounded_rect(d, (410,275,590,296), 6, alpha_color((16,40,22),st_a), None)
        label(d, "SEEN IDs STORE", 500, 286, f_small, alpha_color(L_GREEN,st_a))
        entries = []
        if ph >= 3: entries.append(("msg-001", "payment#42", GREEN))
        if ph >= 8: entries.append(("msg-002", "payment#43", CYAN))
        for ei, (eid, ekey, ec) in enumerate(entries):
            ea = min(prog,1) if ((ph==3 and ei==0) or (ph==8 and ei==1)) else 1.0
            rounded_rect(d, (420, 300+ei*28, 580, 323+ei*28), 4,
                         alpha_color((16,34,20),ea), alpha_color(ec,ea*0.5), 1)
            label(d, f"{eid}  ·  {ekey}", 500, 311+ei*28, f_tiny, alpha_color(TEXT,ea))

        # Consumer
        cs_a = min(prog,1) if ph==2 else (1 if ph>=2 else 0.0)
        cc = lerpC(BORDER, GREEN, pulse(fi/4)) if ph in (2,8) else (GREEN if ph>2 else BORDER)
        rounded_rect(d, CONS_BOX, 10, alpha_color((16,30,18),cs_a), alpha_color(cc,cs_a), 2)
        label(d, "CONSUMER", 705, 190, f_label, alpha_color(L_GREEN,cs_a))
        label(d, "payment_processor", 705, 208, f_tiny, alpha_color(MUTED,cs_a))
        if ph in (2,8):
            label(d, "processing…", 705, 226, f_tiny, alpha_color(GREEN,min(prog,1)))
        elif ph >= 3:
            label(d, "processed ✓", 705, 226, f_tiny, alpha_color(GREEN,cs_a))

        # DB
        db_a = min(prog,1) if ph==3 else (1 if ph>=3 else 0.0)
        rounded_rect(d, DB_BOX, 8, alpha_color(SURFACE,db_a), alpha_color(CYAN,db_a*0.7), 2)
        label(d, "PAYMENTS DB", 705, 330, f_small, alpha_color(L_CYAN,db_a))
        if ph >= 3:
            label(d, "payment#42 written ✓", 705, 350, f_tiny, alpha_color(GREEN,db_a))
        if ph >= 8:
            label(d, "payment#43 written ✓", 705, 367, f_tiny, alpha_color(GREEN,min(prog,1)))

        # Animated arrows
        if ph >= 1:
            a = min(prog,1) if ph==1 else 1.0
            ex = int(lerp(145,195,a))
            arrow(d, 145, 210, ex, 160, alpha_color(BLUE,a), width=2)

        if ph >= 2:
            a = min(prog,1) if ph==2 else 1.0
            ex = int(lerp(355,410,a))
            arrow(d, 355, 160, ex, 175, alpha_color(GREEN,a), width=2)
            label(d, "consume", 382, 155, f_tiny, alpha_color(GREEN,a))

        if ph == 3:
            a = min(prog,1)
            arrow(d, 635, 200, int(lerp(635,590,a)), 195, alpha_color(GREEN,a), width=1)
            arrow(d, 705, 275, 705, int(lerp(275,300,a)), alpha_color(CYAN,a), width=1)

        if ph >= 4:
            a = min(prog,1) if ph==4 else 1.0
            ex = int(lerp(145,195,a))
            arrow(d, 145, 220, ex, 195, alpha_color(RED,a), width=2)
            label(d, "duplicate!", 168, 210, f_tiny, alpha_color(RED,a))

        if ph >= 5:
            a = min(prog,1) if ph==5 else 1.0
            ex = int(lerp(355,410,a))
            arrow(d, 355, 195, ex, 185, alpha_color(AMBER,a), width=2)
            label(d, "check?", 382, 180, f_tiny, alpha_color(AMBER,a))

        if ph == 6:
            a = min(prog,1)
            # X mark over duplicate msg
            xc, yc = 282, 163
            d.line([(xc-12,yc-8),(xc+12,yc+8)], fill=alpha_color(RED,a), width=3)
            d.line([(xc+12,yc-8),(xc-12,yc+8)], fill=alpha_color(RED,a), width=3)
            label(d, "DROPPED", 282, 175, f_tiny, alpha_color(RED,a))

        if ph >= 7:
            a = min(prog,1) if ph==7 else 1.0
            ex = int(lerp(145,195,a))
            arrow(d, 145, 225, ex, 215, alpha_color(CYAN,a), width=2)

        if ph >= 8:
            a = min(prog,1) if ph==8 else 1.0
            ex = int(lerp(355,410,a))
            arrow(d, 355, 220, ex, 195, alpha_color(GREEN,a), width=2)

        step_indicator(d,
            ["idle","send","consume","ack+store","dup arrives","check","drop!","new msg","process","done"],
            ph, GREEN, L_GREEN)
        frames.append(img)

    save_gif(frames, "08_idempotent", duration=88)


# ══════════════════════════════════════════════════════════════════════════════
# 09. SCHEMA REGISTRY
# ══════════════════════════════════════════════════════════════════════════════
def make_schema_registry():
    print("Generating Schema Registry GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO,   10)
    f_tiny  = ft(MONO,    9)
    f_badge = ft(MONO_B,  9)

    # Phases:
    # 0=idle  1=producer_registers_v1  2=registry_stores  3=producer_publishes_v1
    # 4=consumer_fetches_schema  5=consumer_deserializes  6=schema_evolves_v2
    # 7=backwards_compat_check  8=consumer_reads_v2_with_v1  9=pause
    PHASES = [5, 6, 6, 6, 6, 6, 7, 6, 6, 7]
    get_phase, total = phase_fn(PHASES)

    PROD_BOX  = (20,  150, 155, 250)
    REG_BOX   = (220, 60,  560, 390)
    BROKER    = (220, 290, 560, 390)
    CONS_BOX  = (615, 150, 770, 280)

    frames = []
    for fi in range(total):
        ph, prog = get_phase(fi)
        img, d = new_frame()

        rounded_rect(d, (20,16,780,52), 8, SURFACE, BORDER, 1)
        label(d, "SCHEMA REGISTRY", W//2, 34, f_title, (251,146,60))
        rounded_rect(d, (660,20,770,48), 5, (42,26,10), None)
        label(d, "COMPATIBILITY", 715, 34, f_badge, AMBER)

        # Producer
        p_act = ph in (1,3,6)
        pc = lerpC(BORDER, BLUE, pulse(fi/4)) if p_act else BORDER
        rounded_rect(d, PROD_BOX, 10, (18,26,44), pc, 2)
        label(d, "PRODUCER", 87, 178, f_label, L_BLUE)
        label(d, "order_service", 87, 196, f_tiny, MUTED)
        if ph >= 6:
            label(d, "schema v2", 87, 215, f_tiny, alpha_color(AMBER,min(prog,1) if ph==6 else 1.0))
        elif ph >= 1:
            label(d, "schema v1", 87, 215, f_tiny, alpha_color(GREEN,min(prog,1) if ph==1 else 1.0))

        # Schema Registry box
        rounded_rect(d, REG_BOX, 12, SURFACE, AMBER, 2)
        rounded_rect(d, (220,60,560,88), 8, (50,34,10), None)
        label(d, "SCHEMA REGISTRY", 390, 74, f_label, L_AMBER)

        # Schema v1 entry
        v1_a = min(prog,1) if ph==2 else (1 if ph>=2 else 0.0)
        rounded_rect(d, (235,96,548,185), 8, alpha_color((18,26,14),v1_a), alpha_color(GREEN,v1_a), 2)
        rounded_rect(d, (235,96,548,116), 6, alpha_color((20,42,16),v1_a), None)
        label(d, "subject: order-value  /  version: 1  /  id: 42", 391, 106, f_tiny, alpha_color(L_GREEN,v1_a))
        schema_v1 = [
            '{ "type":"record",',
            '  "name":"Order",',
            '  "fields":[',
            '    {"name":"id",    "type":"string"},',
            '    {"name":"amount","type":"double"}',
            '  ]',
            '}',
        ]
        for li, line in enumerate(schema_v1):
            label(d, line, 245, 126+li*10, ft(MONO,8), alpha_color((150,200,120),v1_a), anchor="lm")

        # Schema v2 entry (evolved)
        v2_a = min(prog,1) if ph==6 else (1 if ph>=6 else 0.0)
        rounded_rect(d, (235,192,548,285), 8, alpha_color((26,20,10),v2_a), alpha_color(AMBER,v2_a), 2)
        rounded_rect(d, (235,192,548,212), 6, alpha_color((46,32,8),v2_a), None)
        label(d, "subject: order-value  /  version: 2  /  id: 43", 391, 202, f_tiny, alpha_color(L_AMBER,v2_a))
        schema_v2 = [
            '{ "type":"record",',
            '  "name":"Order",',
            '  "fields":[',
            '    {"name":"id",      "type":"string"},',
            '    {"name":"amount",  "type":"double"},',
            '    {"name":"currency","type":"string",  ← NEW FIELD',
            '     "default":"USD"}  ✓ backwards-compat',
            '}',
        ]
        for li, line in enumerate(schema_v2):
            col = AMBER if ("NEW" in line or "compat" in line) else (150,200,120)
            label(d, line, 245, 220+li*9, ft(MONO,8), alpha_color(col,v2_a), anchor="lm")

        # Compatibility check badge
        if ph == 7:
            a = min(prog,1)
            rounded_rect(d, (245,258,548,282), 6, alpha_color((10,35,10),a), alpha_color(GREEN,a), 2)
            label(d, "✓ BACKWARDS_COMPATIBLE  —  safe to publish", 396, 270, f_tiny, alpha_color(GREEN,a))
        elif ph >= 7:
            rounded_rect(d, (245,258,548,282), 6, (10,35,10), (20,100,40), 2)
            label(d, "✓ BACKWARDS_COMPATIBLE  —  safe to publish", 396, 270, f_tiny, GREEN)

        # Broker
        rounded_rect(d, BROKER, 8, (14,18,30), BLUE, 1)
        rounded_rect(d, (220,290,560,308), 6, (24,36,60), None)
        label(d, "TOPIC: orders", 390, 299, f_small, L_BLUE)

        # Messages in broker
        msgs = []
        if ph >= 3: msgs.append(("id:42  v1", GREEN))
        if ph >= 8: msgs.append(("id:43  v2", AMBER))
        for mi, (mt, mc) in enumerate(msgs):
            ma = min(prog,1) if ((ph==3 and mi==0) or (ph==8 and mi==1)) else 1.0
            rounded_rect(d, (235+mi*165, 312, 390+mi*165, 338), 5,
                         alpha_color((14,28,14),ma), alpha_color(mc,ma), 1)
            label(d, mt, 312+mi*165, 325, f_tiny, alpha_color(mc,ma))

        # Consumer
        c_act = ph in (4,5,8)
        cc = lerpC(BORDER, CYAN, pulse(fi/4)) if c_act else BORDER
        rounded_rect(d, CONS_BOX, 10, (12,28,36), cc, 2)
        label(d, "CONSUMER", 692, 185, f_label, L_CYAN)
        label(d, "analytics_svc", 692, 204, f_tiny, MUTED)

        if ph == 4:
            label(d, "fetching schema…", 692, 224, f_tiny, alpha_color(AMBER,min(prog,1)))
        elif ph == 5:
            label(d, "deserializing v1", 692, 224, f_tiny, alpha_color(GREEN,min(prog,1)))
            label(d, "✓ OK", 692, 240, f_small, alpha_color(GREEN,min(prog,1)))
        elif ph >= 5 and ph < 8:
            label(d, "reads v1 ✓", 692, 224, f_tiny, GREEN)
        elif ph == 8:
            label(d, "reads v2 ✓", 692, 224, f_tiny, alpha_color(GREEN,min(prog,1)))
            label(d, "(v1 schema ok!)", 692, 240, f_tiny, alpha_color(AMBER,min(prog,1)))

        # Animated arrows
        # 1: Producer → Registry (register)
        if ph >= 1:
            a = min(prog,1) if ph==1 else 1.0
            ex = int(lerp(155,220,a))
            arrow(d, 155, 175, ex, 130, alpha_color(GREEN,a), width=2)
            label(d, "register v1", 185, 143, f_tiny, alpha_color(L_GREEN,a))

        # 2: Registry ack
        if ph >= 2:
            a = min(prog,1) if ph==2 else 1.0
            dashed_arrow(d, 220, 140, int(lerp(220,155,a)), 185, alpha_color(GREEN,a), width=1)
            label(d, "id: 42", 185, 167, f_tiny, alpha_color(GREEN,a))

        # 3: Producer → Broker (publish with schema id embedded)
        if ph >= 3:
            a = min(prog,1) if ph==3 else 1.0
            ey = int(lerp(220,310,a))
            arrow(d, 120, 250, 120, ey, alpha_color(BLUE,a), width=2)
            arrow(d, 120, ey, 220, 325, alpha_color(BLUE,a), width=2)
            label(d, "publish+schemaId:42", 175, 268, f_tiny, alpha_color(L_BLUE,a))

        # 4: Consumer fetches schema
        if ph >= 4:
            a = min(prog,1) if ph==4 else 1.0
            ex = int(lerp(615,560,a))
            arrow(d, 615, 190, ex, 140, alpha_color(AMBER,a), width=2)
            label(d, "GET /schemas/42", 590, 163, f_tiny, alpha_color(AMBER,a), anchor="rm")

        # 5: Consumer reads broker
        if ph >= 5:
            a = min(prog,1) if ph==5 else 1.0
            arrow(d, 615, 210, int(lerp(615,560,a)), 325, alpha_color(CYAN,a), width=1)

        # 6: Producer registers v2
        if ph >= 6:
            a = min(prog,1) if ph==6 else 1.0
            ex = int(lerp(155,220,a))
            arrow(d, 155, 195, ex, 230, alpha_color(AMBER,a), width=2)
            label(d, "register v2", 185, 213, f_tiny, alpha_color(L_AMBER,a))

        # 8: consumer reads v2
        if ph >= 8:
            a = min(prog,1) if ph==8 else 1.0
            arrow(d, 615, 220, int(lerp(615,560,a)), 330, alpha_color(GREEN,a), width=1)

        step_indicator(d,
            ["idle","reg v1","ack","publish","fetch","deser","evolve v2","compat?","consume v2","done"],
            ph, AMBER, L_AMBER)
        frames.append(img)

    save_gif(frames, "09_schema_registry", duration=92)


# ══════════════════════════════════════════════════════════════════════════════
# 10. RETRY STRATEGIES
# ══════════════════════════════════════════════════════════════════════════════
def make_retry_strategies():
    print("Generating Retry Strategies GIF…")
    f_title = ft(SANS_B, 15)
    f_label = ft(MONO_B, 12)
    f_small = ft(MONO,   10)
    f_tiny  = ft(MONO,    9)
    f_badge = ft(MONO_B,  9)

    # We'll animate 3 strategies side-by-side, each with their retry timeline:
    # Immediate, Linear backoff, Exponential backoff + jitter
    # Then show final comparison chart
    # Phases: 0=idle  1=attempt1(all fail)  2=retry1  3=retry2  4=retry3  5=retry4
    #         6=exp_succeeds  7=chart  8=pause

    PHASES = [5, 7, 7, 7, 7, 7, 7, 10, 8]
    get_phase, total = phase_fn(PHASES)

    # Three strategy lanes, stacked
    STRAT = [
        {"name":"IMMEDIATE RETRY", "col":RED,    "lc":L_RED,    "bg":(30,8,8),
         "delays":[0,0,0,0,0], "y0":80},
        {"name":"LINEAR BACKOFF",  "col":AMBER,  "lc":L_AMBER,  "bg":(32,22,6),
         "delays":[0,2,4,6,8], "y0":195},
        {"name":"EXP + JITTER",    "col":GREEN,  "lc":L_GREEN,  "bg":(8,28,16),
         "delays":[0,1,3,7,8], "y0":310},
    ]
    SH = 95   # strategy lane height

    # Timeline x positions for attempts
    T_START = 110
    T_END   = 680
    T_W     = T_END - T_START

    def attempt_x(attempt, max_delay_sum, strategy_delays):
        # cumulative time position
        cumulative = sum(strategy_delays[:attempt]) + attempt
        total_time = sum(strategy_delays) + len(strategy_delays)
        return int(T_START + (cumulative / total_time) * T_W)

    frames = []
    for fi in range(total):
        ph, prog = get_phase(fi)
        img, d = new_frame()

        rounded_rect(d, (20,16,780,52), 8, SURFACE, BORDER, 1)
        label(d, "RETRY STRATEGIES", W//2, 34, f_title, (251,146,60))
        rounded_rect(d, (660,20,770,48), 5, (42,26,10), None)
        label(d, "RESILIENCE", 715, f_badge, AMBER)

        # Time axis header
        rounded_rect(d, (T_START, 62, T_END, 74), 3, BORDER, None)
        label(d, "TIME →", T_START+10, 68, ft(MONO,8), MUTED, anchor="lm")
        label(d, "T=0", T_START, 56, ft(MONO,8), MUTED)
        label(d, "T=max", T_END, 56, ft(MONO,8), MUTED)

        for si, strat in enumerate(STRAT):
            sy0 = strat["y0"]
            sy1 = sy0 + SH
            sc  = strat["col"]
            slc = strat["lc"]
            sbg = strat["bg"]
            delays = strat["delays"]
            n_attempts = 5

            # Lane background
            rounded_rect(d, (20, sy0, 780, sy1), 8, sbg, sc, 1)
            label(d, strat["name"], 65, sy0+18, f_small, slc, anchor="lm")

            # Description
            descs = [
                "retry immediately — hammers the service",
                "wait N×base between attempts (e.g. 2s, 4s, 6s…)",
                "wait 2ⁿ + random jitter — prevents thundering herd",
            ]
            label(d, descs[si], 65, sy0+32, ft(MONO,8), MUTED, anchor="lm")

            # Timeline rail
            rail_y = sy0 + 62
            d.line([(T_START, rail_y),(T_END, rail_y)], fill=BORDER, width=1)

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
            SUCCESS_AT = {0: None, 1: None, 2: 3}  # strategy index: attempt index (0-based)

            for ai in range(n_shown):
                ax = T_START + int((positions[ai] / max(total_t,1)) * T_W)
                is_success = (SUCCESS_AT[si] == ai)
                fail = not is_success

                if ph < 8:
                    # animate current attempt arriving
                    if ai == ph - 1:
                        ax_anim = T_START + int((positions[ai] / max(total_t,1)) * T_W * prog)
                        # travelling dot
                        for tx in range(T_START, ax_anim, 8):
                            d.ellipse([(tx-2,rail_y-2),(tx+2,rail_y+2)],
                                      fill=alpha_color(sc, 0.3))
                        ax = ax_anim

                # Draw attempt marker
                mk_col = GREEN if is_success else sc
                mk_bg  = (8,30,10) if is_success else sbg
                d.ellipse([(ax-12,rail_y-12),(ax+12,rail_y+12)],
                          fill=mk_bg, outline=mk_col, width=2)
                label(d, "✓" if is_success else "✗",
                      ax, rail_y, f_small, GREEN if is_success else sc)
                label(d, f"t{ai+1}", ax, rail_y+22, ft(MONO,8), MUTED)

                # Draw delay gap label between attempts
                if ai < n_shown-1 and ai < n_attempts-1 and ph < 8:
                    next_ax = T_START + int((positions[ai+1] / max(total_t,1)) * T_W)
                    gap = delays[ai+1]
                    if gap > 0 and next_ax > ax+20:
                        mid = (ax + next_ax)//2
                        d.line([(ax+14,rail_y),(next_ax-14,rail_y)],
                               fill=alpha_color(sc,0.4), width=1)
                        label(d, f"+{gap}s", mid, rail_y-14, ft(MONO,8), alpha_color(slc,0.7))

        # Thundering herd warning for immediate
        if ph >= 3:
            a = min(prog,1) if ph==3 else 1.0
            rounded_rect(d, (T_END+5, STRAT[0]["y0"]+10, 775, STRAT[0]["y0"]+80), 6,
                         alpha_color((40,8,8),a), alpha_color(RED,a), 1)
            label(d, "⚠ THUNDERING", T_END+40, STRAT[0]["y0"]+28, f_tiny, alpha_color(L_RED,a))
            label(d, "HERD RISK", T_END+40, STRAT[0]["y0"]+43, f_tiny, alpha_color(RED,a))
            label(d, "all clients retry", T_END+40, STRAT[0]["y0"]+58, ft(MONO,8), alpha_color(MUTED,a))
            label(d, "at same time!", T_END+40, STRAT[0]["y0"]+69, ft(MONO,8), alpha_color(RED,a))

        # Jitter explanation
        if ph >= 5:
            a = min(prog,1) if ph==5 else 1.0
            rounded_rect(d, (T_END+5, STRAT[2]["y0"]+10, 775, STRAT[2]["y0"]+80), 6,
                         alpha_color((8,30,12),a), alpha_color(GREEN,a), 1)
            label(d, "✓ JITTER", T_END+40, STRAT[2]["y0"]+28, f_tiny, alpha_color(L_GREEN,a))
            label(d, "spreads load", T_END+40, STRAT[2]["y0"]+43, f_tiny, alpha_color(GREEN,a))
            label(d, "avoids spikes", T_END+40, STRAT[2]["y0"]+58, ft(MONO,8), alpha_color(GREEN,a))
            label(d, "± random offset", T_END+40, STRAT[2]["y0"]+69, ft(MONO,8), alpha_color(MUTED,a))

        # Comparison summary panel (phase 7)
        if ph >= 7:
            a = min(prog,1) if ph==7 else 1.0
            rounded_rect(d, (20,405,780,455), 8, alpha_color(SURFACE,a), alpha_color(BORDER,a), 1)
            cols_data = [
                (RED,   "Immediate",   "Fastest retry", "Thundering herd", "✗ not recommended"),
                (AMBER, "Linear",      "Predictable",   "Still bunches up", "~ okay for low RPS"),
                (GREEN, "Exp+Jitter",  "Best spread",   "Higher latency",   "✓ production default"),
            ]
            for ci, (cc, cname, pro, con, verdict) in enumerate(cols_data):
                cx = 130 + ci*200
                label(d, cname, cx, 415, f_small, alpha_color(cc,a))
                label(d, f"+ {pro}", cx, 428, ft(MONO,8), alpha_color(MUTED,a))
                label(d, f"- {con}", cx, 438, ft(MONO,8), alpha_color(MUTED,a))
                label(d, verdict, cx, 450, ft(MONO,8), alpha_color(cc,a))
        else:
            step_indicator(d,
                ["idle","t1","retry1","retry2","retry3","retry4","success","summary","done"],
                ph, AMBER, L_AMBER)

        frames.append(img)

    save_gif(frames, "10_retry_strategies", duration=95)


if __name__ == "__main__":
    make_cqrs()
    make_idempotent()
    make_schema_registry()
    make_retry_strategies()
    print("\nAll done!")
