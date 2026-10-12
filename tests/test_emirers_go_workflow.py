"""The EmirErs /go reusable workflow (.github/workflows/emirers-go.yml): the rules its callers
rely on. Standard library only; the step body is read as text, so a refactor that drops one of
these guarantees fails here before any consumer picks it up."""
import json
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / ".github" / "workflows" / "emirers-go.yml").read_text(encoding="utf-8")
FIRE = TEMPLATE.split("  explain:", 1)[0]
EXPLAIN = "  explain:" + TEMPLATE.split("  explain:", 1)[1]
RUNS = [part.split("\n\n  explain:")[0] for part in TEMPLATE.split("run: |")[1:]]


def condition(job):
    return re.search(r"if: >-\n((?:\s{6}.*\n)+)", job).group(1)


class ReusableWorkflow(unittest.TestCase):
    def test_is_a_reusable_workflow_with_the_stub_contract(self):
        self.assertIn("on:\n  workflow_call:\n", TEMPLATE)
        for inp in ("routine_id:", "routine_opus_id:", "branch_prefix:", "founder:", "agent:"):
            self.assertIn(inp, TEMPLATE)
        self.assertIn("secrets:\n      fire_token:", TEMPLATE)
        self.assertIn("      fire_token_opus:\n        description:", TEMPLATE)
        for ref in ("${{ inputs.routine_id }}", "${{ inputs.branch_prefix }}", "${{ secrets.fire_token }}"):
            self.assertIn(ref, FIRE)

    def test_fire_runs_for_the_founders_go_on_any_open_issue(self):
        cond = condition(FIRE)
        for part in ("github.event.comment.user.login == inputs.founder", "!github.event.issue.pull_request",
                     "github.event.issue.state == 'open'", "startsWith(github.event.comment.body, '/go')"):
            self.assertIn(part, cond)
        self.assertNotIn("labels", cond)
        self.assertNotIn("assignees", cond)

    def test_a_go_where_it_cannot_act_is_explained(self):
        cond = condition(EXPLAIN)
        self.assertIn("github.event.comment.user.login == inputs.founder", cond)
        self.assertIn("(github.event.issue.pull_request || github.event.issue.state != 'open')", cond)
        self.assertIn("content=confused", EXPLAIN)

    def test_mode_choice(self):
        """An open PR from any agent branch wins; a waiting agent continues on its newest live branch
        (no merged or closed PR); otherwise new work on a fresh branch."""
        self.assertIn('case " $LABELS " in *" needs-decision "*|*" stuck "*) waiting=1 ;; esac', FIRE)
        self.assertIn('fresh="${BRANCH_PREFIX}${ISSUE}-go-$(date -u +%m%d%H%M)"', FIRE)
        self.assertIn("select(.head.ref | test($re))", FIRE)
        self.assertIn("state=closed&per_page=1", FIRE)
        order = [FIRE.index(x) for x in ('if [ -n "$open_branch" ]; then', 'elif [ -n "$waiting" ]; then',
                                         '            mode="task"')]
        self.assertEqual(order, sorted(order))
        self.assertIn('mode="continue"; branch=$open_branch; what="continuing on PR #$open_pr"', FIRE)
        self.assertIn('mode="continue"; branch=${live:-$fresh}', FIRE)
        self.assertIn('mode="task"; branch=$fresh', FIRE)
        self.assertIn("printf 'issue: %s\\nbranch: %s\\nmode: continue' \"$ISSUE\" \"$branch\"", FIRE)
        self.assertIn("printf 'issue: %s\\nbranch: %s' \"$ISSUE\" \"$branch\"", FIRE)

    def test_fresh_branch_passes_the_routine_branch_check(self):
        """The routine's TASK step 1 regex (emirers routines/dispatch-prompt.md) must accept a fresh branch."""
        check = r"^[a-z0-9][a-z0-9._-]*/([a-z0-9]+-)?123-[a-z0-9-]+$"
        for prefix in ("feature/pel-", "mertyertugrul/mer-", "feature/"):
            self.assertIsNotNone(re.match(check, f"{prefix}123-go-10101040"), prefix)

    def test_blockers_gate_only_new_work_and_fail_closed(self):
        gate = FIRE.index('if [ "$mode" = "task" ]; then')
        self.assertLess(FIRE.index('mode="task"; branch=$fresh'), gate)
        self.assertGreater(FIRE.index("dependencies/blocked_by"), gate)
        self.assertIn('if ! blockers=$(gh api "repos/$REPO/issues/$ISSUE/dependencies/blocked_by"', FIRE)
        self.assertNotIn('2>/dev/null || echo ""', FIRE)

    def test_assignment_only_after_an_accepted_fire(self):
        """A failed fire must never leave an agent-owned issue with nothing behind it."""
        self.assertGreater(FIRE.index('-f "assignees[]=$AGENT"'), FIRE.index("react rocket"))
        self.assertIn('-f "assignees[]=$AGENT" >/dev/null 2>&1 || true', FIRE)

    def test_nothing_after_a_fire_can_fail_the_step(self):
        """Once the routine accepted the fire, 🚀 comes first and the trap is off: a parse error must not
        drop the 🚀 (the dedupe key) or the marker (what watch adopts)."""
        after = FIRE.split('case "$code" in', 1)[1]
        self.assertLess(after.index("trap - ERR"), after.index("react rocket"))
        self.assertLess(after.index("react rocket"), after.index("session=$(jq"))

    def test_marker_shape_watch_adopts(self):
        line = re.search(r"say \"(<!-- emirers-go-run [^\"]*-->)", FIRE).group(1)
        self.assertEqual(line, "<!-- emirers-go-run branch=$branch mode=$mode session=$session routine=$fire_routine -->")

    def test_comment_text_never_reaches_a_command(self):
        """Untrusted text goes through env only; `${{ … }}` inside `run:` would be script injection."""
        self.assertEqual(len(RUNS), 2)
        for run in RUNS:
            self.assertNotIn("${{", run)
            self.assertNotIn("$BODY", run.split("first=", 1)[1].split("\n", 1)[1])
        self.assertEqual(TEMPLATE.count("BODY: ${{ github.event.comment.body }}"), 2)

    def test_only_a_go_that_fired_holds_the_next_one_back(self):
        """A /go that failed (😕) or was skipped (👀) never blocks a retry: only 🚀 ones, older ones,
        first line only."""
        self.assertIn("select((.reactions.rocket // 0) > 0)", RUNS[0])
        self.assertIn(".id < $me", RUNS[0])
        self.assertIn('split("\\n")[0]', RUNS[0])
        self.assertIn("react rocket", RUNS[0])

    def test_branch_key_starts_with_a_letter(self):
        """Issue 3 must not match another issue's `x/12-3-foo`."""
        m = re.search(r're="(.*)"', TEMPLATE).group(1).replace("${ISSUE}", "3")
        self.assertIsNone(re.match(m, "feature/12-3-foo"))
        for ok in ("feature/pel-3-x", "feature/3-x", "mertyertugrul/mer-3-a-b"):
            self.assertIsNotNone(re.match(m, ok), ok)
        self.assertIsNone(re.match(m, "feature/pel-33-x"))

    def test_failures_still_react_and_never_die_on_sigpipe(self):
        self.assertIn("set -Eeuo pipefail", RUNS[0])
        self.assertIn("trap 'react confused' ERR", RUNS[0])
        for run in RUNS:
            self.assertNotIn("head -n", run)

    def test_fire_serializes_per_issue_under_its_own_group(self):
        """Not the stub's group name: a called job in its caller's group would wait for the caller forever."""
        self.assertIn("    concurrency:\n      group: emirers-go-fire-${{ github.repository }}-${{ github.event.issue.number }}\n"
                      "      cancel-in-progress: false\n", FIRE)

    def test_least_privilege(self):
        self.assertIn("permissions:\n  contents: read\n  issues: write\n  pull-requests: read\n", TEMPLATE)
        self.assertEqual(TEMPLATE.count("secrets."), 2)


