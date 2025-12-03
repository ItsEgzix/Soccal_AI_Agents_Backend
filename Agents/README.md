# Agents Framework

Scalable, maintainable framework for AI agents, teams, and tools.

## 📁 Structure

```
Agents/
├── core/                    # Core infrastructure (never modify)
│   ├── base_agent.py       # Base class for ALL agents
│   ├── base_tool.py        # Base class for ALL tools
│   ├── base_team.py        # Base class for ALL teams
│   ├── path_manager.py      # Centralized path management
│   └── registry.py         # Auto-discovery system
│
├── teams/                   # All agent teams (add new teams here)
│   └── company_context/     # Example team
│       ├── agents/          # Team's agents
│       ├── tools/           # Team's tools
│       └── utils/           # Team-specific utilities
│
└── shared/                  # Shared across ALL teams
    ├── llms/               # LLM configuration
    └── models/             # Shared models
```

## 🚀 Quick Start

### Adding a New Agent

1. Navigate to your team: `teams/{team_name}/agents/`
2. Create folder: `{agent_name}/`
3. Create `agent.py`:

```python
from ...core.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def execute(self, **kwargs):
        # Your logic here
        return result
```

4. Done! Agent is automatically discovered by registry.

### Adding a New Team

1. Create folder: `teams/{team_name}/`
2. Add structure:
   ```
   {team_name}/
   ├── __init__.py
   ├── README.md
   ├── agents/
   ├── tools/
   └── utils/
   ```
3. Done! Team is automatically discovered.

### Adding a New Tool

1. Create folder: `teams/{team_name}/tools/{tool_name}/`
2. Create tool class (optionally inheriting from `BaseTool`)
3. Export in `__init__.py`
4. Done! Tool is available to all team agents.

## 📖 Core Concepts

### BaseAgent

All agents inherit from `BaseAgent` which provides:

- Consistent initialization
- Standardized logging
- Common LLM setup
- Token tracking

### PathManager

Centralized path management - no more scattered `sys.path.append()`!

```python
from core.path_manager import AgentPathManager

# Setup imports automatically
AgentPathManager.setup_imports("team_name", "agent_name")

# Get paths
team_path = AgentPathManager.get_team_path("team_name")
agent_path = AgentPathManager.get_agent_path("team_name", "agent_name")
```

### Registry

Auto-discovery system for agents, teams, and tools:

```python
from core.registry import AgentRegistry

# Discover all components
AgentRegistry.discover_all()

# Get an agent
agent_class = AgentRegistry.get_agent("team_name", "agent_name")

# List all agents
agents = AgentRegistry.list_agents()
```

## 🎯 Best Practices

1. **Always inherit from base classes**: `BaseAgent`, `BaseTool`, `BaseTeam`
2. **Use PathManager**: Never use `sys.path.append()` directly
3. **Document in README.md**: Each team/agent should have documentation
4. **Follow naming conventions**: snake_case for folders, PascalCase for classes
5. **Keep teams independent**: No cross-team dependencies
6. **Use shared utilities**: Put common code in `shared/`

## 🔧 Migration from Old Structure

The old structure (`Company Context Team/`) is still supported for backward compatibility. New code should use the new structure (`teams/company_context/`).

### Old Structure (deprecated)

```
Agents/
└── Company Context Team/
    ├── Company_Context_Agent/
    └── Brand_Voice_Agent/
```

### New Structure (current)

```
Agents/
└── teams/
    └── company_context/
        ├── agents/
        │   ├── company_context/
        │   └── brand_voice/
        └── tools/
```

## 📚 Examples

See `teams/company_context/` for complete examples of:

- Agent implementation
- Tool integration
- Team utilities
- Prompt loading

## 🤝 Contributing

When adding new components:

1. Follow the structure above
2. Inherit from appropriate base class
3. Use PathManager for paths
4. Document in README.md
5. Test with the test framework
