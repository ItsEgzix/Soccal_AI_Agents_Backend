# Migration Guide: Old to New Structure

This guide helps you migrate from the old structure to the new scalable structure.

## Overview

### Old Structure (Deprecated)

```
Agents/
└── Company Context Team/
    ├── Company_Context_Agent/
    │   ├── agent.py
    │   ├── prompts/
    │   └── tools/
    ├── Brand_Voice_Agent/
    │   ├── agent.py
    │   ├── prompts/
    │   └── tools/
    └── utils/
        └── prompt_loader.py
```

### New Structure (Current)

```
Agents/
├── core/                    # Core infrastructure
│   ├── base_agent.py
│   ├── base_tool.py
│   ├── path_manager.py
│   └── registry.py
│
├── teams/
│   └── company_context/
│       ├── agents/
│       │   ├── company_context/
│       │   └── brand_voice/
│       ├── tools/
│       │   ├── web_scraper/
│       │   └── instagram_scraper/
│       └── utils/
│           └── prompt_loader.py
│
└── shared/
    └── llms/
        └── config.py
```

## Key Changes

### 1. Path Management

**Old Way:**

```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools', 'web scraper'))
from scraper import CompanyScraper
```

**New Way:**

```python
from core.path_manager import AgentPathManager

# Setup imports automatically
AgentPathManager.setup_imports("company_context", "company_context")

# Import tools
from ...tools.web_scraper.scraper import CompanyScraper
```

### 2. Agent Base Class

**Old Way:**

```python
class CompanyContextAgent:
    def __init__(self, company_id: str, llm=None, ...):
        self.company_id = company_id
        self.llm = llm or LLMConfig.get_default_llm()
```

**New Way:**

```python
from core.base_agent import BaseAgent

class CompanyContextAgent(BaseAgent):
    def __init__(self, company_id: str, **kwargs):
        super().__init__(**kwargs)  # Handles LLM setup
        self.company_id = company_id

    def execute(self, **kwargs) -> Dict[str, Any]:
        # Main entry point
        return self.extract_company_profile()
```

### 3. Import Paths

**Old Way:**

```python
# Multiple sys.path.append() calls
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from prompt_loader import PromptLoader

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from llms.config import LLMConfig
```

**New Way:**

```python
# Single setup call
AgentPathManager.setup_imports("company_context", "company_context")

# Clean imports
from ...utils.prompt_loader import PromptLoader
# LLM config is handled by BaseAgent
```

## Migration Steps

### Step 1: Update Agent Imports

1. Import `BaseAgent` from `core.base_agent`
2. Inherit from `BaseAgent`
3. Call `super().__init__()` in `__init__`
4. Implement `execute()` method

### Step 2: Use PathManager

1. Replace all `sys.path.append()` with `AgentPathManager.setup_imports()`
2. Use relative imports where possible
3. Use `AgentPathManager` methods for path operations

### Step 3: Update Tool Imports

1. Tools can optionally inherit from `BaseTool`
2. Use `AgentPathManager` for paths
3. Keep tools in `teams/{team_name}/tools/`

### Step 4: Test

1. Test framework automatically supports both old and new structures
2. Agents are auto-discovered by registry
3. No changes needed to test code

## Backward Compatibility

The old structure is still supported for backward compatibility:

- Test framework checks both old and new paths
- Old imports still work
- Gradual migration is possible

## Benefits

1. **Scalability**: Easy to add new teams, agents, tools
2. **Maintainability**: Clear structure, consistent patterns
3. **Discoverability**: Auto-discovery via registry
4. **Type Safety**: Base classes provide consistent interfaces
5. **Documentation**: Clear structure makes code self-documenting

## Questions?

See `Agents/README.md` for more details and examples.
