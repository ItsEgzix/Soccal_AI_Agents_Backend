# Migration Guide: Old to New Structure

## Overview

The test framework has been refactored from a monolithic structure to a modular, beginner-friendly architecture.

## What Changed

### Before (Monolithic)

- `agent_tester.py`: 932 lines, everything in one file
- `test_api.py`: Mixed concerns (routes, handlers, database)
- Hard to understand, test, or extend

### After (Modular)

- **Config layer**: Centralized configuration
- **Database layer**: Clean abstractions
- **Services layer**: Business logic
- **Testers layer**: Agent-specific testing
- **API layer**: Separated routes and handlers

## Migration Steps

### For Existing Code

The old `agent_tester.py` is still present for backward compatibility. To migrate:

1. **Update imports**:

   ```python
   # Old
   from test.agent_tester import AgentTester

   # New
   from test.testers.factory import TesterFactory
   factory = TesterFactory()
   tester = factory.create("Company_Context_Agent")
   ```

2. **Use new structure**:

   ```python
   # Old way (still works)
   tester = AgentTester()
   result = tester.test_company_context_agent_with_prompt_ids(...)

   # New way (recommended)
   factory = TesterFactory()
   tester = factory.create("Company_Context_Agent")
   result = tester.test(prompt_ids, use_draft, test_variables)
   ```

### For New Code

Always use the new modular structure:

```python
from test.testers.factory import TesterFactory
from test.config import DatabaseConfig

# Setup
factory = TesterFactory()

# Test
tester = factory.create("Company_Context_Agent")
result = tester.test(
    prompt_ids=['uuid1', 'uuid2'],
    use_draft=False,
    test_variables={'website_url': 'https://example.com'}
)
```

## Benefits

1. **Easier to understand**: Each module has a single purpose
2. **Easier to test**: Components can be tested independently
3. **Easier to extend**: Add new testers without modifying existing code
4. **Better for beginners**: Clear structure and documentation

## Backward Compatibility

The old `AgentTester` class is still available, but new code should use the modular structure.

## Next Steps

1. Gradually migrate existing code to use new structure
2. Remove old `agent_tester.py` once migration is complete
3. Update any external code that depends on old structure
