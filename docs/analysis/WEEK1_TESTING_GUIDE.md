# Week 1: Testing Infrastructure Setup
## Quick Start Guide for Automated Testing

**Goal:** Establish testing foundation with CI/CD, fixtures, and first journey tests  
**Timeline:** 5 days  
**Target:** 30% code coverage, CI/CD operational

---

## Day 1: Setup & Fixtures

### Morning: Install Testing Tools

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx

# Update requirements.txt
echo "pytest>=8.4.2" >> requirements.txt
echo "pytest-asyncio>=1.2.0" >> requirements.txt
echo "pytest-cov>=4.1.0" >> requirements.txt
echo "pytest-mock>=3.12.0" >> requirements.txt
echo "httpx>=0.28.1" >> requirements.txt

# Commit
git add requirements.txt
git commit -m "Add testing dependencies"
```

### Afternoon: Create Test Fixtures

**Create:** `backend/tests/fixtures/__init__.py`
```python
"""Test fixtures for HomeView AI tests."""
```

**Create:** `backend/tests/fixtures/test_data.py`
```python
"""Shared test fixtures for customer journey tests."""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, Home, Room, User, HomeownerProfile, Conversation
from backend.database import get_async_db

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
async def test_user(db_session):
    """Create a test homeowner user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        user_type="homeowner",
        is_active=True
    )
    db_session.add(user)
    
    profile = HomeownerProfile(
        user_id=user.id,
        first_name="Test",
        last_name="User",
        preferences={"style": "modern", "budget_range": "medium"}
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_home(db_session, test_user):
    """Create a test home with kitchen."""
    home = Home(
        id=uuid4(),
        owner_id=test_user.id,
        address="123 Test St",
        home_type="single_family",
        square_footage=2000
    )
    db_session.add(home)
    
    kitchen = Room(
        id=uuid4(),
        home_id=home.id,
        name="Kitchen",
        room_type="kitchen",
        square_footage=200
    )
    db_session.add(kitchen)
    
    await db_session.commit()
    await db_session.refresh(home)
    return home

@pytest.fixture
async def test_conversation(db_session, test_user, test_home):
    """Create a test conversation."""
    conversation = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        home_id=test_home.id,
        persona="homeowner",
        scenario="diy_project_plan",
        is_active=True
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation
```

**Create:** `backend/tests/conftest.py`
```python
"""Pytest configuration and shared fixtures."""
import pytest
from backend.tests.fixtures.test_data import *

# Make fixtures available to all tests
pytest_plugins = ["backend.tests.fixtures.test_data"]
```

---

## Day 2: First Journey Test

### Morning: Create Test Structure

**Create:** `backend/tests/journeys/__init__.py`
```python
"""Customer journey end-to-end tests."""
```

**Create:** `backend/tests/journeys/test_kitchen_renovation.py`
```python
"""
End-to-end test for Journey 1: Homeowner Complete Kitchen Renovation.

This test validates the complete flow:
1. Initial idea exploration
2. Provide requirements (budget, style)
3. Request visual designs
4. Product search and pricing
5. DIY vs contractor decision
6. Contractor search
7. Export PDF
8. Follow-up questions
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app
from backend.api.auth import get_current_user, get_current_user_optional

