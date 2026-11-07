"""Builds pitch/Hydra_Pay_Pitch_Deck.pptx (16:9, dark theme matching the app).

Run:  python pitch/build_deck.py
Needs: pip install python-pptx
Edit the text in this file and re-run to regenerate the deck. Speaker notes are under each slide.
"""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSETS = HERE / "assets"
OUT = HERE / "Hydra_Pay_Pitch_Deck.pptx"

SITE = "hydra-pay.vercel.app"
FOOTER = "Hydra Pay  ·  Team HYDRA-PAY  ·  Technical University of Kenya"

# ---------- palette (same as the app's "hydra" dark theme) ----------
BG = RGBColor(0x0A, 0x0F, 0x1F)
CARD = RGBColor(0x13, 0x1A, 0x2E)
CARD2 = RGBColor(0x1A, 0x23, 0x3B)
LINE = RGBColor(0x2A, 0x34, 0x52)
TEXT = RGBColor(0xEC, 0xF0, 0xF8)
MUTED = RGBColor(0x9A, 0xA4, 0xBC)
BLUE = RGBColor(0x5B, 0x8C, 0xFF)
VIOLET = RGBColor(0x8B, 0x5C, 0xF6)
GREEN = RGBColor(0x34, 0xD3, 0x99)
RED = RGBColor(0xF8, 0x71, 0x71)
AMBER = RGBColor(0xFB, 0xBF, 0x24)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Segoe UI"
FONT_BOLD = "Segoe UI Semibold"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W, H = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]
slide_no = 0


# ---------- helpers ----------

