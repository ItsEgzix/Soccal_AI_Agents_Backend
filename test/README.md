# Agent Test Framework

A modular, beginner-friendly testing framework for AI agents.

## 📁 Structure

```
test/
├── config/          # Configuration management
│   ├── settings.py  # Database and test configuration
│   └── paths.py     # Path management utilities
├── database/        # Database layer
│   ├── connection.py              # Connection management
│   ├── prompt_repository.py       # Prompt fetching
│   └── test_result_repository.py  # Test result storage
├── services/        # Business logic services
│   ├── scraper_service.py  # Website/Instagram scraping
│   └── prompt_service.py   # Prompt loading/overriding
├── testers/         # Agent testers
│   ├── base_tester.py           # Abstract base class
│   ├── company_context_tester.py
│   ├── brand_voice_tester.py
│   ├── full_workflow_tester.py
│   └── factory.py   # Tester factory
├── api/             # API layer
│   ├── models.py    # Pydantic models
│   ├── handlers.py  # Request handlers
│   └── routes.py    # FastAPI routes
└── utils/           # Utilities
    ├── logger.py    # Logging utilities
    └── exceptions.py # Custom exceptions
```

## 🚀 Quick Start

### 1. Setup

```bash
# Install dependencies
pip install fastapi uvicorn psycopg2-binary python-dotenv

# Set environment variables in .env
DATABASE_URL=postgresql://user:password@host:port/dbname
# OR
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=5432
DB_NAME=your_db
```

### 2. Run the API

```bash
# From AI_Backend directory
python -m test.test_api
```

Or using uvicorn:

```bash
uvicorn test.test_api:app --host 0.0.0.0 --port 8000
```

## 📖 Architecture

### Configuration Layer (`config/`)

**Purpose**: Centralized configuration management

- `settings.py`: Loads and validates environment variables
- `paths.py`: Manages all file paths (no scattered path manipulations)

**Example**:

```python
from test.config import DatabaseConfig, PathManager

# Load config
db_config = DatabaseConfig.from_env()

# Get paths
agents_dir = PathManager.get_agents_dir()
```

### Database Layer (`database/`)

**Purpose**: Clean database abstractions

- `connection.py`: Context manager for database connections
- `prompt_repository.py`: Fetch prompts by ID
- `test_result_repository.py`: Save test results

**Example**:

```python
from test.database import DatabaseConnection, PromptRepository
from test.config import DatabaseConfig

# Setup
db_config = DatabaseConfig.from_env()
db_conn = DatabaseConnection(db_config)
prompt_repo = PromptRepository(db_conn)

# Fetch prompts
prompts = prompt_repo.fetch_prompts_by_ids(['uuid1', 'uuid2'], use_draft=False)
```

### Services Layer (`services/`)

**Purpose**: Business logic services

- `scraper_service.py`: Website and Instagram scraping
- `prompt_service.py`: Prompt loading and overriding

**Example**:

```python
from test.services import ScraperService

scraper = ScraperService()
company_id = scraper.ensure_company_exists("https://example.com")
captions = scraper.scrape_instagram("username", limit=5)
```

### Testers Layer (`testers/`)

**Purpose**: Agent-specific testing logic

- `base_tester.py`: Abstract base class with common functionality
- Specific testers: `CompanyContextTester`, `BrandVoiceTester`, `FullWorkflowTester`
- `factory.py`: Creates testers with dependency injection

**Example**:

```python
from test.testers.factory import TesterFactory

factory = TesterFactory()
tester = factory.create("Company_Context_Agent")

result = tester.test(
    prompt_ids=['uuid1', 'uuid2'],
    use_draft=False,
    test_variables={'website_url': 'https://example.com'}
)
```

### API Layer (`api/`)

**Purpose**: HTTP API endpoints

- `models.py`: Pydantic request/response models
- `handlers.py`: Business logic for requests
- `routes.py`: FastAPI route definitions

## 🔧 Adding a New Agent Tester

1. **Create tester class** in `testers/`:

```python
from .base_tester import BaseAgentTester

class MyNewAgentTester(BaseAgentTester):
    def test(self, prompt_ids, use_draft, test_variables):
        # Your testing logic here
        pass
```

2. **Register in factory** (`testers/factory.py`):

```python
def create(self, agent_name: str):
    # ... existing code ...
    elif agent_name == "MyNewAgent":
        return MyNewAgentTester(*dependencies)
```

3. **Done!** The API will automatically support it.

## 🎯 Benefits

### For Beginners

- **Clear structure**: Each folder has a single purpose
- **Easy to find code**: Know exactly where to look
- **Simple examples**: Each module has clear examples
- **Type hints**: Better IDE support and documentation

### For Development

- **Modular**: Change one part without affecting others
- **Testable**: Each component can be tested independently
- **Extensible**: Add new features without modifying existing code
- **Maintainable**: Clear separation of concerns

## 📝 API Endpoints

### POST `/test-agent-compare`

Test an agent with both draft and published prompts.

**Request**:

```json
{
  "agentName": "Company_Context_Agent",
  "publishedPromptIds": ["uuid1", "uuid2"],
  "draftPromptIds": ["uuid3", "uuid4"],
  "testVariables": {
    "website_url": "https://example.com"
  },
  "adminId": "admin-uuid"
}
```

**Response**:

```json
{
  "testResultId": "result-uuid",
  "success": true,
  "agent": "Company_Context_Agent",
  "draftResult": { ... },
  "publishedResult": { ... },
  "executionTime": 12.5,
  "comparison": { ... }
}
```

### GET `/health`

Health check endpoint.

## 🔍 Troubleshooting

### Database Connection Issues

Check your `.env` file has either:

- `DATABASE_URL` (full connection string), OR
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`

### Import Errors

Make sure you're running from the `AI_Backend` directory:

```bash
cd AI_Backend
python -m test.test_api
```

### Agent Not Found

Check that the agent name matches exactly:

- `Company_Context_Agent`
- `Brand_Voice_Agent`
- `full_workflow`

## 📚 Further Reading

- See individual module docstrings for detailed documentation
- Check `testers/base_tester.py` for tester interface
- Review `api/handlers.py` for request handling logic
