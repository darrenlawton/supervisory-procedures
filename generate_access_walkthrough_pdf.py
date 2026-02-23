"""Generate the Agent Skill Access Provisioning walkthrough PDF."""
from fpdf import FPDF
from fpdf.enums import XPos, YPos

OUTPUT = "/Users/darrenlawton/DevArea/IB_Skill_Access_Provisioning_Walkthrough.pdf"

_CHAR_MAP = {
    "\u2014": "-",
    "\u2013": "-",
    "\u2192": "->",
    "\u2190": "<-",
    "\u2193": "v",
    "\u2022": "*",
    "\u2019": "'",
    "\u2018": "'",
    "\u201c": '"',
    "\u201d": '"',
}

def _s(text: str) -> str:
    for src, dst in _CHAR_MAP.items():
        text = text.replace(src, dst)
    return text


SECTIONS = [
    {
        "is_cover": True,
        "title": "Provisioning Agent Access to a Skill",
        "subtitle": "A Step-by-Step Guide for Investment Banking Supervisors",
        "date": "23 February 2026",
        "bullets": [
            "How the three-layer access control system works",
            "Scenario A - Including an agent when the skill is first submitted",
            "Scenario B - Adding a new agent to an already-approved skill",
            "Scenario C - Revoking agent access",
            "Runtime behaviour and error handling",
            "Rules and what to avoid",
        ],
    },
    {
        "heading": "How the Three-Layer Access Control System Works",
        "body": (
            "Every time an agent calls registry.get_skill(), three checks run in sequence. "
            "All three must pass before the skill data is returned.\n\n"
            "Layer 1 - Status gate\n"
            "The skill's status field must be 'approved'. Draft and deprecated skills are "
            "always blocked regardless of which agents are listed. This gate cannot be "
            "bypassed. A skill must be merged to main and promoted to approved status "
            "by the hub team before any agent can use it.\n\n"
            "Layer 2 - Allowlist gate\n"
            "The requesting agent_id must appear in the skill's authorised_agents list. "
            "This is the layer you control as a supervisor. Adding or removing an agent "
            "means editing the authorised_agents field in the YAML and submitting a PR.\n\n"
            "Layer 3 - Schema validity gate\n"
            "Invalid skill files are excluded from the registry at load time. A skill that "
            "fails schema validation is silently skipped - it cannot be reached by any agent. "
            "This is enforced automatically when the registry loads."
        ),
    },
    {
        "heading": "Layer Flow Diagram",
        "body": (
            "Agent calls: registry.get_skill(\n"
            "    'investment_banking/retail-company-valuation',\n"
            "    agent_id='ib-valuation-agent-prod'\n"
            ")\n\n"
            "    |\n"
            "    v\n"
            "Layer 1 - Status gate\n"
            "  Is skill status == 'approved'?\n"
            "  NO  ->  SkillNotApprovedError  (blocked)\n"
            "  YES |\n"
            "      v\n"
            "Layer 2 - Allowlist gate\n"
            "  Is agent_id in authorised_agents?\n"
            "  NO  ->  AgentNotAuthorisedError  (blocked)\n"
            "  YES |\n"
            "      v\n"
            "Layer 3 - Schema validity gate\n"
            "  Did the skill pass schema validation at load time?\n"
            "  NO  ->  skill not in registry (unreachable)\n"
            "  YES |\n"
            "      v\n"
            "  Skill data returned to agent"
        ),
        "mono": True,
    },
    {
        "heading": "Scenario A - New Skill Not Yet Merged (Initial Setup)",
        "body": (
            "This is the situation when you are submitting a brand new skill for the first "
            "time. The agent ID must be included in the skill YAML before the PR is opened "
            "- not added afterwards.\n\n"
            "In the retail-company-valuation skill, this was done correctly at authoring:\n\n"
            "    metadata:\n"
            "      authorised_agents:\n"
            "        - ib-valuation-agent-prod\n\n"
            "Once the PR is reviewed and the hub team merges it to main, the skill status "
            "is set to 'approved' and ib-valuation-agent-prod has immediate access. No "
            "further change is needed.\n\n"
            "If you realise before merging that you need to add another agent, simply edit "
            "the YAML in the same PR and add the agent to the list. Each agent that will "
            "need to use the skill in any environment (production, staging, UAT) should be "
            "listed before the initial merge."
        ),
    },
    {
        "heading": "Scenario B - Adding a New Agent to an Approved Skill",
        "body": (
            "This is the most common ongoing task. For example, adding a staging agent "
            "'ib-valuation-agent-staging' to the already-live valuation skill.\n\n"
            "Step 1 - Check the current state of the skill\n"
            "    supv show investment_banking/retail-company-valuation\n\n"
            "This displays the current authorised agents, skill status, and version. "
            "Confirm status is 'approved' before proceeding.\n\n"
            "Step 2 - Create a branch\n"
            "    git checkout -b feat/ib-valuation-add-staging-agent\n\n"
            "Step 3 - Edit the YAML\n"
            "Open registry/investment_banking/retail-company-valuation.yml and make "
            "two changes:\n"
            "  (a) Add the new agent ID to authorised_agents\n"
            "  (b) Bump the version (adding an agent = MINOR bump: 1.0.0 -> 1.1.0)\n\n"
            "    metadata:\n"
            "      version: 1.1.0\n"
            "      authorised_agents:\n"
            "        - ib-valuation-agent-prod\n"
            "        - ib-valuation-agent-staging   # new\n\n"
            "Step 4 - Validate locally\n"
            "    supv validate registry/investment_banking/retail-company-valuation.yml\n\n"
            "Expected: checkmark   registry/.../retail-company-valuation.yml -- valid\n\n"
            "Step 5 - Commit and push\n"
            "    git add registry/investment_banking/retail-company-valuation.yml\n"
            "    git commit -m 'feat(registry): add staging agent to IB retail valuation'\n"
            "    git push origin feat/ib-valuation-add-staging-agent\n\n"
            "Step 6 - Open a PR\n"
            "Use the standard PR template (Change type: Update). For an agent addition, "
            "the minimum checklist items are:\n"
            "  [ ] Skill validated locally\n"
            "  [ ] Authorised agents are named explicitly (not '*')\n"
            "  [ ] Supervisor email is current and monitored\n\n"
            "Compliance sign-off is generally not required for adding an agent to an "
            "already-approved skill unless it introduces a new environment or agent type. "
            "Check with your governance team if uncertain.\n\n"
            "Step 7 - Review gates\n"
            "CI validates the YAML -> IB CODEOWNER approves -> Hub team merges to main.\n"
            "The moment it merges, ib-valuation-agent-staging can load the skill. "
            "No restart or cache flush is required."
        ),
    },
    {
        "heading": "Scenario C - Revoking Access from an Agent",
        "body": (
            "Revoking access is the reverse of adding it. Remove the agent ID from "
            "authorised_agents, bump the version, and submit a PR.\n\n"
            "Example: removing ib-valuation-agent-staging after it is decommissioned.\n\n"
            "    metadata:\n"
            "      version: 1.2.0          # bumped\n"
            "      authorised_agents:\n"
            "        - ib-valuation-agent-prod\n"
            "        # ib-valuation-agent-staging removed\n\n"
            "Once merged, the next get_skill() call from ib-valuation-agent-staging will "
            "raise AgentNotAuthorisedError immediately. The change takes effect at the "
            "next registry load - no delay and no grace period.\n\n"
            "Important: do not simply comment out the agent ID - remove the line "
            "entirely. Commented-out entries in YAML are ignored by the parser but "
            "can cause confusion in future reviews."
        ),
        "mono_snippet": True,
    },
    {
        "heading": "Runtime Behaviour and Error Handling",
        "body": (
            "Developers building agents must handle the three typed exceptions that the "
            "access control system raises. The registry never silently swallows an "
            "access failure.\n\n"
            "from supervisory_procedures.core.registry import SkillRegistry\n"
            "from supervisory_procedures.core.access_control import (\n"
            "    AgentNotAuthorisedError,\n"
            "    SkillNotApprovedError,\n"
            "    SkillNotFoundError,\n"
            ")\n\n"
            "registry = SkillRegistry()\n\n"
            "try:\n"
            "    skill = registry.get_skill(\n"
            "        'investment_banking/retail-company-valuation',\n"
            "        agent_id='ib-valuation-agent-prod',\n"
            "    )\n"
            "except SkillNotFoundError:\n"
            "    # Skill ID does not exist in registry\n"
            "    ...\n"
            "except SkillNotApprovedError as exc:\n"
            "    # Layer 1 blocked - skill is draft or deprecated\n"
            "    # exc.status is 'draft' or 'deprecated'\n"
            "    ...\n"
            "except AgentNotAuthorisedError as exc:\n"
            "    # Layer 2 blocked - agent not on the allowlist\n"
            "    # exc.agent_id and exc.skill_id are available for logging\n"
            "    ..."
        ),
        "mono": True,
    },
    {
        "heading": "Rules and What to Avoid",
        "body": (
            "Always name agents explicitly\n"
            "Use the agent's full environment-qualified ID, e.g. ib-valuation-agent-prod "
            "or ib-valuation-agent-staging. This makes it clear exactly which deployments "
            "are authorised and simplifies future audits.\n\n"
            "Never use the wildcard in production\n"
            "The authorised_agents field accepts ['*'] which allows any agent to load the "
            "skill. This is flagged as a warning by the wizard and the CI pipeline. For a "
            "risk_classification: high skill such as the valuation model, the hub team "
            "will reject a PR that uses a wildcard. It is only acceptable in isolated "
            "test or sandbox environments.\n\n"
            "Always bump the version on every access change\n"
            "Adding or removing an agent is a MINOR version bump (1.0.0 -> 1.1.0). This "
            "ensures the audit history in git clearly reflects every change to who can "
            "access the skill and when.\n\n"
            "Draft skills are always blocked\n"
            "Even if an agent is listed in authorised_agents, it cannot load the skill "
            "while status is 'draft'. The status gate (Layer 1) runs first and cannot be "
            "bypassed. The skill must be merged and approved before access takes effect.\n\n"
            "Access changes go through the same PR process as skill authoring\n"
            "There is no admin panel or direct edit mechanism. Every change to "
            "authorised_agents must be made via a PR, pass CI validation, receive "
            "CODEOWNER approval, and be merged by the hub team. This ensures there is "
            "a full audit trail for every access grant and revocation."
        ),
    },
    {
        "heading": "Quick Reference",
        "body": (
            "Task                                    Command\n"
            "-----------------------------------------------------------------------\n"
            "Check who has access to a skill         supv show <skill_id>\n"
            "List all IB skills and their status     supv list -b investment_banking\n"
            "List only approved skills               supv list -s approved\n"
            "Validate after editing                  supv validate registry/<path>.yml\n"
            "Validate entire registry                supv validate registry/ --strict\n\n"
            "Version bump convention\n"
            "-----------------------------------------------------------------------\n"
            "Adding an agent         MINOR bump   1.0.0 -> 1.1.0\n"
            "Removing an agent       MINOR bump   1.1.0 -> 1.2.0\n"
            "Editing skill content   MINOR bump   1.0.0 -> 1.1.0\n"
            "Breaking change         MAJOR bump   1.x.x -> 2.0.0\n"
            "Patch / typo fix        PATCH bump   1.0.0 -> 1.0.1"
        ),
        "mono": True,
    },
]


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

