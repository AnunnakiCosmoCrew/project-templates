"""The Claude PR review workflow (workflows/claude-pr-review.yml, installed as
.github/workflows/claude-review.yml): which events review, and that an event the job skips can
never cancel a review in progress (PT-43). Standard library only.

The job's `if:` and the concurrency group are GitHub expressions. Both are translated to Python
and evaluated against event payloads shaped like GitHub's, so the test checks behaviour, not
text: for every event, the run shares the PR's concurrency group exactly when the job would
review."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "workflows" / "claude-pr-review.yml"
INSTALLED = ROOT / ".github" / "workflows" / "claude-review.yml"
TEMPLATE = CANONICAL.read_text(encoding="utf-8")


def block(after, job=None):
    """The value of `after`: a folded (`>-`) scalar joined into one line, or a one-line value.
    With `job`, only that job's section of the file is searched."""
    text = TEMPLATE
    if job:
        m = re.search(r"\n  %s:\n(.*?)(?=\n  [\w-]+:\n|\Z)" % re.escape(job), TEMPLATE, re.S)
        assert m, f"job {job} not found in {CANONICAL.name}"
        text = m.group(1) + "\n"
    deeper = len(after) - len(after.lstrip(" ")) + 1         # continuation lines sit deeper than the key
    m = re.search(re.escape(after) + r" >-\n((?:[ ]{%d,}.*\n)+)" % deeper, text)
    if m:
        return " ".join(line.strip() for line in m.group(1).splitlines())
    m = re.search(re.escape(after) + r" (.+)\n", text)
    assert m, f"{after.strip()} not found in {CANONICAL.name}"
    return m.group(1).strip()


JOB_IF = block("    if:", job="review")
TIER_IF = block("    if:", job="founder-tier")
GROUP = block("  group:")


def lookup(ctx, path):
    cur = ctx
    for part in path.split("."):
        if part == "*":                                  # labels.*.name: the next part maps over the list
            continue
        if isinstance(cur, list):
            cur = [x.get(part) for x in cur]
        else:
            cur = (cur or {}).get(part)
    return cur


def py(expr):
    """GitHub expression → Python expression over `C(path)`. Covers what these two use."""
    expr = re.sub(r"\$\{\{(.*?)\}\}", r" (\1) ", expr)
    expr = re.sub(r"contains\(([\w.*\[\]]+),\s*('[^']*')\)", r"(\2 in (C('\1') or []))", expr)
    expr = re.sub(r"(?<!C\(')(?<![\w.'])((?:github|vars|inputs)\.[\w.*\[\]]+)", r"C('\1')", expr)
    expr = expr.replace("&&", " and ").replace("||", " or ")
    expr = re.sub(r"!(?!=)", " not ", expr)
    expr = re.sub(r"(?<!')\bfalse\b(?!')", "False", expr)      # bare literals only, never 'true' in quotes
    expr = re.sub(r"(?<!')\btrue\b(?!')", "True", expr)
    return expr


def evaluate(expr, ctx):
    return eval(py(expr), {"C": lambda p: lookup(ctx, p)})


def group_of(ctx):
    """The concurrency group string for one event."""
    parts = re.split(r"(\$\{\{.*?\}\})", GROUP)
    return "".join(str(evaluate(p, ctx)) if p.startswith("${{") else p for p in parts).replace(" ", "")


def event(action, labels=(), label=None, draft=False, name="pull_request", actor="luvita-agents", same_repo=True, run_id=1):
    pr = {"number": 78, "draft": draft, "labels": [{"name": n} for n in labels],
          "head": {"repo": {"full_name": "AnunnakiCosmoCrew/x" if same_repo else "fork/x"}}}
    return {"github": {"event_name": name, "actor": actor, "repository": "AnunnakiCosmoCrew/x", "run_id": run_id,
                       "event": {"action": action, "pull_request": pr, "label": {"name": label} if label else None}},
            "vars": {"CLAUDE_REVIEW_ENABLED": "true"}, "inputs": {"pr": None}}


DISPATCH = {"github": {"event_name": "workflow_dispatch", "actor": "mertyertugrul", "repository": "AnunnakiCosmoCrew/x",
                       "run_id": 9, "event": {}}, "vars": {"CLAUDE_REVIEW_ENABLED": "true"}, "inputs": {"pr": "78"}}