@pytest.mark.asyncio
class TestKitchenRenovationJourney:
    """Test complete kitchen renovation journey."""
    
    @pytest.fixture
    def client(self, test_user):
        """Create test client with auth override."""
        def override_get_current_user():
            return test_user
        
        def override_get_current_user_optional():
            return test_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_current_user_optional] = override_get_current_user_optional
        
        with TestClient(app) as client:
            yield client
        
        app.dependency_overrides.clear()
    
    async def test_step1_initial_idea_exploration(self, client, test_conversation):
        """
        Step 1: User asks about kitchen renovation ideas.
        Expected: AI provides overview and asks clarifying questions.
        """
        with patch("backend.integrations.gemini.client.GeminiClient.generate_text") as mock_gen:
            mock_gen.return_value = """
            I'd be happy to help with your kitchen renovation! To provide the best recommendations, 
            I have a few questions:
            
            1. What's your approximate budget range?
            2. Are you looking for a complete remodel or specific updates?
            3. What style do you prefer (modern, traditional, farmhouse, etc.)?
            """
            
            response = client.post(
                f"/api/chat/conversations/{test_conversation.id}/messages",
                json={
                    "message": "I'm thinking about renovating my kitchen. Where should I start?",
                    "mode": "agent"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "budget" in data["response"].lower()
            assert "style" in data["response"].lower()
            print(f"✅ Step 1 passed: Initial exploration successful")
    
    async def test_step2_provide_requirements(self, client, test_conversation):
        """
        Step 2: User provides budget and style preferences.
        Expected: AI suggests design options.
        """
        with patch("backend.integrations.gemini.client.GeminiClient.generate_text") as mock_gen:
            mock_gen.return_value = """
            Great! With a $30,000 budget for a modern kitchen, here are some options:
            
            **Option 1: Full Remodel** - $28,000-$32,000
            **Option 2: Refresh & Update** - $15,000-$20,000
            
            Would you like me to show you design examples?
            """
            
            response = client.post(
                f"/api/chat/conversations/{test_conversation.id}/messages",
                json={
                    "message": "My budget is around $30,000 and I prefer modern style",
                    "mode": "agent"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "option" in data["response"].lower()
            assert "$" in data["response"]
            print(f"✅ Step 2 passed: Requirements processed")
    
    # Add more test steps here...
```

### Afternoon: Run First Tests

```bash
# Run the journey test
pytest backend/tests/journeys/test_kitchen_renovation.py -v

# Run with output
pytest backend/tests/journeys/test_kitchen_renovation.py -v -s

# Check coverage
pytest backend/tests/journeys/ --cov=backend --cov-report=term-missing
```

---

## Day 3: CI/CD Setup

### Morning: Create GitHub Actions Workflow

**Create:** `.github/workflows/test.yml`
```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests with coverage
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: |
        pytest --cov=backend --cov-report=xml --cov-report=term -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
```

### Afternoon: Configure Coverage

**Create:** `.coveragerc`
```ini
[run]
source = backend
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*
    */.venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

**Create:** `pytest.ini`
```ini
[pytest]
testpaths = backend/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    asyncio: mark test as async
    integration: mark test as integration test
    performance: mark test as performance test
```

---

## Day 4: Add More Journey Tests

### Morning: Expand Kitchen Renovation Test

Add these test methods to `test_kitchen_renovation.py`:

```python
async def test_step3_request_visual_design(self, client, test_conversation):
    """Step 3: User requests visual design examples."""
    # Implementation here

async def test_step4_product_search_and_pricing(self, client, test_conversation):
    """Step 4: User asks for specific product recommendations."""
    # Implementation here

async def test_step5_diy_vs_contractor_decision(self, client, test_conversation):
    """Step 5: User asks whether to DIY or hire contractor."""
    # Implementation here
```

### Afternoon: Create Second Journey Test

**Create:** `backend/tests/journeys/test_diy_project.py`
```python
"""
End-to-end test for Journey 2: DIY Worker Bathroom Upgrade.

Tests DIY-specific flow with tool recommendations and safety warnings.
"""
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
class TestDIYBathroomUpgrade:
    """Test DIY bathroom upgrade journey."""
    
    async def test_step1_project_scope(self, client, test_conversation):
        """User describes DIY bathroom project."""
        # Implementation here
    
    async def test_step2_tool_recommendations(self, client, test_conversation):
        """AI provides tool list and safety warnings."""
        # Implementation here
```

---

## Day 5: Measure & Report

### Morning: Run Full Test Suite

```bash
# Run all tests with coverage
pytest --cov=backend --cov-report=html --cov-report=term -v

# Open coverage report
# Windows: start htmlcov/index.html
# Mac: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html

# Generate coverage badge
coverage-badge -o coverage.svg
```

### Afternoon: Document & Review

**Create:** `backend/tests/README.md`
```markdown
# HomeView AI Test Suite

## Running Tests

### All tests
```bash
pytest -v
```

### Specific test file
```bash
pytest backend/tests/journeys/test_kitchen_renovation.py -v
```

### With coverage
```bash
pytest --cov=backend --cov-report=html
```

## Test Structure

```
backend/tests/
├── fixtures/           # Shared test fixtures
│   └── test_data.py   # User, home, conversation fixtures
├── journeys/          # End-to-end journey tests
│   ├── test_kitchen_renovation.py
│   └── test_diy_project.py
├── unit/              # Unit tests (coming soon)
└── integration/       # Integration tests (coming soon)
```

## Coverage Goals

- **Week 1:** 30% coverage
- **Week 2:** 50% coverage
- **Week 3:** 70% coverage
- **Week 4:** 80% coverage

## CI/CD

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request

View results: [GitHub Actions](../../actions)
```

---

## Success Checklist

### Day 1 ✅
- [ ] Testing dependencies installed
- [ ] Test fixtures created
- [ ] `conftest.py` configured

### Day 2 ✅
- [ ] First journey test created
- [ ] At least 2 test steps passing
- [ ] Tests run locally

### Day 3 ✅
- [ ] GitHub Actions workflow created
- [ ] Coverage configuration added
- [ ] CI/CD running on push

### Day 4 ✅
- [ ] Kitchen renovation test complete (5+ steps)
- [ ] Second journey test started
- [ ] Coverage report generated

### Day 5 ✅
- [ ] Full test suite passing
- [ ] Coverage ≥30%
- [ ] Documentation complete
- [ ] Team demo prepared

---

## Common Issues & Solutions

### Issue: Tests fail with database errors
**Solution:** Ensure test database is properly initialized
```python
# In conftest.py
@pytest.fixture(scope="session")
async def setup_test_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
```

### Issue: Async tests not running
**Solution:** Add `pytest-asyncio` and configure
```ini
# In pytest.ini
[pytest]
asyncio_mode = auto
```

### Issue: Mocks not working
**Solution:** Patch at the right location
```python
# Patch where it's used, not where it's defined
with patch("backend.workflows.chat_workflow.GeminiClient.generate_text"):
    # Not: backend.integrations.gemini.client.GeminiClient
```

### Issue: Coverage too low
**Solution:** Focus on critical paths first
- Chat workflow (highest priority)
- RAG service
- Vision service
- Agent base classes

---

## Next Steps (Week 2)

1. **Add Unit Tests** - Test individual functions/classes
2. **Integration Tests** - Test service interactions
3. **Performance Tests** - Benchmark critical endpoints
4. **Edge Case Tests** - Error scenarios, invalid inputs
5. **Target:** 50% coverage

---

## Resources

- **pytest docs:** https://docs.pytest.org/
- **pytest-asyncio:** https://pytest-asyncio.readthedocs.io/
- **FastAPI testing:** https://fastapi.tiangolo.com/tutorial/testing/
- **Coverage.py:** https://coverage.readthedocs.io/

---

**Questions?** Check `CODE_IMPROVEMENTS_ASSESSMENT.md` for detailed guidance.

**Let's build robust tests! 🧪**

