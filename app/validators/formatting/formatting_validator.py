"""Module 3: Formatting Validator (rule-based, no LLM).

Compares the document's actual formatting against config/formatting_spec.yaml:
font family, font size, heading size, bold/italics, line spacing, margins,
page numbers, header/footer, table style, image alignment, bullet style.
"""

from typing import Optional

from app.config_loader import load_formatting_spec
from app.schemas.document import ParsedDocument
from app.schemas.modules import FormattingCheckResult, FormattingRuleResult


class FormattingValidator:
    def __init__(self, spec: Optional[dict] = None):
        self.spec = spec or load_formatting_spec()

    # ------------------------------------------------------------- helpers
    def _body_paragraphs(self, doc: ParsedDocument):
        return [p for p in doc.paragraphs if not (p.style and p.style.lower().startswith("heading"))]

    def _heading_paragraphs(self, doc: ParsedDocument):
        return [p for p in doc.paragraphs if p.style and p.style.lower().startswith("heading")]

    def _dominant_body_font(self, doc: ParsedDocument) -> Optional[dict]:
        fonts = [p.dominant_font for p in self._body_paragraphs(doc) if p.dominant_font]
        if not fonts:
            return None
        return {
            "family": max((f.family or "" for f in fonts), key=lambda x: sum(1 for g in fonts if (g.family or "").lower() == x.lower())),
            "size": max((f.size_pt or 0 for f in fonts), key=lambda x: sum(1 for g in fonts if (g.size_pt or 0) == x)),
        }

    def _r(self, rule, label, passed, expected, actual, severity="major"):
        return FormattingRuleResult(
            rule=rule, label=label, passed=passed, expected=expected,
            actual=actual, severity=severity,
        )

    # ------------------------------------------------------------- rules
    def _check_body_font(self, doc: ParsedDocument) -> list[FormattingRuleResult]:
        spec = self.spec["body"]
        out = []
        paragraphs = self._body_paragraphs(doc)
        if not paragraphs:
            return [self._r("body_font_family", "Body font family", False, spec["font_family"], "no body text")]
        fonts = [p.dominant_font for p in paragraphs if p.dominant_font]
        if not fonts:
            return [self._r("body_font_family", "Body font family", False, spec["font_family"], "unknown")]

        # family: most common among non-empty
        fams = [f.family or "" for f in fonts]
        fams = [f for f in fams if f]
        if fams:
            common = max(set(fams), key=fams.count)
            expected_fam = spec["font_family"].lower()
            fam_ok = common.lower() == expected_fam or expected_fam in common.lower()
            out.append(self._r("body_font_family", "Body font family", fam_ok, spec["font_family"], common, "major" if fam_ok else "major"))
        else:
            out.append(self._r("body_font_family", "Body font family", False, spec["font_family"], "unknown"))

        # size
        sizes = [f.size_pt for f in fonts if f.size_pt]
        if sizes:
            common_size = max(set(sizes), key=sizes.count)
            tol = spec.get("font_size_tolerance_pt", 0.5)
            size_ok = abs(common_size - spec["font_size_pt"]) <= tol
            out.append(self._r("body_font_size", "Body font size", size_ok, spec["font_size_pt"], common_size))
        else:
            out.append(self._r("body_font_size", "Body font size", False, spec["font_size_pt"], "unknown"))

        # line spacing
        spacings = [p.line_spacing for p in paragraphs if p.line_spacing]
        if spacings:
            common_sp = max(set(spacings), key=spacings.count)
            tol = spec.get("line_spacing_tolerance", 0.05)
            ok = abs(common_sp - spec["line_spacing"]) <= tol
            out.append(self._r("line_spacing", "Line spacing", ok, spec["line_spacing"], common_sp))
        else:
            out.append(self._r("line_spacing", "Line spacing", True, spec["line_spacing"], "n/a", "minor"))

        # bold/italics usage sanity: body should not be entirely bold
        bold_frac = sum(1 for f in fonts if f.bold) / max(len(fonts), 1)
        if bold_frac > 0.9:
            out.append(self._r("body_bold", "Body not fully bold", False, "bold fraction < 0.9", f"{bold_frac:.0%}"))
        else:
            out.append(self._r("body_bold", "Body not fully bold", True, "bold fraction < 0.9", f"{bold_frac:.0%}", "minor"))
        return out

    def _check_headings(self, doc: ParsedDocument) -> list[FormattingRuleResult]:
        spec = self.spec["headings"]
        headings = self._heading_paragraphs(doc)
        if not headings:
            return [self._r("headings_style", "Heading styles used", False, ">=1 heading-style paragraph", "0 headings")]
        fonts = [h.dominant_font for h in headings if h.dominant_font]
        if not fonts:
            return [self._r("headings_style", "Heading styles used", True, "-", "no font info", "minor")]
        fams = [f.family or "" for f in fonts]
        fams = [f for f in fams if f]
        if fams:
            common = max(set(fams), key=fams.count)
            expected = spec["font_family"].lower()
            ok = common.lower() == expected or expected in common.lower()
            out = [self._r("heading_font_family", "Heading font family", ok, spec["font_family"], common)]
        else:
            out = [self._r("heading_font_family", "Heading font family", True, spec["font_family"], "unknown", "minor")]
        body = self._dominant_body_font(doc)
        sizes = [f.size_pt for f in fonts if f.size_pt]
        if sizes and body and body["size"]:
            common_size = max(set(sizes), key=sizes.count)
            ratio = common_size / body["size"]
            ok = abs(ratio - spec["size_ratio_vs_body"]) <= 0.4
            out.append(self._r("heading_size_ratio", "Heading size vs body", ok, f"{spec['size_ratio_vs_body']}x", f"{ratio:.2f}x"))
        else:
            out.append(self._r("heading_size_ratio", "Heading size vs body", True, "-", "n/a", "minor"))
        return out

    def _check_page(self, doc: ParsedDocument) -> list[FormattingRuleResult]:
        spec = self.spec["page"]
        out = []
        m = doc.margins
        tol = spec.get("margins_tolerance_inches", 0.2)
        for side, key in (("top", "top_in"), ("bottom", "bottom_in"), ("left", "left_in"), ("right", "right_in")):
            expected = spec["margins_inches"][side]
            actual = getattr(m, key)
            if actual is None:
                out.append(self._r(f"margin_{side}", f"Margin ({side})", False, expected, "unavailable", "minor"))
            else:
                ok = abs(actual - expected) <= tol
                out.append(self._r(f"margin_{side}", f"Margin ({side})", ok, expected, actual))
        pn = spec.get("page_numbers_required", True)
        if pn:
            out.append(self._r("page_numbers", "Page numbers", doc.page_numbers_present, "present", doc.page_numbers_present))
        if spec.get("header_required"):
            out.append(self._r("header", "Header present", bool(doc.header_text), "non-empty", doc.header_text or "(empty)"))
        else:
            out.append(self._r("header", "Header (optional)", True, "-", doc.header_text or "(none)", "minor"))
        if spec.get("footer_required"):
            out.append(self._r("footer", "Footer present", bool(doc.footer_text), "non-empty", doc.footer_text or "(empty)"))
        else:
            out.append(self._r("footer", "Footer (optional)", True, "-", doc.footer_text or "(none)", "minor"))
        return out

    def _check_tables(self, doc: ParsedDocument) -> list[FormattingRuleResult]:
        spec = self.spec["tables"]
        if not doc.tables:
            return [self._r("table_style", "Table style", True, "-", "no tables", "minor")]
        if doc.file_type != "docx":
            return [self._r("table_style", "Table style", True, "docx-only rule", "pdf tables", "minor")]
        allowed = [s.lower() for s in spec.get("allowed_styles", [])]
        bad = [t.style for t in doc.tables if not t.style or (t.style.lower() not in allowed and t.style.lower() != "table grid")]
        # allow "Table Grid" default and listed styles
        ok = not bad
        return [self._r("table_style", "Table style", ok, spec["allowed_styles"], bad or "all styled")]

    def _check_images(self, doc: ParsedDocument) -> list[FormattingRuleResult]:
        spec = self.spec["images"]
        if not doc.images:
            return [self._r("image_alignment", "Image alignment", True, spec["alignment"], "no images", "minor")]
        expected = spec["alignment"]
        if expected == "any":
            return [self._r("image_alignment", "Image alignment", True, "any", "-", "minor")]
        alignments = [img.alignment for img in doc.images if img.alignment]
        if not alignments:
            return [self._r("image_alignment", "Image alignment", True, expected, "not captured (PDF)", "minor")]
        ok = all(a == expected for a in alignments)
        return [self._r("image_alignment", "Image alignment", ok, expected, alignments)]

    def _check_bullets(self, doc: ParsedDocument) -> list[FormattingRuleResult]:
        spec = self.spec["bullets"]
        bullets = [p for p in doc.paragraphs if p.bullet]
        if not bullets:
            return [self._r("bullet_style", "Bullet style", True, "-", "no lists used", "minor")]
        markers = [p.list_marker or p.text[:1] for p in bullets if p.text]
        accepted = spec["accepted_markers"]
        unknown = [m for m in markers if m not in accepted]
        ok = not unknown
        return [self._r("bullet_style", "Bullet style", ok, accepted, f"{len(bullets)} list paragraphs", "major" if unknown else "minor")]

    # ------------------------------------------------------------- entry
    def validate(self, doc: ParsedDocument) -> FormattingCheckResult:
        results: list[FormattingRuleResult] = []
        results += self._check_body_font(doc)
        results += self._check_headings(doc)
        results += self._check_page(doc)
        results += self._check_tables(doc)
        results += self._check_images(doc)
        results += self._check_bullets(doc)
        return FormattingCheckResult(results=results)