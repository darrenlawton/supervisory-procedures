"""Generate the IB Valuation Skill walkthrough PDF."""
from fpdf import FPDF
from fpdf.enums import XPos, YPos

OUTPUT = "/Users/darrenlawton/DevArea/IB_Valuation_Skill_Walkthrough.pdf"

# Normalise characters that are outside latin-1 (fpdf core font range)
_CHAR_MAP = {
    "\u2014": "-",   # em dash
    "\u2013": "-",   # en dash
    "\u2192": "->",  # right arrow
    "\u2190": "<-",  # left arrow
    "\u2193": "v",   # down arrow
    "\u2022": "*",   # bullet
    "\u2019": "'",   # right single quote
    "\u2018": "'",   # left single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
}

def _s(text: str) -> str:
    """Sanitise a string to latin-1 safe characters."""
    for src, dst in _CHAR_MAP.items():
        text = text.replace(src, dst)
    return text

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

SECTIONS = [
    {
        "heading": None,
        "title": "Creating an Agent Skill: Retail Company Valuation Model",
        "subtitle": "A Step-by-Step Guide for Investment Banking Supervisors",
        "date": "23 February 2026",
        "is_cover": True,
    },
    {
        "heading": "Overview",
        "body": (
            "This guide walks an Investment Banking Division supervisor through the process "
            "of authoring, validating, and submitting an Agent Skill for a retail company "
            "valuation model into the firm's Agent Skill Registry.\n\n"
            "The registry follows a hub-and-spoke governance model. Business area supervisors "
            "(spokes) author skills for their own domain; the central innovation hub team "
            "owns the schema, tooling, and CI pipeline, and performs the final merge to main.\n\n"
            "Because 'investment_banking' is a new business area, the process has two phases:\n"
            "  Phase 1 - Register the Investment Banking business area\n"
            "  Phase 2 - Author, validate, and submit the skill"
        ),
    },
    {
        "heading": "Phase 1 - Register the Investment Banking Business Area",
        "body": (
            "This is a one-time setup step required before any skills can be submitted "
            "for the investment_banking area.\n\n"
            "Step 1.1 - Contact the central innovation hub team\n"
            "Notify the hub team that Investment Banking is onboarding as a new spoke. "
            "They will create a CODEOWNERS entry:\n"
            "    /registry/investment_banking/   @org/investment-banking-supervisors\n\n"
            "Step 1.2 - Create the business area directory\n"
            "Create registry/investment_banking/README.md listing your team as owners, "
            "then open a pull request. The hub team reviews and merges it. Once merged, "
            "your team can begin authoring skills."
        ),
    },
    {
        "heading": "Phase 2 - Authoring the Skill",
        "body": (
            "Option A - Use the wizard (recommended for first-timers)\n"
            "Run 'supv new' in a terminal. The wizard asks plain-English questions and "
            "writes the YAML file for you. No knowledge of YAML syntax is required.\n\n"
            "Option B - Write the YAML directly\n"
            "Create the file at:\n"
            "    registry/investment_banking/retail-company-valuation.yml\n\n"
            "A skill definition has seven sections:\n"
            "  metadata              - ownership, version, authorised agents, status\n"
            "  context               - business description, rationale, regulations, risk level\n"
            "  scope                 - exhaustive approved activities allowlist\n"
            "  constraints           - procedural requirements and absolute prohibitions\n"
            "  hard_veto_triggers    - conditions that cause the agent to immediately halt\n"
            "  oversight_checkpoints - human review and approval gates\n"
            "  workflow              - ordered steps the agent executes"
        ),
    },
    {
        "heading": "Key Authoring Principles",
        "body": (
            "1. The approved_activities list is an exhaustive allowlist\n"
            "Anything not listed is forbidden. Be specific - 'Calculate EV/EBITDA, P/E, "
            "EV/Sales, and EV/EBIT multiples for comparable companies' is correct; "
            "'Process financial data' is too vague.\n\n"
            "2. Define hard veto triggers for your highest risks\n"
            "Every skill must have at least one. For IBD valuation, the critical triggers are:\n"
            "  inside-information-detected - MNPI in a data source\n"
            "  target-on-restricted-list   - active deal or conflict of interest\n"
            "  data-source-not-approved    - unauthorised data vendor\n\n"
            "3. Name authorised agents explicitly\n"
            "Use the agent's full ID (e.g. 'ib-valuation-agent-prod'). "
            "Do not use '*' except in controlled test environments.\n\n"
            "4. Status starts as draft\n"
            "Set status: draft when authoring. The hub team promotes it to 'approved' "
            "after the pull request is reviewed and merged. A draft skill cannot be "
            "loaded by any agent.\n\n"
            "5. High risk requires compliance sign-off\n"
            "This skill is classified risk_classification: high. Compliance team "
            "sign-off must be attached to the pull request before it can be approved."
        ),
    },
    {
        "heading": "Skill Metadata Block",
        "body": (
            "id:               investment_banking/retail-company-valuation\n"
            "name:             Retail Company Valuation Model\n"
            "version:          1.0.0\n"
            "schema_version:   '1.1'\n"
            "business_area:    investment_banking\n"
            "supervisor.name:  Your Full Name\n"
            "supervisor.email: your.name@bank.example.com\n"
            "supervisor.role:  Head of Investment Banking Coverage - Retail\n"
            "status:           draft\n"
            "created_at:       2026-02-23\n"
            "approved_at:      null  (set by hub on merge)\n"
            "approved_by:      null  (set by hub on merge)\n"
            "authorised_agents:\n"
            "  - ib-valuation-agent-prod"
        ),
        "mono": True,
    },
    {
        "heading": "Approved Activities (Scope Allowlist)",
        "body": (
            "The following activities are the complete allowlist for this skill. "
            "The agent may not perform any action not on this list.\n\n"
            "1.  Check the target company against the firm's restricted and watch lists\n"
            "    prior to any data retrieval\n"
            "2.  Retrieve public financial filings (10-K, 20-F, annual reports) for\n"
            "    target and comparable companies\n"
            "3.  Pull approved market data feeds for share price, EV, and trading multiples\n"
            "4.  Calculate EV/EBITDA, P/E, EV/Sales, and EV/EBIT multiples for\n"
            "    comparable companies\n"
            "5.  Build DCF model inputs using normalised historical financials and\n"
            "    published consensus forecasts\n"
            "6.  Construct LBO model skeleton with standard leverage assumptions\n"
            "7.  Flag data gaps or anomalies in source financials for analyst follow-up\n"
            "8.  Generate a structured valuation summary report for senior banker review\n"
            "9.  Package and deliver the approved valuation model to authorised recipients\n"
            "10. Log all data sources, versions, and assumptions to the audit trail"
        ),
    },
    {
        "heading": "Hard Veto Triggers",
        "body": (
            "inside-information-detected\n"
            "  Condition: A data source is flagged as containing MNPI about the target.\n"
            "  Action:    halt_and_escalate\n"
            "  Contact:   compliance-mnpi-desk@bank.example.com\n\n"
            "target-on-restricted-list\n"
            "  Condition: Target company appears on the firm's restricted or watch list.\n"
            "  Action:    halt_and_escalate\n"
            "  Contact:   conflicts-office@bank.example.com\n\n"
            "data-source-not-approved\n"
            "  Condition: Agent attempts to retrieve data from an unapproved vendor.\n"
            "  Action:    halt_and_notify\n"
            "  Contact:   ib-data-governance@bank.example.com"
        ),
    },
    {
        "heading": "Oversight Checkpoints",
        "body": (
            "Required workflow checkpoints (always triggered):\n\n"
            "restricted-list-cleared\n"
            "  Type:       approve\n"
            "  Reviewer:   Compliance - Conflicts Office\n"
            "  SLA:        2 hours\n"
            "  Gate:       Must pass before any data retrieval begins\n\n"
            "valuation-senior-review\n"
            "  Type:       approve\n"
            "  Reviewer:   VP or MD - Investment Banking Coverage\n"
            "  SLA:        24 hours\n"
            "  Gate:       Must pass before external distribution\n\n"
            "external-sharing-approval\n"
            "  Type:       approve\n"
            "  Reviewer:   Coverage Managing Director\n"
            "  SLA:        4 hours\n"
            "  Gate:       Must pass before model is delivered to recipients\n\n"
            "Condition-triggered checkpoints:\n\n"
            "data-anomaly-flagged\n"
            "  Trigger:    Material inconsistency or anomaly in source financials\n"
            "  Type:       review  |  Reviewer: Analyst or Associate\n\n"
            "private-company-target\n"
            "  Trigger:    Target company is not publicly listed\n"
            "  Type:       approve  |  Reviewer: Legal Counsel + Compliance\n"
            "  SLA:        48 hours"
        ),
    },
    {
        "heading": "Workflow — Ordered Execution Steps",
        "body": (
            "Step                       Activity                              Control\n"
            "-------------------------------------------------------------------------\n"
            "restricted-list-check      Check restricted/watch lists          Veto + Checkpoint\n"
            "log-list-check             Audit log\n"
            "retrieve-public-filings    Retrieve 10-K/20-F filings            Veto\n"
            "log-filings-retrieved      Audit log\n"
            "pull-market-data           Pull market data feeds                Veto\n"
            "log-market-data-retrieved  Audit log\n"
            "calculate-trading-multiples Calculate comps multiples\n"
            "log-multiples-calculated   Audit log\n"
            "build-dcf-inputs           Build DCF inputs                      Veto\n"
            "log-dcf-built              Audit log\n"
            "construct-lbo-skeleton     Construct LBO skeleton\n"
            "log-lbo-constructed        Audit log\n"
            "flag-data-anomalies        Flag anomalies\n"
            "generate-valuation-report  Generate summary report               Checkpoint\n"
            "log-report-generated       Audit log\n"
            "deliver-model              Deliver to recipients                 Checkpoint\n"
            "log-delivery               Audit log\n\n"
            "Veto triggers fire immediately if their condition is met — halting the agent.\n"
            "Checkpoints pause execution until a human approves before the next step runs."
        ),
        "mono": True,
    },
    {
        "heading": "Phase 3 — Validate and Submit",
        "body": (
            "Step 3.1 — Validate locally\n"
            "    supv validate registry/investment_banking/retail-company-valuation.yml\n\n"
            "Fix any reported errors before proceeding.\n\n"
            "Step 3.2 — Create a branch and commit\n"
            "    git checkout -b feat/ib-retail-valuation-skill\n"
            "    git add registry/investment_banking/retail-company-valuation.yml\n"
            "    git commit -m 'feat(registry): add Retail Company Valuation skill for IB'\n"
            "    git push origin feat/ib-retail-valuation-skill\n\n"
            "Step 3.3 — Open a pull request\n"
            "Use the PR template at .github/pull_request_template.md and complete "
            "the Supervisor Sign-off Checklist.\n\n"
            "Step 3.4 — Review gates\n"
            "    CI runs: supv validate registry/ --strict  (blocks on failure)\n"
            "         ↓\n"
            "    IB spoke CODEOWNER reviews content  (business sign-off)\n"
            "         ↓\n"
            "    Hub team reviews structure  (schema compliance)\n"
            "         ↓\n"
            "    Hub team merges to main  (skill goes live)"
        ),
    },
    {
        "heading": "PR Checklist — Supervisor Sign-off",
        "body": (
            "Complete all items before opening the pull request:\n\n"
            "  [ ] Read the Authoring Guide (docs/authoring-guide.md)\n"
            "  [ ] Skill validated locally: supv validate registry/<path>.yml\n"
            "  [ ] All approved activities are explicitly listed — the list is exhaustive\n"
            "  [ ] At least one hard veto trigger is defined\n"
            "  [ ] Authorised agents are named explicitly (not '*')\n"
            "  [ ] Supervisor email is current and monitored\n"
            "  [ ] Applicable regulations reviewed with the compliance team\n"
            "  [ ] Risk classification reflects actual risk\n"
            "      (risk_classification: high requires compliance sign-off attachment)\n"
            "  [ ] Compliance team sign-off attached\n"
            "  [ ] Data processing implications reviewed with DPO\n"
            "      (personal data is not involved in this skill)\n\n"
            "Once merged to main, the hub team sets approved_at and approved_by, "
            "status changes from 'draft' to 'approved', and ib-valuation-agent-prod "
            "can load and execute the skill."
        ),
    },
]

# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

class WalkthroughPDF(FPDF):

    BRAND_BLUE = (15, 52, 96)
    BRAND_LIGHT = (220, 230, 242)
    TEXT_DARK = (30, 30, 30)
    MONO_BG = (245, 246, 248)
    RULE_GREY = (180, 190, 200)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*self.BRAND_BLUE)
        self.rect(0, 0, 210, 12, style="F")
        self.set_y(2)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, _s("Agent Skill Authoring Guide - IB Retail Company Valuation"), align="L")
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

    def cover(self, title, subtitle, date):
        self.add_page()
        # Navy banner top
        self.set_fill_color(*self.BRAND_BLUE)
        self.rect(0, 0, 210, 60, style="F")
        self.set_y(14)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(180, 205, 235)
        self.cell(0, 8, "INVESTMENT BANKING DIVISION", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "B", 20)
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
        self.cell(0, 8, f"Date: {date}    |    Status: Draft    |    Classification: Internal", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Summary box
        self.set_y(90)
        self.set_x(20)
        self.set_fill_color(*self.BRAND_LIGHT)
        self.set_draw_color(*self.BRAND_BLUE)
        self.set_line_width(0.4)
        self.rect(20, 90, 170, 68, style="FD")
        self.set_y(97)
        self.set_x(28)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.BRAND_BLUE)
        self.cell(0, 7, "What this document covers", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.TEXT_DARK)
        items = [
            "Phase 1 - Registering Investment Banking as a new business area",
            "Phase 2 - Authoring the retail company valuation skill (YAML)",
            "Approved activities, hard veto triggers, and oversight checkpoints",
            "Workflow: ordered execution steps with control gates",
            "Phase 3 - Local validation, branch, PR, and review gates",
            "Supervisor sign-off checklist",
        ]
        for item in items:
            self.set_x(28)
            self.cell(4, 6, "-", new_x=XPos.RIGHT)
            self.multi_cell(152, 6, _s(item))

        # Footer note
        self.set_y(270)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, "INTERNAL - Investment Banking Division  |  Do not distribute externally", align="C")

    def section(self, heading, body, mono=False):
        self.set_x(14)
        # Heading bar
        self.set_fill_color(*self.BRAND_BLUE)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(182, 8, _s(f"  {heading}"), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

        # Body
        self.set_x(14)
        if mono:
            self.set_fill_color(*self.MONO_BG)
            self.set_draw_color(*self.RULE_GREY)
            self.set_line_width(0.2)
            self.set_font("Courier", "", 7.5)
            self.set_text_color(*self.TEXT_DARK)
            self.set_x(14)
            self.multi_cell(182, 4.5, _s(body), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*self.TEXT_DARK)
            self.set_x(14)
            self.multi_cell(182, 5, _s(body), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(5)

    def build(self, sections):
        for s in sections:
            if s.get("is_cover"):
                self.cover(s["title"], s["subtitle"], s["date"])
                continue
            # Estimate if heading + first ~3 lines fit; if not, new page
            if self.get_y() > 240:
                self.add_page()
            elif self.page_no() > 1 and self.get_y() < 20:
                pass  # just after header, fine
            self.section(s["heading"], s["body"], mono=s.get("mono", False))

    def add_page(self, *args, **kwargs):
        super().add_page(*args, **kwargs)
        if self.page_no() > 1:
            self.set_y(16)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

pdf = WalkthroughPDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=16)
pdf.set_margins(14, 14, 14)
pdf.add_page()  # triggers cover via build() instead
pdf.set_y(16)

# Build skips the first add_page call because cover() calls it internally
p = WalkthroughPDF(orientation="P", unit="mm", format="A4")
p.set_auto_page_break(auto=True, margin=16)
p.set_margins(14, 14, 14)
p.build(SECTIONS)
p.output(OUTPUT)

print(f"PDF written to {OUTPUT}")
