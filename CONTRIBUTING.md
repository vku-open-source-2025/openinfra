# Contributing to OpenInfra

First off, thank you for considering contributing to OpenInfra! 🎉

OpenInfra is an open-source urban infrastructure asset management system, and we welcome contributions from the community. Whether you're fixing bugs, adding features, improving documentation, or reporting issues, your help is appreciated.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

---

## 📜 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

---

## 🤝 How Can I Contribute?

### Reporting Bugs 🐛

Before creating a bug report, please check the [existing issues](https://github.com/your-org/openinfra/issues) to see if the problem has already been reported.

When creating a bug report, use the bug report template and include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, browser, versions)
- Error messages or logs

### Suggesting Features 💡

We love feature suggestions! Please use the feature request template and include:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Examples from other projects (if applicable)

### Submitting Pull Requests 🔧

We actively welcome your pull requests! See the [Pull Request Process](#pull-request-process) section below.

### Improving Documentation 📚

Documentation improvements are always welcome:
- Fix typos or clarify existing docs
- Add examples and tutorials
- Translate documentation
- Add API usage examples

### Answering Questions ❓

Help others by answering questions in:
- [GitHub Discussions](https://github.com/your-org/openinfra/discussions)
- GitHub Issues labeled with `question`

---

## 🛠️ Development Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**

### Initial Setup

1. **Fork and Clone**

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/openinfra.git
cd openinfra

# Add upstream remote
git remote add upstream https://github.com/your-org/openinfra.git
```

2. **Start Infrastructure Services**

```bash
cd infra
docker-compose up -d
```

3. **Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black flake8 mypy pytest pytest-asyncio pytest-cov

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Initialize database
python scripts/init_db.py
python scripts/create_superuser.py
```

4. **Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
# Edit .env with backend URL
```

5. **Verify Setup**

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Open http://localhost:5173
```

---

## 🔄 Development Workflow

### 1. Create a Branch

Always create a new branch for your work:

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/issue-description

# Or for documentation
git checkout -b docs/what-you-are-documenting
```

### Branch Naming Convention

- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes
- `docs/*` - Documentation updates
- `refactor/*` - Code refactoring
- `test/*` - Adding or updating tests
- `chore/*` - Maintenance tasks

### 2. Make Changes

- Write clean, readable code
- Follow the [coding standards](#coding-standards)
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Backend tests
cd backend
pytest
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test
npm run test:coverage

# E2E tests
npm run test:e2e
```

### 4. Commit Changes

Follow the [commit guidelines](#commit-guidelines):

```bash
git add .
git commit -m "feat: add asset filtering by location"
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Go to GitHub and create a Pull Request
```

---

## 📝 Coding Standards

### Python (Backend)

**Style Guide**: PEP 8

**Formatting**: We use Black for automatic formatting

```bash
# Format code
black app/

# Check formatting
black --check app/
```

**Linting**: We use flake8

```bash
flake8 app/
```

**Type Hints**: Required for all functions

```python
def create_asset(asset_data: dict) -> Asset:
    """
    Create a new infrastructure asset.

    Args:
        asset_data: Dictionary containing asset information

    Returns:
        Created Asset object

    Raises:
        ValidationError: If asset_data is invalid
    """
    ...
```

**Docstrings**: Use Google-style docstrings

**Imports**: Organized with isort

```bash
isort app/
```

**Example**:

```python
from typing import Optional, List
from datetime import datetime

from app.domain.models.asset import Asset
from app.domain.repositories.asset_repository import AssetRepository


class AssetService:
    """Service for managing infrastructure assets."""

    def __init__(self, repository: AssetRepository) -> None:
        self.repository = repository

    async def create_asset(
        self,
        name: str,
        asset_type: str,
        coordinates: dict
    ) -> Asset:
        """Create a new asset with validation."""
        ...
```

### TypeScript/JavaScript (Frontend)

**Style Guide**: [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)

**Formatting**: ESLint + Prettier

```bash
# Lint code
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix
```

**Type Safety**: Use TypeScript strictly

```typescript
// Good
interface AssetProps {
  id: string;
  name: string;
  location: Coordinates;
}

function AssetCard({ id, name, location }: AssetProps) {
  ...
}

// Avoid 'any'
// Bad
function processData(data: any) { ... }

// Good
function processData(data: unknown) {
  if (isAssetData(data)) {
    ...
  }
}
```

**React Best Practices**:

- Use functional components with hooks
- Properly type props and state
- Use meaningful component names
- Extract reusable logic into custom hooks
- Keep components focused and small

**Example**:

```typescript
interface AssetListProps {
  filters: AssetFilters;
  onAssetSelect: (assetId: string) => void;
}

export const AssetList: React.FC<AssetListProps> = ({
  filters,
  onAssetSelect,
}) => {
  const { data, isLoading, error } = useAssets(filters);

  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div className="space-y-4">
      {data?.assets.map((asset) => (
        <AssetCard
          key={asset.id}
          asset={asset}
          onClick={() => onAssetSelect(asset.id)}
        />
      ))}
    </div>
  );
};
```

### General Guidelines

- **DRY**: Don't Repeat Yourself
- **SOLID Principles**: Especially Single Responsibility
- **Clean Architecture**: Respect layer boundaries
- **Meaningful Names**: Use descriptive variable/function names
- **Comments**: Explain *why*, not *what*
- **Error Handling**: Always handle errors gracefully
- **Security**: Never commit secrets or credentials

---

## 📝 Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **ci**: CI/CD changes
- **build**: Build system changes

### Scope (Optional)

The scope indicates what area of the codebase is affected:

- `assets` - Asset management
- `maintenance` - Maintenance features
- `iot` - IoT sensors
- `auth` - Authentication
- `api` - API endpoints
- `ui` - User interface
- `docs` - Documentation

### Examples

```bash
# Feature
git commit -m "feat(assets): add geospatial filtering for assets"

# Bug fix
git commit -m "fix(auth): resolve JWT token expiration issue"

# Documentation
git commit -m "docs(api): add examples for maintenance endpoints"

# Refactoring
git commit -m "refactor(services): extract common validation logic"

# Breaking change
git commit -m "feat(api): change asset response format

BREAKING CHANGE: asset response now includes GeoJSON geometry instead of separate lat/lng fields"
```

### Commit Best Practices

- Use imperative mood ("add feature" not "added feature")
- Keep subject line under 50 characters
- Capitalize subject line
- Don't end subject with a period
- Add body if needed to explain *what* and *why*
- Reference issues: "Closes #123" or "Fixes #456"

---

## 🔀 Pull Request Process

### Before Submitting

1. **Update your branch** with latest upstream changes:

```bash
git checkout main
git pull upstream main
git checkout your-feature-branch
git rebase main
```

2. **Run all tests**:

```bash
# Backend
cd backend
pytest --cov=app

# Frontend
cd frontend
npm test
npm run lint
```

3. **Update documentation** if needed

4. **Add/update tests** for your changes

### Submitting the PR

1. **Push to your fork**:

```bash
git push origin your-feature-branch
```

2. **Create Pull Request** on GitHub

3. **Fill out the PR template** completely:
   - Clear description of changes
   - Link to related issues
   - Screenshots (for UI changes)
   - Test results
   - Breaking changes (if any)

4. **Request review** from maintainers

### PR Title Format

Use the same format as commit messages:

```
feat(assets): add geospatial filtering
fix(auth): resolve token expiration bug
docs(api): add maintenance endpoint examples
```

### Review Process

- Maintainers will review your PR within 48 hours
- Address review feedback promptly
- Keep discussions professional and constructive
- Be open to suggestions and alternative approaches
- Once approved, a maintainer will merge your PR

### After Your PR is Merged

1. **Delete your branch**:

```bash
git branch -d your-feature-branch
git push origin --delete your-feature-branch
```

2. **Update your fork**:

```bash
git checkout main
git pull upstream main
git push origin main
```

3. **Celebrate!** 🎉 You've contributed to OpenInfra!

---

## 🧪 Testing

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Aim for > 80% code coverage
- Tests should be fast and isolated

### Backend Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/e2e/test_assets.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/e2e/test_assets.py::test_create_asset
```

**Test Structure**:

```python
# tests/e2e/test_assets.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_asset(client: AsyncClient, admin_token: str):
    """Test asset creation with valid data."""
    response = await client.post(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Asset",
            "feature_type": "bts_station",
            "coordinates": {"lng": 108.2, "lat": 16.0}
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Asset"
    assert "id" in data
```

### Frontend Testing

```bash
# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run in watch mode
npm test -- --watch
```

**Test Structure**:

```typescript
// components/AssetCard.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AssetCard } from './AssetCard';

describe('AssetCard', () => {
  it('renders asset information correctly', () => {
    const asset = {
      id: '1',
      name: 'Test Asset',
      status: 'operational'
    };

    render(<AssetCard asset={asset} />);

    expect(screen.getByText('Test Asset')).toBeInTheDocument();
    expect(screen.getByText('operational')).toBeInTheDocument();
  });

  it('calls onClick when card is clicked', async () => {
    const onClickMock = jest.fn();
    const asset = { id: '1', name: 'Test' };

    render(<AssetCard asset={asset} onClick={onClickMock} />);

    await userEvent.click(screen.getByRole('button'));

    expect(onClickMock).toHaveBeenCalledWith('1');
  });
});
```

---

## 📚 Documentation

### Types of Documentation

1. **Code Comments**: Explain complex logic
2. **Docstrings/JSDoc**: Document functions and classes
3. **README**: Project overview and setup
4. **API Docs**: Endpoint documentation (auto-generated)
5. **Architecture Docs**: System design
6. **User Guides**: How to use features

### Documentation Guidelines

- Keep documentation up-to-date with code changes
- Use clear, simple language
- Include examples and code snippets
- Add diagrams for complex concepts
- Test all examples to ensure they work

### Updating Documentation

If your PR changes:
- **API**: Update `backend/docs/API_DOCUMENTATION.md`
- **Architecture**: Update `backend/docs/architecture.md`
- **Features**: Update `README.md`
- **Setup**: Update setup instructions

---

## 💬 Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussions, Q&A
- **Pull Requests**: Code review and technical discussions

### Getting Help

- Check existing documentation
- Search closed issues for similar problems
- Ask in GitHub Discussions
- Be patient and respectful

### Recognition

Contributors will be:
- Listed in `AUTHORS.md`
- Mentioned in release notes
- Thanked in our README

---

## 🎯 Good First Issues

New to the project? Look for issues labeled:
- `good first issue` - Easy tasks for beginners
- `help wanted` - Tasks where we need help
- `documentation` - Documentation improvements

---

## 📋 Checklist for Pull Requests

Before submitting, ensure:

- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Branch is up-to-date with main
- [ ] No merge conflicts
- [ ] PR description is clear and complete
- [ ] Related issues are linked
- [ ] Screenshots added (for UI changes)

---

## ❓ Questions?

If you have questions about contributing:
1. Check this guide thoroughly
2. Search existing issues/discussions
3. Ask in [GitHub Discussions](https://github.com/your-org/openinfra/discussions)
4. Reach out to maintainers

---

## 🙏 Thank You!

Thank you for contributing to OpenInfra! Your efforts help build better infrastructure management tools for cities and communities worldwide.

---

**Happy Contributing! 🚀**