JQ = re.search(r"jq -rs '(\[add // \[\] \| \.\[\]\n\s+\| select\(\.user\.login == \"github-actions\[bot\]\"\).*?last // \"\")'", FIRE, re.S).group(1)
OPUS, SONNET = "trig_opus", "trig_sonnet"


def marked(*comments):
    """What the workflow's marker filter returns for (author, body) comments, oldest first."""
    data = json.dumps([{"user": {"login": who}, "body": body} for who, body in comments])
    out = subprocess.run(["jq", "-rs", JQ], input=data, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def marker(routine=None):
    extra = f" routine={routine}" if routine else ""
    return f"<!-- emirers-go-run branch=feature/x/1-a mode=continue session=s_1{extra} -->\n🚀 `/go` started an agent"


BOT = "github-actions[bot]"


class OpusRoutine(unittest.TestCase):
    """A continue run goes back to the routine the run started on; everything else stays on Sonnet."""

    def test_opus_only_for_a_continue_run_with_an_opus_routine_configured(self):
        gate = 'if [ "$mode" = "continue" ] && [ -n "$ROUTINE_OPUS" ]; then'
        self.assertIn(gate, FIRE)
        self.assertIn("fire_routine=$ROUTINE; fire_token=$FIRE_TOKEN\n", FIRE)
        self.assertIn("fire_routine=$ROUTINE_OPUS; fire_token=$FIRE_TOKEN_OPUS", FIRE)
        # Chosen before the fire, after the mode (and the task-only blocker gate) is known.
        self.assertGreater(FIRE.index(gate), FIRE.index('mode="task"; branch=$fresh'))
        self.assertLess(FIRE.index(gate), FIRE.index('case "$code" in'))
        self.assertIn("routines/$fire_routine/fire", FIRE)
        self.assertIn("Bearer $fire_token", FIRE)
        self.assertNotIn("routines/$ROUTINE/fire", FIRE)
        self.assertNotIn("Bearer $FIRE_TOKEN\"", FIRE)

    def test_without_an_opus_routine_the_opus_secret_is_never_read(self):
        self.assertIn("FIRE_TOKEN_OPUS: ${{ inputs.routine_opus_id != '' && secrets.fire_token_opus || '' }}", FIRE)
        self.assertIn("      routine_opus_id:\n", TEMPLATE)
        self.assertRegex(TEMPLATE, r"routine_opus_id:\n(?:        .*\n)*?        default: ''\n")

    def test_opus_without_its_token_refuses_instead_of_falling_back(self):
        block = FIRE.split('if [ "$marked" = "$ROUTINE_OPUS" ]; then', 1)[1].split("what=", 1)[0]
        self.assertIn('if [ -z "$FIRE_TOKEN_OPUS" ]; then', block)
        self.assertIn("react confused", block)
        self.assertIn("exit 1", block)

    def test_unreadable_comments_fire_nothing(self):
        self.assertIn("if ! marked=$(gh api --paginate", FIRE)
        after = FIRE.split("if ! marked=$(gh api --paginate", 1)[1]
        self.assertLess(after.index("react confused"), after.index("exit 1"))
        self.assertLess(after.index("exit 1"), after.index('case "$code" in') if 'case "$code" in' in after else len(after))

    def test_the_marker_is_trusted_from_the_actions_bot_only(self):
        self.assertIn('select(.user.login == "github-actions[bot]")', FIRE)

    def test_comment_text_never_reaches_the_comparison_unvetted(self):
        """The id is limited to a safe charset and only ever compared with the configured id."""
        self.assertIn("routine=(?<r>[A-Za-z0-9_-]+)", FIRE)
        self.assertNotIn("eval", FIRE)

    @unittest.skipUnless(shutil.which("jq"), "jq not installed")
    def test_marker_naming_opus_selects_opus(self):
        self.assertEqual(marked((BOT, marker(OPUS))), OPUS)

    @unittest.skipUnless(shutil.which("jq"), "jq not installed")
    def test_newest_marker_wins(self):
        self.assertEqual(marked((BOT, marker(OPUS)), (BOT, "🚀 other"), (BOT, marker(SONNET))), SONNET)
        self.assertEqual(marked((BOT, marker(SONNET)), (BOT, marker(OPUS))), OPUS)

    @unittest.skipUnless(shutil.which("jq"), "jq not installed")
    def test_marker_naming_sonnet_or_without_the_field_or_absent_is_not_opus(self):
        self.assertEqual(marked((BOT, marker(SONNET))), SONNET)
        self.assertEqual(marked((BOT, marker())), "")
        self.assertEqual(marked(), "")
        self.assertEqual(marked((BOT, "just a comment")), "")

    @unittest.skipUnless(shutil.which("jq"), "jq not installed")
    def test_a_person_cannot_steer_the_routine(self):
        for who in ("mertyertugrul", "luvita-agents", "github-actions", "copilot-pull-request-reviewer[bot]"):
            self.assertEqual(marked((who, marker(OPUS))), "", who)
        self.assertEqual(marked((BOT, marker(SONNET)), ("mertyertugrul", marker(OPUS))), SONNET)

    @unittest.skipUnless(shutil.which("jq"), "jq not installed")
    def test_only_the_first_line_of_a_comment_counts(self):
        self.assertEqual(marked((BOT, "quoted:\n" + marker(OPUS))), "")
        self.assertEqual(marked((BOT, "<!-- emirers-go-run -->\n routine=" + OPUS)), "")


if __name__ == "__main__":
    unittest.main()