def box(slide, x, y, w, h, fill=CARD, line=LINE, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    s.shadow.inherit = False
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    return s


def gradient(shape, a=BLUE, b=VIOLET, angle=0):
    shape.fill.gradient()
    shape.fill.gradient_angle = angle
    stops = shape.fill.gradient_stops
    stops[0].color.rgb = a
    stops[0].position = 0
    stops[1].color.rgb = b
    stops[1].position = 1.0


def text(slide, x, y, w, h, content, size=16, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=1.1, font=None):
    """content: str, or list of paragraphs; each paragraph is a str or a list of (text, {opts}) runs."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = content if isinstance(content, list) else [content]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        runs = para if isinstance(para, list) else [(para, {})]
        for t, o in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.size = Pt(o.get("size", size))
            f.bold = False
            f.name = font or (FONT_BOLD if o.get("bold", bold) else FONT)
            f.color.rgb = o.get("color", color)
        if isinstance(para, list) and para and "space_after" in para[0][1]:
            p.space_after = Pt(para[0][1]["space_after"])
    return tb


def bullets(slide, x, y, w, h, items, size=15, color=TEXT, mark="•", mark_color=BLUE, gap=8):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.line_spacing = 1.1
        r = p.add_run()
        r.text = f"{mark}  "
        r.font.size = Pt(size)
        r.font.color.rgb = mark_color
        r.font.name = FONT_BOLD
        parts = item if isinstance(item, tuple) else (None, item)
        if parts[0]:
            r = p.add_run()
            r.text = parts[0] + " "
            r.font.size = Pt(size)
            r.font.color.rgb = TEXT
            r.font.name = FONT_BOLD
        r = p.add_run()
        r.text = parts[1]
        r.font.size = Pt(size)
        r.font.color.rgb = color if not parts[0] else MUTED
        r.font.name = FONT
    return tb


def pill(slide, x, y, label, color=BLUE, w=None, size=11):
    w = w or Inches(0.16 + 0.085 * len(label))
    s = box(slide, x, y, w, Inches(0.32), fill=CARD2, line=color, radius=0.5)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size = Pt(size)
    r.font.name = FONT_BOLD
    r.font.color.rgb = color
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return s


def image(slide, path, x, y, w=None, h=None, border=True):
    pic = slide.shapes.add_picture(str(path), x, y, w, h)
    if border:
        pic.line.color.rgb = LINE
        pic.line.width = Pt(1)
    return pic


def new_slide(eyebrow=None, title=None, notes=""):
    global slide_no
    slide_no += 1
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = BG
    # soft brand glows in the corners
    for (gx, gy, c) in ((-2.2, -2.4, BLUE), (11.2, 5.2, VIOLET)):
        g = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(gx), Inches(gy), Inches(4.4), Inches(4.4))
        g.line.fill.background()
        g.shadow.inherit = False
        g.fill.solid()
        g.fill.fore_color.rgb = c
        _alpha(g, 9)
    if eyebrow:
        text(s, Inches(0.7), Inches(0.5), Inches(10), Inches(0.3), eyebrow.upper(), 12, BLUE, bold=True)
    if title:
        text(s, Inches(0.7), Inches(0.8), Inches(11.9), Inches(0.9), title, 32, TEXT, bold=True)
    if slide_no > 1:
        text(s, Inches(0.7), Inches(7.0), Inches(9), Inches(0.3), FOOTER, 10, MUTED)
        text(s, Inches(11.6), Inches(7.0), Inches(1.0), Inches(0.3), str(slide_no), 10, MUTED, align=PP_ALIGN.RIGHT)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def _alpha(shape, pct):
    """Set fill transparency (python-pptx has no API for it)."""
    from pptx.oxml.ns import qn
    sf = shape.fill._xPr.find(qn("a:solidFill"))
    clr = sf[0]
    a = clr.makeelement(qn("a:alpha"), {"val": str(int(pct * 1000))})
    clr.append(a)


def card(slide, x, y, w, h, title, body, accent=BLUE, num=None, title_size=17, body_size=13):
    box(slide, x, y, w, h)
    bar = box(slide, x, y, w, Inches(0.06), fill=accent, line=None, radius=0, shape=MSO_SHAPE.RECTANGLE)
    pad = Inches(0.28)
    top = y + Inches(0.3)
    if num is not None:
        c = box(slide, x + pad, top, Inches(0.5), Inches(0.5), fill=accent, line=None, radius=0.5)
        gradient(c, accent, VIOLET if accent == BLUE else accent)
        tf = c.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = str(num)
        r.font.size = Pt(16)
        r.font.name = FONT_BOLD
        r.font.color.rgb = WHITE
        top += Inches(0.7)
    text(slide, x + pad, top, w - 2 * pad, Inches(0.5), title, title_size, TEXT, bold=True)
    text(slide, x + pad, top + Inches(0.48), w - 2 * pad, h - (top - y) - Inches(0.6), body, body_size, MUTED, spacing=1.15)
    return bar


def stat(slide, x, y, w, value, label, color=BLUE, size=54):
    text(slide, x, y, w, Inches(1.0), value, size, color, bold=True, align=PP_ALIGN.CENTER)
    text(slide, x, y + Inches(1.05), w, Inches(0.6), label, 14, MUTED, align=PP_ALIGN.CENTER)


def table(slide, x, y, col_w, rows, header_fill=CARD2, row_h=Inches(0.46), first_bold=True, size=13, colors=None):
    """rows[0] is the header. colors: optional {(r,c): RGBColor} for cell text."""
    colors = colors or {}
    cols = len(rows[0])
    shape = slide.shapes.add_table(len(rows), cols, x, y, sum(col_w, Emu(0)), row_h * len(rows))
    tbl = shape.table
    # plain style, we colour cells ourselves
    tblPr = tbl._tbl.tblPr
    tblPr.set("bandRow", "0")
    tblPr.set("firstRow", "0")
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = cw
    for r, row in enumerate(rows):
        tbl.rows[r].height = row_h
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_fill if r == 0 else (CARD if r % 2 else BG)
            cell.margin_left = cell.margin_right = Inches(0.14)
            cell.margin_top = cell.margin_bottom = Inches(0.05)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 or isinstance(val, str) and len(val) > 3 else PP_ALIGN.CENTER
            run = p.add_run()
            run.text = val
            run.font.size = Pt(size)
            bold = r == 0 or (c == 0 and first_bold)
            run.font.name = FONT_BOLD if bold else FONT
            run.font.color.rgb = colors.get((r, c), BLUE if r == 0 else TEXT if c == 0 else MUTED)
    return shape


# =====================================================================
# 1. Title
# =====================================================================
s = new_slide(notes=(
    "Good morning. We are Team HYDRA-PAY from the Technical University of Kenya. "
    "Hydra Pay lets a customer tap a card and pay with M-Pesa in seconds. The business gets paid, "
    "the payment is confirmed by Safaricom, and every sale is recorded automatically."
))
pill(s, Inches(0.8), Inches(1.25), "●  Works with M-Pesa", GREEN, w=Inches(2.1))
text(s, Inches(0.8), Inches(1.85), Inches(7.5), Inches(1.4), [[("Tap. Pay. ", {}), ("Done.", {"color": BLUE})]], 66, TEXT, bold=True)
text(s, Inches(0.8), Inches(3.2), Inches(7.6), Inches(1.3),
     "Hydra Pay is a low-cost tap-to-pay system for busy small businesses. Customers tap a card and pay with M-Pesa. "
     "Every payment is confirmed by Safaricom and recorded automatically.", 18, MUTED, spacing=1.25)
for i, (t, c) in enumerate((("Faster queues", BLUE), ("Verified payments", GREEN), ("Clear records", VIOLET))):
    pill(s, Inches(0.8 + i * 2.05), Inches(4.85), t, c, w=Inches(1.9), size=12)
text(s, Inches(0.8), Inches(5.6), Inches(7), Inches(0.9), [
    [("Team HYDRA-PAY", {"bold": True, "color": TEXT})],
    [("Technical University of Kenya", {})],
    [(f"Live:  {SITE}", {"color": BLUE})],
], 15, MUTED, spacing=1.3)
image(s, ASSETS / "mobile.png", Inches(9.0), Inches(0.55), h=Inches(6.4))

# =====================================================================
# 2. Problem
# =====================================================================
s = new_slide("The problem", "Busy small businesses lose time and money at the till", notes=(
    "Picture a canteen at lunch hour or a matatu at the stage. Cash means counting and change. M-Pesa means typing "
    "a till number, then arguing over fake SMSs and screenshots. And at the end of the day the owner has a notebook, "
    "a till and a phone inbox that don't add up."
))
cw = Inches(3.8)
for i, (t, b, c) in enumerate((
    ("Cash slows everything", "Counting money and finding change at every sale builds queues. Cash leaves no record and is a target for theft.", AMBER),
    ("Mobile money disputes", "Fake confirmation SMSs, screenshots, reversals and \"I've sent it\" arguments. Checking each payment holds up the queue.", RED),
    ("Records don't add up", "Sales sit in a notebook, the till and a phone inbox. At the end of the day owners can't tell what they earned.", VIOLET),
)):
    card(s, Inches(0.7) + i * (cw + Inches(0.25)), Inches(2.0), cw, Inches(2.9), t, b, c, num=i + 1, body_size=14)
q = box(s, Inches(0.7), Inches(5.3), Inches(11.9), Inches(1.1), fill=CARD2, line=BLUE)
text(s, Inches(1.0), Inches(5.3), Inches(11.3), Inches(1.1),
     [[("Owners need an affordable way to ", {}), ("accept, verify and record", {"color": BLUE, "bold": True}), (" payments without slowing down.", {})]],
     20, TEXT, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)

# =====================================================================
# 3. Market
# =====================================================================
s = new_slide("Market evidence", "Cash and M-Pesa live side by side", notes=(
    "Nearly every small business in Kenya still handles cash, but most already accept digital payments. "
    "So the opportunity isn't to replace M-Pesa. It's to make M-Pesa faster at the counter and to record every "
    "sale automatically, using the habits people already have."
))
sw = Inches(3.8)
for i, (v, l, c) in enumerate((
    ("99%", "of surveyed small businesses run\npartly or wholly in cash", AMBER),
    ("86%", "accepted digital payments\nby June 2023", GREEN),
    ("Both", "mobile money is everywhere, but cash\nis still how many get paid", BLUE),
)):
    x = Inches(0.7) + i * (sw + Inches(0.25))
    box(s, x, Inches(2.0), sw, Inches(2.6))
    stat(s, x, Inches(2.45), sw, v, l, c)
text(s, Inches(0.7), Inches(4.85), Inches(11.9), Inches(0.4),
     "Sources: FinAccess MSE Tracker Survey 2023; World Bank analysis of Kenya's mobile money market.", 11, MUTED)
q = box(s, Inches(0.7), Inches(5.4), Inches(11.9), Inches(1.0), fill=CARD2, line=LINE)
text(s, Inches(1.0), Inches(5.4), Inches(11.3), Inches(1.0),
     [[("Hydra Pay works with the M-Pesa habits people already have. ", {}),
       ("The opportunity is making every transaction faster and easier to track.", {"color": BLUE, "bold": True})]],
     17, TEXT, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)

# =====================================================================
# 4. Solution
# =====================================================================
s = new_slide("Our solution", "One tap: pay, verify and record in one flow", notes=(
    "Here is the whole flow. The customer taps a card, key tag or wristband. The price is sent to their phone as an "
    "M-Pesa prompt. They enter their PIN, and Hydra Pay marks the sale paid only when Safaricom confirms it. "
    "The sale is saved with its M-Pesa code, and the customer gets a receipt on WhatsApp or SMS. "
    "Businesses choose pay-per-tap, or a prepaid card for regulars, which needs no PIN at all."
))
sw = Inches(2.82)
for i, (t, b) in enumerate((
    ("Tap", "The customer taps a card, key tag or wristband on the reader."),
    ("M-Pesa prompt", "The price pops up on the customer's phone, paid to the business till."),
    ("Verify", "They enter their PIN. Paid only when Safaricom confirms."),
    ("Record", "Saved with amount, time and M-Pesa code. Receipt by WhatsApp or SMS."),
)):
    card(s, Inches(0.7) + i * (sw + Inches(0.21)), Inches(1.95), sw, Inches(2.75), t, b, BLUE, num=i + 1, body_size=13)
for i, (t, b, c) in enumerate((
    ("Pay each time", "Every tap sends one M-Pesa prompt for the price. Nothing to set up for customers.", BLUE),
    ("Prepaid card", "Regulars top up once with M-Pesa or cash. Each tap deducts instantly, with no PIN needed.", GREEN),
)):
    x = Inches(0.7) + i * Inches(6.03)
    box(s, x, Inches(5.0), Inches(5.87), Inches(1.5), fill=CARD2, line=c)
    text(s, x + Inches(0.3), Inches(5.2), Inches(5.3), Inches(0.4), t, 17, c, bold=True)
    text(s, x + Inches(0.3), Inches(5.65), Inches(5.3), Inches(0.8), b, 14, MUTED)

# =====================================================================
# 5. Product
# =====================================================================
s = new_slide("The product", "A live dashboard for the owner, a website for customers", notes=(
    "This is the real product, not a mock-up. The owner's dashboard shows money collected today, paid and unpaid taps, "
    "who is inside, and a live feed of every tap and payment. It works on a phone, a tablet or a big screen. "
    "Customers and partners can see how it works and try a demo on our public website."
))
image(s, ASSETS / "dashboard_crop.png", Inches(0.7), Inches(1.85), w=Inches(7.7))
bullets(s, Inches(8.65), Inches(1.95), Inches(4.0), Inches(4.8), [
    ("Live totals:", "money collected, paid and unpaid taps, who is inside."),
    ("Live feed:", "every tap and payment the moment it happens."),
    ("Card management:", "register, top up, block or move a lost card."),
    ("Works on any screen:", "phone, tablet or desktop, light or dark, six colour themes."),
    ("Exports:", "daily records to Excel (CSV)."),
    ("Public website:", f"{SITE} with a try-it-yourself demo."),
], size=14, gap=10)

# =====================================================================
# 6. Technology
# =====================================================================
s = new_slide("How it's built", "Simple, low-cost hardware with verified money behind it", notes=(
    "The reader is an ESP32 with an RC522 RFID module, which are cheap, off-the-shelf parts. It sends each card ID "
    "to our Python server, which runs the payment logic and the dashboard. Payments go through Safaricom's Daraja API, "
    "receipts through WhatsApp and SMS, and a USSD menu works on any phone. The key engineering choice: a payment is "
    "only marked paid on Safaricom's answer, and it is recorded exactly once."
))
y0 = Inches(1.95)
nodes = (
    ("Card reader", "ESP32 + RC522\nlow-cost parts", BLUE),
    ("Hydra Pay server", "Python · tap logic,\npayments, dashboard", VIOLET),
    ("Safaricom M-Pesa", "Daraja STK push\n+ status check", GREEN),
)
nw = Inches(3.3)
for i, (t, b, c) in enumerate(nodes):
    x = Inches(0.7) + i * (nw + Inches(0.6))
    box(s, x, y0, nw, Inches(1.35), fill=CARD2, line=c)
    text(s, x, y0 + Inches(0.2), nw, Inches(0.4), t, 16, c, bold=True, align=PP_ALIGN.CENTER)
    text(s, x, y0 + Inches(0.62), nw, Inches(0.7), b, 12, MUTED, align=PP_ALIGN.CENTER)
    if i < 2:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + nw + Inches(0.12), y0 + Inches(0.5), Inches(0.36), Inches(0.34))
        a.fill.solid(); a.fill.fore_color.rgb = MUTED; a.line.fill.background(); a.shadow.inherit = False
mini = (("WhatsApp", "receipts, bot,\nAI in 3 languages"), ("SMS", "receipts and alerts\nvia ThriveVAS"),
        ("USSD", "menu for any phone,\nno smartphone needed"), ("Records", "cards, taps and payments,\nnothing deleted"))
mw = Inches(2.82)
for i, (t, b) in enumerate(mini):
    x = Inches(0.7) + i * (mw + Inches(0.21))
    box(s, x, Inches(3.55), mw, Inches(1.0))
    text(s, x + Inches(0.2), Inches(3.65), mw - Inches(0.4), Inches(0.35), t, 14, TEXT, bold=True)
    text(s, x + Inches(0.2), Inches(3.98), mw - Inches(0.4), Inches(0.55), b, 11, MUTED)
bullets(s, Inches(0.7), Inches(4.85), Inches(11.9), Inches(2.0), [
    ("Verified money:", "paid only on Safaricom's answer, recorded exactly once, even if the confirmation arrives twice."),
    ("Reliable reads:", "the reader filters double taps and retries half-read cards; it reconnects by itself if unplugged."),
    ("Auditable:", "an undo is a new reversal entry, so the full history is always kept."),
    ("Protected:", "every change, including sending a payment prompt, needs the owner's admin PIN."),
], size=13, gap=5)

# =====================================================================
# 7. Traction
# =====================================================================
s = new_slide("Proof of work", "It works today, and you can try it", notes=(
    "We tested the full payment flow on Safaricom's Daraja sandbox: 27 prompts sent, 10 confirmed as paid, and 15 that "
    "were declined or not answered, all correctly marked as not paid. None was wrongly counted as paid. "
    "On the right is what works today."
))
sw = Inches(1.95)
for i, (v, l, c) in enumerate((("27", "M-Pesa prompts\nsent", BLUE), ("10", "confirmed paid\nby Safaricom", GREEN), ("15", "declined or unanswered,\ncorrectly NOT paid", AMBER))):
    x = Inches(0.7) + i * (sw + Inches(0.15))
    box(s, x, Inches(1.95), sw, Inches(2.4))
    stat(s, x, Inches(2.2), sw, v, l, c, size=48)
text(s, Inches(0.7), Inches(4.5), Inches(6.2), Inches(0.35), "Daraja sandbox test runs, 22–23 October 2026.", 11, MUTED)
box(s, Inches(0.7), Inches(5.0), Inches(6.15), Inches(1.5), fill=CARD2, line=GREEN)
text(s, Inches(1.0), Inches(5.15), Inches(5.6), Inches(0.4), "Live demo at our table", 16, GREEN, bold=True)
text(s, Inches(1.0), Inches(5.6), Inches(5.6), Inches(0.85),
     "Tap a card: watch the M-Pesa prompt arrive, the dashboard update and the receipt land.", 13, MUTED)
box(s, Inches(7.15), Inches(1.95), Inches(5.45), Inches(4.55))
text(s, Inches(7.45), Inches(2.15), Inches(5), Inches(0.4), "Working today", 16, TEXT, bold=True)
bullets(s, Inches(7.45), Inches(2.65), Inches(5.0), Inches(3.8), [
    "Card and key-tag taps logged as IN / OUT",
    "M-Pesa prompt to the customer's phone for the price",
    "Receipts with the M-Pesa code on WhatsApp and SMS",
    "Prepaid wallet with M-Pesa or cash top-ups",
    "WhatsApp bot and AI help in English, Kiswahili and Sheng",
    "Live dashboard on phone and desktop, with CSV export",
    "Lost card: move the account to a new card in one click",
    "USSD menu for phones without internet",
    f"Public website and demo: {SITE}",
], size=13, mark="✓", mark_color=GREEN, gap=4)

# =====================================================================
# 8. Target market
# =====================================================================
s = new_slide("Target market", "Businesses where every second counts", notes=(
    "We start with canteens and market traders, where we can watch the queue and measure the difference. "
    "Then we move to matatus, where fares are small, frequent and time-critical. Our customer is the business owner; "
    "the users are the person paying and the person receiving."
))
cw = Inches(3.8)
for i, (tag, tc, t, b, need) in enumerate((
    ("PILOT FIRST", GREEN, "Canteens & cafés", "Lunch-hour rush, fixed prices, regular customers.", "shorter checkout and accurate sales records."),
    ("PILOT FIRST", GREEN, "Shops & market stalls", "Mixed cash and M-Pesa every day.", "easy payment tracking without expensive software."),
    ("NEXT", BLUE, "Matatus & transport", "Many small fares under time pressure. Tap IN to board.", "fast fare collection and clear daily takings."),
)):
    x = Inches(0.7) + i * (cw + Inches(0.25))
    box(s, x, Inches(1.95), cw, Inches(3.4))
    pill(s, x + Inches(0.28), Inches(2.2), tag, tc, w=Inches(1.35))
    text(s, x + Inches(0.28), Inches(2.75), cw - Inches(0.56), Inches(0.45), t, 19, TEXT, bold=True)
    text(s, x + Inches(0.28), Inches(3.3), cw - Inches(0.56), Inches(0.9), b, 14, MUTED)
    text(s, x + Inches(0.28), Inches(4.25), cw - Inches(0.56), Inches(0.9), [[("Need: ", {"bold": True, "color": TEXT}), (need, {})]], 14, MUTED)
text(s, Inches(0.7), Inches(5.7), Inches(11.9), Inches(0.8),
     [[("Customer: ", {"bold": True, "color": TEXT}), ("the business owner or operator.   ", {}),
       ("Users: ", {"bold": True, "color": TEXT}), ("the person paying and the person receiving. We start where we can observe and measure, then move to matatus.", {})]],
     14, MUTED)

# =====================================================================
# 9. Competition
# =====================================================================
s = new_slide("Why Hydra Pay", "Better than cash, a till number or a notebook", notes=(
    "Compared with what businesses use today: cash has no record and needs change. A till number means typing and "
    "fake SMSs. A notebook is manual. A card machine is expensive and takes a cut of every sale. Hydra Pay is the only "
    "option that is fast, verified, automatic and takes no cut. Standard M-Pesa charges still apply."
))
Y, N, P = "✓", "✗", "~"
rows = [
    ["", "Hydra Pay", "Cash", "Till number", "Notebook", "Card machine"],
    ["No change, nothing to type", Y, N, P, N, P],
    ["Payment checked with Safaricom", Y, N, P, N, Y],
    ["Every sale saved automatically", Y, N, P, N, Y],
    ["Daily totals ready", Y, N, P, P, P],
    ["Receipt for the customer", Y, N, Y, N, Y],
    ["Works without a smartphone", Y, Y, Y, Y, P],
    ["No cut taken from each sale", Y, Y, P, Y, N],
]
colors = {}
for r in range(1, len(rows)):
    for c in range(1, 6):
        v = rows[r][c]
        colors[(r, c)] = GREEN if v == Y else RED if v == N else AMBER
colors[(0, 1)] = WHITE
t = table(s, Inches(0.7), Inches(1.9), [Inches(4.15)] + [Inches(1.55)] * 5, rows, row_h=Inches(0.55), size=14, colors=colors)
tbl = t.table
for r in range(len(rows)):
    for c in range(1, 6):
        tbl.cell(r, c).text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    hp = tbl.cell(r, 1)
    hp.fill.solid()
    hp.fill.fore_color.rgb = RGBColor(0x1E, 0x2B, 0x55)
text(s, Inches(0.7), Inches(6.45), Inches(11.9), Inches(0.35), "✓ yes    ~ partly    ✗ no    ·    Standard M-Pesa charges still apply.", 12, MUTED)

# =====================================================================
# 10. Business model
# =====================================================================
s = new_slide("Business model", "Affordable for the seller, sustainable for us", notes=(
    "We don't take a cut of each sale, because our customers sell many low-value items and every shilling of margin "
    "matters. Instead: a free basic tier, a small subscription per reader, packages for SACCOs and larger vendors, and "
    "partnerships with associations that bring many businesses at once. We will test willingness to pay in the pilot "
    "before fixing prices."
))
cw = Inches(2.82)
for i, (t, b, c) in enumerate((
    ("Freemium", "Basic transaction recording free; advanced reports and features paid.", BLUE),
    ("Subscription", "An affordable weekly or monthly fee per reader.", VIOLET),
    ("Business packages", "Fleet and multi-stall dashboards for SACCOs and larger vendors.", GREEN),
    ("Partnerships", "Matatu SACCOs, market managers, canteen operators and business associations.", AMBER),
)):
    card(s, Inches(0.7) + i * (cw + Inches(0.21)), Inches(1.95), cw, Inches(2.9), t, b, c, num=i + 1, body_size=13)
box(s, Inches(0.7), Inches(5.2), Inches(11.9), Inches(1.2), fill=CARD2, line=GREEN)
text(s, Inches(1.0), Inches(5.2), Inches(11.3), Inches(1.2),
     [[("No cut of each sale: ", {"bold": True, "color": GREEN}),
       ("low-value, high-volume sellers keep their margin. We'll test willingness to pay in the pilot before fixing prices.", {})]],
     17, TEXT, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)

# =====================================================================
# 11. Risks
# =====================================================================
s = new_slide("Feasibility & security", "Risks we've designed for", notes=(
    "The biggest risk in mobile payments is trust, so we designed for it. Payment status comes only from Safaricom. "
    "Every record keeps its M-Pesa code. Pending is never confused with paid. And every change, including sending a "
    "payment request, needs the owner's PIN."
))
rows = [
    ["Challenge", "How Hydra Pay handles it"],
    ["Fake confirmations", "Status comes only from Safaricom's Daraja API. An unconfirmed payment is never shown as paid."],
    ["Reversals & disputes", "Every payment keeps its M-Pesa code, status and time in a history that is never deleted."],
    ["Slow checkout", "Tap, then PIN. No typing. Checkout time will be measured in the pilot."],
    ["Poor network", "Pending is kept separate from paid and never marked failed too early. Offline tap queue is next."],
    ["Tight budgets", "Off-the-shelf ESP32 + RC522, no POS terminal, no per-sale fee."],
    ["Misuse & data", "Admin PIN for every change; keys kept out of code; minimal data, aligned with Kenya's Data Protection Act."],
]
table(s, Inches(0.7), Inches(1.9), [Inches(3.0), Inches(8.9)], rows, row_h=Inches(0.6), size=14)

# =====================================================================
# 12. Roadmap
# =====================================================================
s = new_slide("Roadmap & validation", "From working prototype to real businesses", notes=(
    "The prototype is done and online. Next we interview 10 to 20 vendors and conductors, move to a live Safaricom "
    "till and USSD short code, and run a controlled pilot in a few canteens and shops, measured against a before baseline. "
    "Then matatu SACCOs."
))
steps = (
    ("DONE", GREEN, "Prototype", "Reader, M-Pesa, verification, records, WhatsApp, SMS and USSD. Dashboard and website online."),
    ("NEXT", BLUE, "Discovery", "10–20 interviews with vendors and conductors about payments, disputes and records."),
    ("NEXT", BLUE, "Go live", "Live Safaricom till, live USSD short code, offline reader that syncs later."),
    ("PILOT", VIOLET, "Controlled pilot", "A few canteens and traders, measured against a before baseline."),
    ("LATER", AMBER, "Expand", "Matatu SACCOs, then more payment options. The owner always gets KES."),
)
cw = Inches(2.24)
line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.17), Inches(11.4), Inches(0.04))
line.fill.solid(); line.fill.fore_color.rgb = LINE; line.line.fill.background()
for i, (tag, c, t, b) in enumerate(steps):
    x = Inches(0.7) + i * (cw + Inches(0.18))
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.2), Inches(2.04), Inches(0.3), Inches(0.3))
    dot.fill.solid(); dot.fill.fore_color.rgb = c; dot.line.fill.background(); dot.shadow.inherit = False
    box(s, x, Inches(2.55), cw, Inches(2.6))
    pill(s, x + Inches(0.2), Inches(2.75), tag, c, w=Inches(0.95))
    text(s, x + Inches(0.2), Inches(3.25), cw - Inches(0.4), Inches(0.4), t, 16, TEXT, bold=True)
    text(s, x + Inches(0.2), Inches(3.7), cw - Inches(0.4), Inches(1.4), b, 12, MUTED, spacing=1.15)
box(s, Inches(0.7), Inches(5.45), Inches(11.9), Inches(1.1), fill=CARD2, line=LINE)
text(s, Inches(1.0), Inches(5.45), Inches(11.3), Inches(1.1),
     [[("We'll measure: ", {"bold": True, "color": TEXT}),
       ("transaction time · queue time at peak · % recorded correctly · verification success · reconciliation errors · "
        "merchant satisfaction and willingness to pay. Targets are set after the baseline.", {})]],
     14, MUTED, anchor=MSO_ANCHOR.MIDDLE)

# =====================================================================
# 13. Industry engagement
# =====================================================================
photos = [ROOT / "WhatsApp Image 2026-10-23 at 14.01.09.jpeg", ROOT / "WhatsApp Image 2026-10-23 at 14.01.08.jpeg"]
if all(p.exists() for p in photos):
    s = new_slide("Industry engagement", "Meeting Safaricom leadership", notes=(
        "We presented Hydra Pay to Safaricom leadership, including the former Chief Financial Services Officer and the "
        "Chief Technology & Information Officer."
    ))
    captions = ("With Safaricom's former Chief Financial Services Officer", "With Safaricom's Chief Technology & Information Officer")
    ph = Inches(4.2)
    sizes = []
    for p in photos:
        with Image.open(p) as im:
            sizes.append(int(ph * im.width / im.height))
    gap = Inches(0.4)
    x = int((W - sum(sizes) - gap) / 2)
    for p, cap, pw in zip(photos, captions, sizes):
        image(s, p, x, Inches(1.9), w=pw, h=ph)
        text(s, x, Inches(1.9) + ph + Inches(0.15), max(pw, Inches(3.2)), Inches(0.6), cap, 13, MUTED)
        x += pw + gap


# =====================================================================
# 14. The ask (fill in before presenting)
# =====================================================================
s = new_slide("The ask", "Help us take Hydra Pay from prototype to pilot", notes=(
    "FILL IN BEFORE PRESENTING: the amount you are asking for, and how it splits across hardware, going live, the pilot "
    "and the team. Say exactly what the money or support unlocks, for example: 20 readers in 10 businesses for 3 months."
))
box(s, Inches(0.7), Inches(1.95), Inches(5.0), Inches(4.5), fill=CARD2, line=AMBER)
text(s, Inches(1.0), Inches(2.2), Inches(4.4), Inches(0.4), "We are asking for", 16, MUTED)
text(s, Inches(1.0), Inches(2.7), Inches(4.4), Inches(1.0), "KSh [amount]", 44, AMBER, bold=True)
text(s, Inches(1.0), Inches(3.75), Inches(4.4), Inches(2.5),
     "[Grant / prize / investment / partnership, and what it unlocks, e.g. 20 readers in 10 businesses for a 3-month pilot.]",
     15, MUTED, spacing=1.2)
uses = (
    ("Hardware", "[ %]", "Readers, cards and tags for pilot businesses"),
    ("Go live", "[ %]", "Live Safaricom till, USSD short code, SMS credit, hosting"),
    ("Pilot", "[ %]", "Onboarding, support and measuring results"),
    ("Team", "[ %]", "Build the offline reader and multi-stall dashboard"),
)
for i, (t, pct, b) in enumerate(uses):
    y = Inches(1.95) + i * Inches(1.15)
    box(s, Inches(6.0), y, Inches(6.6), Inches(1.0))
    text(s, Inches(6.3), y + Inches(0.15), Inches(1.1), Inches(0.7), pct, 22, AMBER, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(7.5), y + Inches(0.14), Inches(4.9), Inches(0.4), t, 16, TEXT, bold=True)
    text(s, Inches(7.5), y + Inches(0.52), Inches(4.9), Inches(0.4), b, 13, MUTED)

# =====================================================================
# 15. Close
# =====================================================================
s = new_slide(notes=(
    "Hydra Pay: fast payments, safer transactions, clearer records. Scan the code to try the demo on your phone, "
    "or come to our table and tap a real card. Thank you, we're happy to take questions."
))
text(s, Inches(0.8), Inches(0.75), Inches(6.5), Inches(2.6),
     [[("Tap.", {})], [("Pay.", {})], [("Done.", {"color": BLUE})]], 54, TEXT, bold=True, spacing=0.95)
text(s, Inches(0.8), Inches(3.7), Inches(5.6), Inches(0.8),
     "Fast payments, safer transactions, clearer records.", 19, MUTED)
qr = box(s, Inches(0.8), Inches(4.65), Inches(1.75), Inches(1.75), fill=WHITE, line=None, radius=0.06)
image(s, ROOT / "pitch" / "qr" / "hydra-pay-landing.png", Inches(0.875), Inches(4.725), w=Inches(1.6), h=Inches(1.6), border=False)
text(s, Inches(2.85), Inches(4.8), Inches(4), Inches(1.6), [
    [("Scan to try the demo", {"bold": True, "color": TEXT, "size": 18})],
    [(SITE, {"color": BLUE, "size": 16})],
    [("Questions? Come tap a real card at our table.", {"size": 14})],
], 14, MUTED, spacing=1.4)
image(s, ASSETS / "demo_crop.png", Inches(6.9), Inches(1.6), w=Inches(5.8))
text(s, Inches(6.9), Inches(4.42), Inches(5.8), Inches(0.4), "The try-it demo on our website", 12, MUTED, align=PP_ALIGN.CENTER)

prs.save(OUT)
print(f"Saved {OUT} ({slide_no} slides)")
