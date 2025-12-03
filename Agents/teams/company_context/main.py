"""
Main entry point for Company Context Team workflow.
"""

import sys
from pathlib import Path

# Import orchestrator from new structure
_orchestrator_path = Path(__file__).parent / "orchestrator"
sys.path.insert(0, str(_orchestrator_path))
from orchestrator import OrchestratorAgent


def process_company_context(company_name: str, website_url: str, instagram_account: str) -> dict:
    """
    Process company context request.
    
    Args:
        company_name: Company name
        website_url: Website URL
        instagram_account: Instagram account (without @)
    
    Returns:
        JSON output with complete company profile
    """
    orchestrator = OrchestratorAgent()
    result = orchestrator.process(company_name, website_url, instagram_account)
    return result


if __name__ == "__main__":
    # Example usage
    result = process_company_context(
        company_name="Example Company",
        website_url="https://example.com",
        instagram_account="example"
    )
    
    import json
    print(json.dumps(result, indent=2))

