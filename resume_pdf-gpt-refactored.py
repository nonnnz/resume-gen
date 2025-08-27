#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate multi-page PDF resumes from JSON (supports EN/TH),
with width-aware wrapping and automatic page breaks.

Usage:
  python resume_pdf.py --data resume_all.json --theme modern --outdir out_pdfs
  (The JSON file may contain a single object or an array of resume records.)
"""

from glob import glob
import os
import random
import sys
import json
import argparse
import datetime
import textwrap
from typing import Any, Dict, List, Optional

# ReportLab
from matplotlib.pylab import rec
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re


HERE = os.path.abspath(os.path.dirname(__file__))

# ---------------- Fonts ----------------


def _try_register(name: str, path: str) -> bool:
    if not os.path.exists(path):
        return False
    try:
        pdfmetrics.registerFont(TTFont(name, path))
        return True
    except Exception:
        return False


def _register_fonts():
    """
    Register Latin + Thai fonts if present.
    Looks in ./, ./fonts, and RESUME_FONT_DIR for common filenames.
    """
    search_dirs = [HERE, os.path.join(HERE, "fonts")]
    if os.environ.get("RESUME_FONT_DIR"):
        search_dirs.append(os.environ["RESUME_FONT_DIR"])

    # candidate files (regular/bold) for Thai
    candidates = [
        # Noto Sans Thai
        ("NotoSansThai",       "NotoSansThai-Regular.ttf"),
        ("NotoSansThai-Bold",  "NotoSansThai-Bold.ttf"),
        # Noto Sans Thai (variable) – register same name twice (ReportLab will pick one)
        ("NotoSansThai",       "NotoSansThai-VariableFont_wdth,wght.ttf"),
        ("NotoSansThai-Bold",  "NotoSansThai-VariableFont_wdth,wght.ttf"),
        # Sarabun
        ("Sarabun",            "Sarabun-Regular.ttf"),
        ("Sarabun-Bold",       "Sarabun-Bold.ttf"),
        # Latin fallbacks
        ("NotoSans",           "NotoSansThai-Regular.ttf"),
        ("NotoSans-Bold",      "NotoSansThai-Bold.ttf"),
    ]

    # try exact matches first
    for name, fname in candidates:
        for d in search_dirs:
            if _try_register(name, os.path.join(d, fname)):
                pass

    # also try globbing for fonts (helps on systems with different filenames)
    patterns = [
        ("NotoSansThai",      "*Noto*Sans*Thai*Regular*.ttf"),
        ("NotoSansThai-Bold", "*Noto*Sans*Thai*Bold*.ttf"),
        ("Sarabun",           "*Sarabun*Regular*.ttf"),
        ("Sarabun-Bold",      "*Sarabun*Bold*.ttf"),
        ("NotoSans",          "*Noto*Sans*Regular*.ttf"),
        ("NotoSans-Bold",     "*Noto*Sans*Bold*.ttf"),
    ]
    for name, pat in patterns:
        for d in search_dirs:
            for p in glob(os.path.join(d, pat)):
                _try_register(name, p)

    # Optionally define a font family alias (useful if you ever use Paragraph styles)
    try:
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        if "NotoSansThai" in pdfmetrics.getRegisteredFontNames():
            registerFontFamily("NotoSansThai",
                               normal="NotoSansThai", bold="NotoSansThai-Bold")
        if "Sarabun" in pdfmetrics.getRegisteredFontNames():
            registerFontFamily("Sarabun", normal="Sarabun",
                               bold="Sarabun-Bold")
        if "NotoSans" in pdfmetrics.getRegisteredFontNames():
            registerFontFamily("NotoSans", normal="NotoSans",
                               bold="NotoSans-Bold")
    except Exception:
        pass


_register_fonts()


def _thai_font_available() -> bool:
    names = set(pdfmetrics.getRegisteredFontNames())
    return any(n in names for n in ["NotoSansThai", "Sarabun"])


def _latin_font_available() -> bool:
    names = set(pdfmetrics.getRegisteredFontNames())
    return any(n in names for n in ["NotoSans", "Helvetica", "Times-Roman"])


# Use Thai-capable font if possible; otherwise Latin; never Helvetica for Thai.
def get_font(weight: str = "regular") -> str:
    bold = (weight == "bold")
    names = set(pdfmetrics.getRegisteredFontNames())

    if _thai_font_available():
        if bold and "NotoSansThai-Bold" in names:
            return "NotoSansThai-Bold"
        if "NotoSansThai" in names:
            return "NotoSansThai"
        if bold and "Sarabun-Bold" in names:
            return "Sarabun-Bold"
        if "Sarabun" in names:
            return "Sarabun"

    # Latin fallback
    if bold and "NotoSans-Bold" in names:
        return "NotoSans-Bold"
    if "NotoSans" in names:
        return "NotoSans"
    return "Helvetica-Bold" if bold else "Helvetica"


# Optional: safety check – call this before rendering each record
_TH_CHARS = re.compile(r"[\u0E00-\u0E7F]")


def ensure_thai_font_for_record(record: dict):
    lang = record.get("language", "en")
    needs_thai = (lang.lower() == "th")
    # Also check content contains Thai, in case lang tag wasn't set
    def textify(x): return x if isinstance(x, str) else ""
    blob = " ".join([textify(record.get("firstname", "")), textify(record.get("lastname", "")),
                     textify(record.get("address", "")), textify(record.get("profileSummary", ""))])
    if _TH_CHARS.search(blob):
        needs_thai = True

    if needs_thai and not _thai_font_available():
        raise RuntimeError(
            "Thai text detected but no Thai-capable font is registered. "
            "Place NotoSansThai-Regular.ttf and NotoSansThai-Bold.ttf (or Sarabun) "
            "next to resume_pdf.py or in ./fonts, or set RESUME_FONT_DIR."
        )


# ---------------- Themes / Colors ----------------
THEME_COLORS = {
    "modern": {
        "bg_accent": colors.HexColor("#EEF2FF"),   # soft indigo tint
        "accent":    colors.HexColor("#6366F1"),
        "secondary": colors.HexColor("#2563EB"),
        "text_primary": colors.HexColor("#111827"),
        "text_secondary": colors.HexColor("#6B7280")
    },
    "classic": {
        "bg_accent": colors.HexColor("#E0F2FE"),   # light sky
        "accent":    colors.HexColor("#0EA5E9"),
        "secondary": colors.HexColor("#0284C7"),
        "text_primary": colors.HexColor("#1F2937"),
        "text_secondary": colors.HexColor("#374151")
    },
    "minimal": {
        "bg_accent": colors.HexColor("#F3F4F6"),   # neutral
        "accent":    colors.HexColor("#6B7280"),
        "secondary": colors.HexColor("#4B5563"),
        "text_primary": colors.black,
        "text_secondary": colors.HexColor("#6B7280")
    }
}

# ---------------- Background ----------------


def draw_background_accent(c: canvas.Canvas, theme: str):
    """
    Draw a subtle header background bar on the current page.
    Called per-page when the page is created.
    """
    colors_theme = THEME_COLORS.get(theme, THEME_COLORS["modern"])
    w, h = A4
    c.saveState()
    c.setFillColor(colors_theme["bg_accent"])
    c.rect(0, h - 40*mm, w, 40*mm, fill=1, stroke=0)
    c.restoreState()


# ---------------- Dates / Localization ----------------
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May",
             "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_TH = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.",
             "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

LABELS = {
    "en": {
        "contact": "Contact",
        "email": "Email",
        "phone": "Phone",
        "address": "Address",
        "experience": "Experience",
        "education": "Education",
        "skills": "Skills",
        "technicalSkills": "Technical Skills",
        "softSkills": "Soft Skills",
        "certificates": "Certificates",
        "publications": "Publications",
        "projects": "Projects",
        "awards": "Awards",
        "languages": "Languages",
        "references": "References",
        "volunteer": "Volunteer",
        "present": "Present",
        "cgpa": "CGPA",
        "faculty": "Faculty",
        "major": "Major",
        "institution": "Institution",
        "summary": "Profile",
        "dob": "Date of Birth",
        "nationality": "Nationality",
        "tech": "Tech"
    },
    "th": {
        "contact": "ข้อมูลติดต่อ",
        "email": "อีเมล",
        "phone": "โทรศัพท์",
        "address": "ที่อยู่",
        "experience": "ประสบการณ์ทำงาน",
        "education": "การศึกษา",
        "skills": "ทักษะ",
        "technicalSkills": "ทักษะด้านเทคนิค",
        "softSkills": "ทักษะด้านอ่อน",
        "certificates": "ใบรับรอง",
        "publications": "ผลงานตีพิมพ์",
        "projects": "โปรเจกต์",
        "awards": "รางวัล",
        "languages": "ภาษา",
        "references": "ผู้รับรอง",
        "volunteer": "จิตอาสา",
        "present": "ปัจจุบัน",
        "cgpa": "เกรดเฉลี่ยสะสม",
        "faculty": "คณะ",
        "major": "สาขา",
        "institution": "สถาบัน",
        "summary": "สรุปโปรไฟล์",
        "dob": "วันเกิด",
        "nationality": "สัญชาติ",
        "tech": "เทคโนโลยี"
    }
}


def parse_iso(date_str: Optional[str]) -> Optional[datetime.date]:
    if not date_str:
        return None
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.date()
    except Exception:
        return None


def format_period(start_iso: Optional[str], end_iso: Optional[str], lang: str) -> str:
    start = parse_iso(start_iso)
    end = parse_iso(end_iso)
    months = MONTHS_EN if lang == "en" else MONTHS_TH
    present = LABELS.get(lang, LABELS["en"])["present"]

    def fmt(d: Optional[datetime.date]):
        return f"{months[d.month-1]} {d.year}" if d else None

    s = fmt(start) or ""
    e = fmt(end) if end else present
    return f"{s} – {e}" if s else e


def safe_get(d: Dict, key: str, default="") -> Any:
    v = d.get(key, default)
    return v if v is not None else default


def clamp_list(xs: Optional[List[str]], n=10) -> List[str]:
    if not xs:
        return []
    return list(xs)[:n]

# ---------------- Page Manager ----------------


class PageManager:
    """Handles page breaks and content flow and redraws background when paging."""

    def __init__(self, canvas_obj, theme, page_height=297*mm, margin_top=30*mm, margin_bottom=25*mm):
        self.canvas = canvas_obj
        self.theme = theme
        self.page_height = page_height
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.current_page = 1
        # First page background
        draw_background_accent(self.canvas, self.theme)

    @property
    def top_y(self):
        return self.page_height - self.margin_top

    def new_page(self):
        self.canvas.showPage()
        self.current_page += 1
        draw_background_accent(self.canvas, self.theme)
        return self.top_y

    def check_and_add_page(self, current_y, required_space=20*mm):
        """Ensure 'required_space' remains; if not, go to new page and return fresh y."""
        if current_y < (self.margin_bottom + required_space):
            return self.new_page()
        return current_y

    def get_remaining_space(self, current_y):
        return current_y - self.margin_bottom

# ---------------- Wrapping & Drawing ----------------


def _wrap_text_by_width(text, font_name, font_size, max_width_pt):
    """
    Greedy width-aware wrapping. Works with Thai and long tokens.
    Falls back to char-wise split when no spaces are present.
    """
    if not text:
        return []

    def width(s):
        try:
            return pdfmetrics.stringWidth(s, font_name, font_size)
        except Exception:
            # last-resort estimate
            return len(s) * font_size * 0.55

    words = text.split(" ")
    if len(words) > 1:
        lines, current = [], ""
        for w in words:
            candidate = w if not current else current + " " + w
            if width(candidate) <= max_width_pt:
                current = candidate
            else:
                if current:
                    lines.append(current)
                # if single word too long → split by chars
                if width(w) > max_width_pt:
                    part = ""
                    for ch in w:
                        if width(part + ch) <= max_width_pt:
                            part += ch
                        else:
                            if part:
                                lines.append(part)
                            part = ch
                    if part:
                        current = part
                    else:
                        current = ""
                else:
                    current = w
        if current:
            lines.append(current)
        return lines
    else:
        # No spaces → char-wise wrapping
        lines, current = [], ""
        for ch in text:
            if width(current + ch) <= max_width_pt:
                current += ch
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
        return lines


def draw_enhanced_text(c: canvas.Canvas, text: str, x, y, width_mm=170,
                       font_size=10, color=None, theme="modern",
                       max_lines=None, page_manager: Optional[PageManager] = None,
                       line_spacing=1.4, font_weight='regular'):
    """
    Width-aware wrapped text with per-line page breaking.
    Returns the updated y after drawing.
    """
    if not text:
        return y

    colors_theme = THEME_COLORS.get(theme, THEME_COLORS["modern"])
    text_color = color or colors_theme["text_primary"]
    font_name = get_font('bold' if font_weight == 'bold' else 'regular')

    c.setFont(font_name, font_size)
    c.setFillColor(text_color)

    max_width_pt = width_mm * mm
    lines = _wrap_text_by_width(text, font_name, font_size, max_width_pt)

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        # add ellipsis to the last line if truncated
        ell = "..."
        # ensure it fits
        while lines and pdfmetrics.stringWidth(lines[-1] + ell, font_name, font_size) > max_width_pt:
            lines[-1] = lines[-1][:-1]
        if lines:
            lines[-1] += ell

    line_height = font_size * line_spacing
    current_y = y

    for line in lines:
        if page_manager:
            current_y = page_manager.check_and_add_page(
                current_y, required_space=line_height + 2*mm)
        c.drawString(x, current_y, line)
        current_y -= line_height

    return current_y


def draw_enhanced_bullet_list(c: canvas.Canvas, items: List[str], x, y, theme: str,
                              font_size=10, max_items=None, page_manager: Optional[PageManager] = None,
                              width_mm=95):
    """
    Bullet list with width-aware wrapped items and per-line page breaking.
    """
    if not items:
        return y

    colors_theme = THEME_COLORS.get(theme, THEME_COLORS["modern"])
    display_items = items[:max_items] if max_items else items
    bullet_w = 4*mm
    line_height = font_size * 1.5
    current_y = y
    font_name = get_font('regular')

    for item in display_items:
        # choose a bullet style per theme
        def bullet_draw(Y):
            if theme == "modern":
                c.setFillColor(colors_theme["accent"])
                c.rect(x + 0.5*mm, Y + 1*mm, 2*mm, 1*mm, fill=1, stroke=0)
            elif theme == "classic":
                c.setFillColor(colors_theme["secondary"])
                c.circle(x + 1*mm, Y + 1.5*mm, 0.8*mm, fill=1, stroke=0)
            else:  # minimal
                c.setFillColor(colors_theme["secondary"])
                c.rect(x + 0.5*mm, Y + 1*mm, 1.5*mm, 1.5*mm, fill=1, stroke=0)

        # wrap by width
        wrapped = _wrap_text_by_width(
            item, font_name, font_size, (width_mm*mm) - bullet_w)

        # draw bullet + lines
        for i, line in enumerate(wrapped):
            if page_manager:
                current_y = page_manager.check_and_add_page(
                    current_y, required_space=line_height + 2*mm)
            if i == 0:
                bullet_draw(current_y)
            text_x = x + bullet_w
            c.setFont(font_name, font_size)
            c.setFillColor(colors_theme["text_primary"])
            c.drawString(text_x, current_y, line)
            current_y -= line_height

    return current_y

# ---------------- Section helpers ----------------


def draw_section_title(c, title: str, x, y, theme: str, font_size=12):
    colors_theme = THEME_COLORS.get(theme, THEME_COLORS["modern"])
    c.setFillColor(colors_theme["accent"])
    c.setFont(get_font('bold'), font_size)
    c.drawString(x, y, title)


def section_contact(c, data, x, y, theme, lang, w_mm=70, page_manager=None):
    L = LABELS.get(lang, LABELS["en"])
    colors_theme = THEME_COLORS.get(theme, THEME_COLORS["modern"])
    draw_section_title(c, L["contact"], x, y, theme)
    y -= 20

    y = draw_enhanced_text(c, f'{L["email"]}: {safe_get(data,"email")}', x, y-2, width_mm=w_mm,
                           theme=theme, page_manager=page_manager)
    y = draw_enhanced_text(c, f'{L["phone"]}: {safe_get(data,"phone")}', x, y-2, width_mm=w_mm,
                           theme=theme, page_manager=page_manager)
    y = draw_enhanced_text(c, f'{L["address"]}: {safe_get(data,"address")}', x, y-2, width_mm=w_mm,
                           theme=theme, page_manager=page_manager)

    socials = [data.get("linkedin"), data.get("github"), data.get("website")]
    socials = [s for s in socials if s]
    if socials:
        social = " | ".join(socials)
        y = draw_enhanced_text(c, social, x, y-2, width_mm=w_mm, font_size=9,
                               color=colors_theme["secondary"], theme=theme, page_manager=page_manager)
    if data.get("dateOfBirth"):
        y = draw_enhanced_text(c, f'{L["dob"]}: {data["dateOfBirth"]}', x, y-1, width_mm=w_mm,
                               font_size=9, color=colors_theme["text_secondary"],
                               theme=theme, page_manager=page_manager)
    if data.get("nationality"):
        y = draw_enhanced_text(c, f'{L["nationality"]}: {data["nationality"]}', x, y-1, width_mm=w_mm,
                               font_size=9, color=colors_theme["text_secondary"],
                               theme=theme, page_manager=page_manager)
    return y


def section_summary(c, data, x, y, theme, lang, w_mm=170, page_manager=None):
    txt = data.get("profileSummary")
    if not txt:
        return y
    draw_section_title(c, LABELS.get(lang, LABELS["en"])[
                       "summary"], x, y, theme)
    y -= 20
    return draw_enhanced_text(c, txt, x, y-2, width_mm=w_mm, font_size=10,
                              color=THEME_COLORS.get(theme, THEME_COLORS["modern"])[
                                  "text_secondary"],
                              theme=theme, page_manager=page_manager)


def section_experience(c, data, x, y, theme, lang, w_mm=95, page_manager=None):
    L = LABELS.get(lang, LABELS["en"])
    exps = data.get("experiencesList") or []
    if not exps:
        return y
    draw_section_title(c, L["experience"], x, y, theme)
    y -= 20
    for exp in exps:
        title = f'{safe_get(exp,"positionName")} — {safe_get(exp,"companyName")}'
        if exp.get("location"):
            title += f' ({exp["location"]})'
        y = draw_enhanced_text(c, title, x, y, width_mm=w_mm, font_size=11,
                               theme=theme, page_manager=page_manager, font_weight='bold')
        period = format_period(exp.get("startPeriod"),
                               exp.get("endPeriod"), lang)
        y = draw_enhanced_text(c, period, x, y-1, width_mm=w_mm, font_size=9,
                               color=THEME_COLORS[theme]["text_secondary"], theme=theme, page_manager=page_manager)
        desc = exp.get("description") or []
        if desc:
            y = draw_enhanced_bullet_list(c, desc, x, y-1, theme, font_size=9,
                                          page_manager=page_manager, width_mm=w_mm)
        tech = exp.get("technologies") or []
        if tech:
            y = draw_enhanced_text(c, f'{L["tech"]}: ' + ", ".join(tech), x, y-1, width_mm=w_mm,
                                   font_size=8, color=THEME_COLORS[theme]["text_secondary"],
                                   theme=theme, page_manager=page_manager)
        y -= 2
    return y


def section_education(c, data, x, y, theme, lang, w_mm=95, page_manager=None):
    L = LABELS.get(lang, LABELS["en"])
    edus = data.get("educationsList") or []
    if not edus:
        return y
    draw_section_title(c, L["education"], x, y, theme)
    y -= 20
    for edu in edus:
        line = f'{safe_get(edu,"degree").title()} — {safe_get(edu,"institution")}'
        y = draw_enhanced_text(c, line, x, y, width_mm=w_mm,
                               font_size=10, theme=theme, page_manager=page_manager)
        years = f'{safe_get(edu,"startYear")} – {safe_get(edu,"endYear") or L["present"]}'
        bits = []
        if safe_get(edu, "faculty"):
            bits.append(f'{L["faculty"]}: {edu["faculty"]}')
        if safe_get(edu, "major"):
            bits.append(f'{L["major"]}: {edu["major"]}')
        if safe_get(edu, "CGPA"):
            bits.append(f'{L["cgpa"]}: {edu["CGPA"]}')
        if bits:
            y = draw_enhanced_text(c, " • ".join(bits), x, y-1, width_mm=w_mm, font_size=9,
                                   color=THEME_COLORS[theme]["text_secondary"], theme=theme, page_manager=page_manager)
        y = draw_enhanced_text(c, years, x, y-1, width_mm=w_mm, font_size=9,
                               color=THEME_COLORS[theme]["text_secondary"], theme=theme, page_manager=page_manager)
        honors = edu.get("honors") or []
        if honors:
            y = draw_enhanced_bullet_list(
                c, honors, x, y-1, theme, font_size=9, page_manager=page_manager, width_mm=w_mm)
        y -= 2
    return y


def section_projects(c, data, x, y, theme, lang, w_mm=95, page_manager=None):
    L = LABELS.get(lang, LABELS["en"])
    projects = data.get("projectsList") or []
    if not projects:
        return y
    draw_section_title(c, L["projects"], x, y, theme)
    y -= 20
    for p in projects:
        techs = ", ".join(p.get("technologies", []))
        header = p.get("title", "")
        header = f'{header} — {techs}' if techs else header
        y = draw_enhanced_text(c, header, x, y, width_mm=w_mm,
                               font_size=10, theme=theme, page_manager=page_manager)
        if p.get("description"):
            y = draw_enhanced_text(c, p["description"], x, y-1, width_mm=w_mm, font_size=9,
                                   theme=theme, page_manager=page_manager)
        if p.get("link"):
            y = draw_enhanced_text(c, p["link"], x, y-1, width_mm=w_mm, font_size=9,
                                   color=THEME_COLORS[theme]["secondary"], theme=theme, page_manager=page_manager)
        y = draw_enhanced_text(c, format_period(p.get("startPeriod"), p.get("endPeriod"), lang),
                               x, y-1, width_mm=w_mm, font_size=9,
                               color=THEME_COLORS[theme]["text_secondary"], theme=theme, page_manager=page_manager)
        y -= 2
    return y


def section_skills(c, data, x, y, theme, lang, w_mm=70, page_manager=None):
    L = LABELS.get(lang, LABELS["en"])
    skills = clamp_list(data.get("skills"), 10)
    if skills:
        draw_section_title(c, L["skills"], x, y, theme)
        y -= 20
        y = draw_enhanced_bullet_list(
            c, skills, x, y-1, theme, font_size=10, page_manager=page_manager, width_mm=w_mm)
        y -= 2

    tskills = data.get("technicalSkills") or {}
    if tskills:
        draw_section_title(c, L["technicalSkills"], x, y, theme)
        y -= 20
        for group, vals in tskills.items():
            cap = group.replace("_", " ").title()
            y = draw_enhanced_text(c, f"{cap}: " + ", ".join(vals), x, y, width_mm=w_mm, font_size=9,
                                   color=THEME_COLORS[theme]["text_secondary"], theme=theme, page_manager=page_manager)
            y -= 1

    sskills = data.get("softSkills") or []
    if sskills:
        draw_section_title(c, L["softSkills"], x, y, theme)
        y -= 20
        y = draw_enhanced_bullet_list(
            c, sskills, x, y-1, theme, font_size=10, page_manager=page_manager, width_mm=w_mm)
    return y


def section_certificates(c, data, x, y, theme, lang, w_mm=95, page_manager=None):
    certs = data.get("certificates") or []
    if not certs:
        return y
    draw_section_title(c, LABELS.get(lang, LABELS["en"])[
                       "certificates"], x, y, theme)
    y -= 20
    return draw_enhanced_bullet_list(c, certs, x, y-1, theme, font_size=10, page_manager=page_manager, width_mm=w_mm)


def section_publications(c, data, x, y, theme, lang, w_mm=95, page_manager=None):
    pubs = data.get("publications") or []
    if not pubs:
        return y
    draw_section_title(c, LABELS.get(lang, LABELS["en"])[
                       "publications"], x, y, theme)
    y -= 20
    return draw_enhanced_bullet_list(c, pubs, x, y-1, theme, font_size=10, page_manager=page_manager, width_mm=w_mm)


def section_awards(c, data, x, y, theme, lang, w_mm=95, page_manager=None):
    L = LABELS.get(lang, LABELS["en"])
    aw = data.get("awardsList") or []
    if not aw:
        return y
    draw_section_title(c, L["awards"], x, y, theme)
    y -= 20
    for a in aw:
        line = f'{safe_get(a,"name")}'
        tail = []
        if a.get("issuer"):
            tail.append(a["issuer"])
        if a.get("year"):
            tail.append(str(a["year"]))
        if tail:
            line += " — " + ", ".join(tail)
        y = draw_enhanced_text(c, line, x, y, width_mm=w_mm,
                               font_size=10, theme=theme, page_manager=page_manager)
        if a.get("description"):
            y = draw_enhanced_text(c, a["description"], x, y-1, width_mm=w_mm, font_size=9,
                                   color=THEME_COLORS[theme]["text_secondary"], theme=theme, page_manager=page_manager)
        y -= 2
    return y


def section_languages_spoken(c, data, x, y, theme, lang, w_mm=95, page_manager=None):
    L = LABELS.get(lang, LABELS["en"])
    langs = data.get("languagesSpoken") or []
    if not langs:
        return y
    draw_section_title(c, L["languages"], x, y, theme)
    y -= 20
    items = [f'{l.get("language","")} — {l.get("proficiency","")}'.strip(
        " —") for l in langs]
    return draw_enhanced_bullet_list(c, items, x, y-1, theme, font_size=10, page_manager=page_manager, width_mm=w_mm)


def section_references(c, data, x, y, theme, lang, w_mm=95, page_manager=None):
    L = LABELS.get(lang, LABELS["en"])
    refs = data.get("referencesList") or []
    if not refs:
        return y
    draw_section_title(c, L["references"], x, y, theme)
    y -= 20
    for r in refs:
        line = f'{safe_get(r,"name")}'
        meta = []
        if r.get("relationship"):
            meta.append(r["relationship"])
        if r.get("company"):
            meta.append(r["company"])
        if meta:
            line += f' ({", ".join(meta)})'
        if r.get("contact"):
            line += f' — {r["contact"]}'
        y = draw_enhanced_text(c, line, x, y, width_mm=w_mm,
                               font_size=10, theme=theme, page_manager=page_manager)
        y -= 2
    return y


def section_volunteer(c, data, x, y, theme, lang, w_mm=95, page_manager=None):
    L = LABELS.get(lang, LABELS["en"])
    vol = data.get("volunteerExperience") or []
    if not vol:
        return y
    draw_section_title(c, L["volunteer"], x, y, theme)
    y -= 20
    for v in vol:
        hdr = f'{safe_get(v,"role")} — {safe_get(v,"organization")}'
        y = draw_enhanced_text(c, hdr, x, y, width_mm=w_mm,
                               font_size=10, theme=theme, page_manager=page_manager)
        y = draw_enhanced_text(c, format_period(v.get("startPeriod"), v.get("endPeriod"), lang),
                               x, y-1, width_mm=w_mm, font_size=9,
                               color=THEME_COLORS[theme]["text_secondary"], theme=theme, page_manager=page_manager)
        acts = v.get("activities") or []
        if acts:
            y = draw_enhanced_bullet_list(
                c, acts, x, y-1, theme, font_size=9, page_manager=page_manager, width_mm=w_mm)
        y -= 2
    return y

# ---------------- Header ----------------


def draw_header(c: canvas.Canvas, data: Dict[str, Any], theme: str, x=20*mm, y=275*mm, w=170*mm):
    colors_theme = THEME_COLORS.get(theme, THEME_COLORS["modern"])
    full_name = f'{safe_get(data,"firstname")} {safe_get(data,"lastname")}'.strip(
    )

    c.setFillColor(colors_theme["text_primary"])
    c.setFont(get_font('bold'), 18)
    c.drawString(x, y, full_name)

    headline = safe_get(data, "headline", "")
    if headline:
        c.setFillColor(colors_theme["accent"])
        c.setFont(get_font('regular'), 11)
        c.drawString(x, y-7*mm, headline)

    # divider line
    c.setStrokeColor(colors_theme["accent"])
    c.setLineWidth(1.2)
    c.line(x, y-10*mm, x+w, y-10*mm)

# ---------------- Theme renderers ----------------


def render_modern(c, data):
    lang = data.get("language", "en")
    page_manager = PageManager(c, "modern")
    # header
    draw_header(c, data, "modern", x=20*mm, y=275*mm, w=170*mm)

    # columns
    margin_x = 20*mm
    left_w = 70*mm
    col_gap = 10*mm
    right_x = margin_x + left_w + col_gap
    right_w = (A4[0] - margin_x) - right_x

    yL = page_manager.top_y - 30*mm
    yR = page_manager.top_y - 30*mm

    yL = section_contact(c, data, margin_x, yL, "modern",
                         lang, w_mm=left_w/mm, page_manager=page_manager)
    yL = section_summary(c, data, margin_x, yL-4, "modern",
                         lang, w_mm=left_w/mm, page_manager=page_manager)
    yL = section_skills(c, data, margin_x, yL-4, "modern",
                        lang, w_mm=left_w/mm, page_manager=page_manager)

    yR = section_experience(c, data, right_x, yR, "modern",
                            lang, w_mm=right_w/mm, page_manager=page_manager)
    yR = section_projects(c, data, right_x, yR-2, "modern",
                          lang, w_mm=right_w/mm, page_manager=page_manager)
    yR = section_education(c, data, right_x, yR-2, "modern",
                           lang, w_mm=right_w/mm, page_manager=page_manager)
    yR = section_certificates(c, data, right_x, yR-2, "modern",
                              lang, w_mm=right_w/mm, page_manager=page_manager)
    yR = section_awards(c, data, right_x, yR-2, "modern",
                        lang, w_mm=right_w/mm, page_manager=page_manager)
    yR = section_publications(c, data, right_x, yR-2, "modern",
                              lang, w_mm=right_w/mm, page_manager=page_manager)
    yR = section_languages_spoken(
        c, data, right_x, yR-2, "modern", lang, w_mm=right_w/mm, page_manager=page_manager)
    section_references(c, data, right_x, yR-2, "modern", lang,
                       w_mm=right_w/mm, page_manager=page_manager)


def render_classic(c, data):
    lang = data.get("language", "en")
    page_manager = PageManager(c, "classic")
    draw_header(c, data, "classic", x=20*mm, y=275*mm, w=170*mm)

    x = 20*mm
    y = page_manager.top_y - 30*mm

    # Contact (single block)
    y = section_contact(c, data, x, y, "classic", lang,
                        w_mm=170, page_manager=page_manager)
    y = section_summary(c, data, x, y-4, "classic", lang,
                        w_mm=170, page_manager=page_manager)
    y = section_experience(c, data, x, y-4, "classic",
                           lang, w_mm=170, page_manager=page_manager)
    y = section_projects(c, data, x, y-2, "classic", lang,
                         w_mm=170, page_manager=page_manager)
    y = section_education(c, data, x, y-2, "classic", lang,
                          w_mm=170, page_manager=page_manager)
    y = section_skills(c, data, x, y-2, "classic", lang,
                       w_mm=170, page_manager=page_manager)
    y = section_awards(c, data, x, y-2, "classic", lang,
                       w_mm=170, page_manager=page_manager)
    y = section_certificates(c, data, x, y-2, "classic",
                             lang, w_mm=170, page_manager=page_manager)
    y = section_publications(c, data, x, y-2, "classic",
                             lang, w_mm=170, page_manager=page_manager)
    y = section_languages_spoken(
        c, data, x, y-2, "classic", lang, w_mm=170, page_manager=page_manager)
    y = section_volunteer(c, data, x, y-2, "classic", lang,
                          w_mm=170, page_manager=page_manager)
    section_references(c, data, x, y-2, "classic", lang,
                       w_mm=170, page_manager=page_manager)


def render_minimal(c, data):
    lang = data.get("language", "en")
    page_manager = PageManager(c, "minimal")
    draw_header(c, data, "minimal", x=20*mm, y=275*mm, w=170*mm)

    x = 20*mm
    y = page_manager.top_y - 30*mm

    y = section_contact(c, data, x, y, "minimal", lang,
                        w_mm=170, page_manager=page_manager)
    y = section_summary(c, data, x, y-12, "minimal", lang,
                        w_mm=170, page_manager=page_manager)
    y = section_experience(c, data, x, y-12, "minimal",
                           lang, w_mm=170, page_manager=page_manager)
    y = section_projects(c, data, x, y-12, "minimal", lang,
                         w_mm=170, page_manager=page_manager)
    y = section_education(c, data, x, y-12, "minimal", lang,
                          w_mm=170, page_manager=page_manager)
    y = section_skills(c, data, x, y-12, "minimal", lang,
                       w_mm=170, page_manager=page_manager)
    y = section_awards(c, data, x, y-12, "minimal", lang,
                       w_mm=170, page_manager=page_manager)
    y = section_certificates(c, data, x, y-12, "minimal",
                             lang, w_mm=170, page_manager=page_manager)
    y = section_publications(c, data, x, y-12, "minimal",
                             lang, w_mm=170, page_manager=page_manager)
    y = section_languages_spoken(
        c, data, x, y-12, "minimal", lang, w_mm=170, page_manager=page_manager)
    y = section_volunteer(c, data, x, y-12, "minimal", lang,
                          w_mm=170, page_manager=page_manager)
    section_references(c, data, x, y-12, "minimal", lang,
                       w_mm=170, page_manager=page_manager)

# ---------------- Build & CLI ----------------


def build_pdf(data: Dict[str, Any], theme: str, out_path: str):
    c = canvas.Canvas(out_path, pagesize=A4)

    # Fallback headline
    data.setdefault("headline",
                    data.get("headline") or (data.get("experiencesList", [{}])[0].get("positionName", "")))

    # Cap flat skills at 10
    data["skills"] = clamp_list(data.get("skills"), 10)

    # Render selected theme
    if theme == "classic":
        render_classic(c, data)
    elif theme == "minimal":
        render_minimal(c, data)
    else:
        render_modern(c, data)

    c.save()


def suggest_outname(data: Dict[str, Any], theme: str) -> str:
    lang = data.get("language", "en")
    position = safe_get(data, "experiencesList", [{}])[
        0].get("positionName", "")
    fn = f"{safe_get(data,'firstname','')}_{safe_get(data,'lastname','')}_{position}_{lang}_{theme}.pdf"
    return "_".join([s for s in fn.replace(" ", "_").split("_") if s])


def main():
    ap = argparse.ArgumentParser(
        description="Generate résumé PDFs from JSON (supports array of records).")
    ap.add_argument("--data", required=True,
                    help="Path to JSON file (object or array of objects).")
    ap.add_argument("--theme", default="modern",
                    choices=["modern", "classic", "minimal"], help="Theme to use.")
    ap.add_argument("--out", default=None,
                    help="Output PDF path (only used for single-record JSON).")
    ap.add_argument("--outdir", default=".",
                    help="Directory for PDFs when --data has multiple records.")
    args = ap.parse_args()

    try:
        with open(args.data, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"Failed to read JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Single or multiple records
    records = payload if isinstance(payload, list) else [payload]

    if len(records) == 1 and args.out:
        out = args.out
        build_pdf(records[0], args.theme, out)
        print(f"✅ Generated: {out}")
        return

    os.makedirs(args.outdir, exist_ok=True)
    for rec in records:
        ensure_thai_font_for_record(rec)
        # just random theme
        theme = random.choice(["modern", "classic", "minimal"])
        out = os.path.join(args.outdir, suggest_outname(rec, theme))
        build_pdf(rec, theme, out)
        print(f"✅ Generated: {out}")


if __name__ == "__main__":
    main()