CASES = {
    "label claude-review (draft)": event("labeled", ["claude-review"], "claude-review", draft=True),
    "label claude-review": event("labeled", ["claude-review"], "claude-review"),
    "label build-bundles": event("labeled", ["claude-review", "build-bundles"], "build-bundles", run_id=2),
    "label needs-mac on a draft": event("labeled", ["needs-mac"], "needs-mac", draft=True, run_id=3),
    "opened, no label": event("opened"),
    "opened as draft": event("opened", draft=True, run_id=4),
    "opened with the label": event("opened", ["claude-review"], run_id=5),
    "ready_for_review, no label": event("ready_for_review"),
    "ready_for_review with the label": event("ready_for_review", ["claude-review"], run_id=6),
    "reopened with the label": event("reopened", ["claude-review"]),
    "workflow_dispatch": DISPATCH,
    # The founder-tier job's trigger (ADR 0007): it must never review and never join the group.
    "target opened": event("opened", name="pull_request_target", run_id=10),
    "target synchronize": event("synchronize", name="pull_request_target", run_id=11),
    "target edited, with the label": event("edited", ["claude-review"], name="pull_request_target", run_id=12),
    "target ready_for_review": event("ready_for_review", name="pull_request_target", run_id=13),
}
TIERS = {"target opened", "target synchronize", "target edited, with the label", "target ready_for_review",
         "workflow_dispatch"}
REVIEWS = {"label claude-review (draft)", "label claude-review", "opened, no label", "ready_for_review, no label",
           "reopened with the label", "workflow_dispatch"}


class ClaudeReviewWorkflow(unittest.TestCase):
    def test_installed_copy_matches_the_canonical_one(self):
        self.assertEqual(INSTALLED.read_text(encoding="utf-8"), TEMPLATE)

    def test_translator_reads_both_expressions(self):
        self.assertIn("CLAUDE_REVIEW_ENABLED", JOB_IF)
        self.assertIn("FOUNDER_TIER_ENABLED", TIER_IF)
        self.assertIn("github.run_id", GROUP)
        self.assertIs(evaluate(JOB_IF, CASES["label claude-review"]), True)

    def test_which_events_review(self):
        for name, ctx in CASES.items():
            with self.subTest(name):
                self.assertEqual(bool(evaluate(JOB_IF, ctx)), name in REVIEWS)

    def test_only_a_reviewing_event_joins_the_prs_group(self):
        """The invariant: a run shares claude-review-<pr>-review exactly when its job reviews.
        A skipped event in that group would cancel the review in progress (PT-43)."""
        for name, ctx in CASES.items():
            with self.subTest(name):
                shared = group_of(ctx) == "claude-review-78-review"
                self.assertEqual(shared, name in REVIEWS, group_of(ctx))

    def test_two_labels_in_the_same_second_leave_the_review_running(self):
        review = group_of(CASES["label claude-review"])
        other = group_of(CASES["label build-bundles"])
        self.assertNotEqual(review, other)
        self.assertEqual(other, "claude-review-78-2")

    def test_a_newer_review_still_replaces_an_older_one(self):
        self.assertEqual(group_of(CASES["label claude-review"]), group_of(CASES["reopened with the label"]))
        self.assertIn("cancel-in-progress: true", TEMPLATE)

    def test_repo_gates_only_on_the_job(self):
        """Fork, Dependabot and the enable switch stop the job; they need no group of their own:
        those runs review nothing and the group keeps them apart only when they would review."""
        off = dict(CASES["label claude-review"], vars={"CLAUDE_REVIEW_ENABLED": "false"})
        self.assertFalse(evaluate(JOB_IF, off))
        self.assertFalse(evaluate(JOB_IF, event("labeled", ["claude-review"], "claude-review", same_repo=False)))
        self.assertFalse(evaluate(JOB_IF, event("opened", actor="dependabot[bot]")))

    def test_which_events_classify_the_founder_tier(self):
        for name, ctx in CASES.items():
            with self.subTest(name):
                self.assertEqual(bool(evaluate(TIER_IF, ctx)), name in TIERS)

    def test_founder_tier_is_independent_of_the_review_switch_and_has_its_own(self):
        ctx = CASES["target opened"]
        self.assertTrue(evaluate(TIER_IF, dict(ctx, vars={"CLAUDE_REVIEW_ENABLED": "false"})))
        self.assertTrue(evaluate(TIER_IF, dict(ctx, vars={})))
        self.assertFalse(evaluate(TIER_IF, dict(ctx, vars={"FOUNDER_TIER_ENABLED": "false"})))

    def test_pull_request_target_only_feeds_the_founder_tier_job(self):
        """pull_request_target runs the default branch's file with a write token: only the
        founder-tier job (no checkout) may run on it, never the review."""
        types = re.search(r"pull_request_target:\n\s+types: \[(.*?)\]", TEMPLATE).group(1)
        self.assertNotIn("labeled", types)
        for action in [t.strip() for t in types.split(",")]:
            with self.subTest(action):
                ctx = event(action, name="pull_request_target")
                self.assertFalse(evaluate(JOB_IF, ctx))
                self.assertTrue(evaluate(TIER_IF, ctx))


if __name__ == "__main__":
    unittest.main()
