import asyncio
import sys
sys.path.insert(0, r"C:\Users\student\Documents\Default Project\guest-lecture-review")

from app.parser import parse_document
from scripts.generate_samples import generate_good_report, generate_bad_report
from pathlib import Path
from app.validators.template.template_validator import TemplateValidator
from app.validators.formatting.formatting_validator import FormattingValidator
from app.checkers.completeness.completeness_checker import CompletenessChecker
from app.checkers.semantic.semantic_checker import SemanticChecker
from app.checkers.grammar.grammar_checker import GrammarChecker
from app.checkers.policy.policy_checker import PolicyChecker
from app.scoring.scoring_agent import compute_report

# Generate samples if needed
good_path = Path("samples/report_good.docx")
bad_path = Path("samples/report_bad.docx")
if not good_path.exists():
    generate_good_report(good_path)
if not bad_path.exists():
    generate_bad_report(bad_path)

good = parse_document(good_path)
bad = parse_document(bad_path)

t_good = TemplateValidator().validate(good)
t_bad = TemplateValidator().validate(bad)

f_good = FormattingValidator().validate(good)
f_bad = FormattingValidator().validate(bad)

comp_good = asyncio.run(CompletenessChecker().check(good))
comp_bad = asyncio.run(CompletenessChecker().check(bad))

sem_good = asyncio.run(SemanticChecker().check(good))
sem_bad = asyncio.run(SemanticChecker().check(bad))

gram_good = asyncio.run(GrammarChecker().check(good))
gram_bad = asyncio.run(GrammarChecker().check(bad))

pol_good = PolicyChecker().check(good)
pol_bad = PolicyChecker().check(bad)

rg = compute_report(t_good, f_good, comp_good, sem_good, gram_good, pol_good, good)
rb = compute_report(t_bad, f_bad, comp_bad, sem_bad, gram_bad, pol_bad, bad)

print("=== Good report ===")
print(f"Overall score: {rg.overall_score}/{rg.overall_max} (grade {rg.grade})")
for c in rg.criteria:
    print(f"  {c.id:20s}: score={c.score:5.1f} / {c.max_score:5.1f}  ({c.mode})  detail={c.detail}")

print("\n=== Bad report ===")
print(f"Overall score: {rb.overall_score}/{rb.overall_max} (grade {rb.grade})")
for c in rb.criteria:
    print(f"  {c.id:20s}: score={c.score:5.1f} / {c.max_score:5.1f}  ({c.mode})  detail={c.detail}")

print("\nMissing items (good):", rg.missing_items)
print("Missing items (bad):", rb.missing_items)
print("\nSuggestions (good):", [s.title for s in rg.suggestions])
print("Suggestions (bad):", [s.title for s in rb.suggestions])