class AccessPDF(FPDF):

    BRAND_BLUE  = (15, 52, 96)
    BRAND_LIGHT = (220, 230, 242)
    TEXT_DARK   = (30, 30, 30)
    MONO_BG     = (245, 246, 248)
    RULE_GREY   = (180, 190, 200)

    # ------------------------------------------------------------------
    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*self.BRAND_BLUE)
        self.rect(0, 0, 210, 12, style="F")
        self.set_y(2)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, "Agent Skill Access Provisioning Guide - Investment Banking Division", align="L")
        self.ln(10)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-12)
        self.set_draw_color(*self.RULE_GREY)
        self.line(14, self.get_y(), 196, self.get_y())
        self.set_font("Helvetica", "", 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, f"Page {self.page_no()}  |  INTERNAL - Investment Banking Division", align="C")

    # ------------------------------------------------------------------
    def cover(self, title, subtitle, date, bullets):
        self.add_page()

        # Navy banner
        self.set_fill_color(*self.BRAND_BLUE)
        self.rect(0, 0, 210, 60, style="F")
        self.set_y(12)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(180, 205, 235)
        self.cell(0, 8, "INVESTMENT BANKING DIVISION", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "B", 19)
        self.set_text_color(255, 255, 255)
        self.set_x(14)
        self.multi_cell(182, 10, _s(title), align="C")
        self.set_font("Helvetica", "", 11)
        self.set_text_color(180, 205, 235)
        self.set_x(14)
        self.multi_cell(182, 7, _s(subtitle), align="C")

        # Light band
        self.set_y(62)
        self.set_fill_color(*self.BRAND_LIGHT)
        self.rect(0, 62, 210, 18, style="F")
        self.set_y(67)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.BRAND_BLUE)
        self.cell(0, 8, f"Date: {date}    |    Status: Draft    |    Classification: Internal",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Summary box
        self.set_y(90)
        self.set_x(20)
        self.set_fill_color(*self.BRAND_LIGHT)
        self.set_draw_color(*self.BRAND_BLUE)
        self.set_line_width(0.4)
        self.rect(20, 90, 170, 72, style="FD")
        self.set_y(97)
        self.set_x(28)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.BRAND_BLUE)
        self.cell(0, 7, "What this document covers", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.TEXT_DARK)
        for item in bullets:
            self.set_x(28)
            self.cell(5, 6, "-", new_x=XPos.RIGHT)
            self.multi_cell(152, 6, _s(item))

        # Footer note
        self.set_y(270)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, "INTERNAL - Investment Banking Division  |  Do not distribute externally", align="C")

    # ------------------------------------------------------------------
    def section(self, heading, body, mono=False):
        if self.get_y() > 245:
            self.add_page()

        self.set_x(14)
        self.set_fill_color(*self.BRAND_BLUE)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(182, 8, _s(f"  {heading}"), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

        self.set_x(14)
        if mono:
            self.set_font("Courier", "", 7.5)
            self.set_text_color(*self.TEXT_DARK)
            self.set_fill_color(*self.MONO_BG)
            self.set_draw_color(*self.RULE_GREY)
            self.set_line_width(0.2)
            self.multi_cell(182, 4.5, _s(body), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*self.TEXT_DARK)
            self.multi_cell(182, 5, _s(body), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(5)

    # ------------------------------------------------------------------
    def add_page(self, *args, **kwargs):
        super().add_page(*args, **kwargs)
        if self.page_no() > 1:
            self.set_y(16)

    # ------------------------------------------------------------------
    def build(self, sections):
        for s in sections:
            if s.get("is_cover"):
                self.cover(s["title"], s["subtitle"], s["date"], s["bullets"])
                continue
            self.section(s["heading"], s["body"], mono=s.get("mono", False))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

pdf = AccessPDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=16)
pdf.set_margins(14, 14, 14)
pdf.build(SECTIONS)
pdf.output(OUTPUT)

print(f"PDF written to {OUTPUT}")
