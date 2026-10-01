"""Test loader: expose scripts/build_profile_svgs.py symbols WITHOUT executing
its module-level network collection.

Mechanism (characterization only — no copies, no mocks): parse the module's
real source on every run and exec only (a) imports, (b) every function def,
(c) module constants on a name allowlist. Nodes are selected by NAME, not line
number, so the loader survives refactors that move code within the file; the
collection section (~L251-496) and orchestration (~L1919+) are simply never
executed. If the module later grows an import-safe layout, tests may switch to
a plain import — assertions must not change either way (see Gate 1)."""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_profile_svgs.py"

# Module-level constants the pure functions close over (sections A/C/E).
_CONSTANTS = frozenset({
    "USER", "TZ", "EN", "ZH", "README_FILES", "ACC_REPO", "TRUNK",
    "MIN_SOURCE_COMMITS", "FIRST_YEAR", "RHYTHM_ORIGIN", "DIFY_OWNER",
    "CONVENTIONAL", "FACT_KEYS", "FIG_SPEC", "SRC_PREFIX", "MARKER",
    "FONT", "LIGHT", "DARK", "_GLYPHS", "GLYPH_W", "FONT_SLACK",
    "BANNED", "KEYFRAME", "TEXT_EL", "FILL_ONLY", "STROKED",
    "LAT_EDGES", "LAT_LABELS", "RUG_DAYS", "GEN_SITE", "HOUR_ORDER",
})


def _target_names(node):
    out = set()
    for t in node.targets:
        if isinstance(t, ast.Name):
            out.add(t.id)
        elif isinstance(t, ast.Tuple):
            out |= {e.id for e in t.elts if isinstance(e, ast.Name)}
    return out


def _selected(tree):
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Try)):
            yield node
        elif isinstance(node, ast.FunctionDef):
            yield node
        elif isinstance(node, ast.Assign) and _target_names(node) <= _CONSTANTS:
            yield node


def load():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    module = ast.Module(body=list(_selected(tree)), type_ignores=[])
    ns = {"__name__": "build_profile_svgs_under_test"}
    exec(compile(module, str(MODULE_PATH), "exec"), ns)
    return ns


NS = load()
