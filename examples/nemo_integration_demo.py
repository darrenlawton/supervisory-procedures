"""NeMo Guardrails integration demo.

Generates NeMo Guardrails artefacts from the loan application skill and
writes them to a local directory.

Run from the project root:
    pip install -e .
    python examples/nemo_integration_demo.py
"""

from pathlib import Path

from supervisory_procedures.adapters.nemo_guardrails import NeMoGuardrailsAdapter
from supervisory_procedures.core.registry import SkillRegistry


def main():
    registry = SkillRegistry()
    skill = registry.get_skill("retail_banking/loan-application-processing")

    adapter = NeMoGuardrailsAdapter()
    result = adapter.export(skill)

    out_dir = Path("examples/nemo_output")
    out_dir.mkdir(exist_ok=True)

    config_path = out_dir / "config.yml"
    rails_path = out_dir / "skill_rails.co"

    config_path.write_text(result["config_yml"])
    rails_path.write_text(result["skill_rails_co"])

    print(f"NeMo Guardrails artefacts written to {out_dir}/")
    print(f"  {config_path}  ({len(result['config_yml'])} bytes)")
    print(f"  {rails_path}  ({len(result['skill_rails_co'])} bytes)")
    print()
    print("Next steps:")
    print("  1. Copy these files into your NeMo Guardrails app config directory")
    print("  2. Fill in the # TODO sections in skill_rails.co with detection logic")
    print("  3. Load the config in your guardrails application")


if __name__ == "__main__":
    main()
