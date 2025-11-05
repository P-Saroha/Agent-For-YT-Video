# Contributing to AI Content Analysis Platform

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git
- Google Gemini API key

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/P-Saroha/Agent-For-YT-Video.git
cd Agent-For-YT-Video

# Create virtual environment
python -m venv myenv
source myenv/bin/activate  # Linux/Mac
# myenv\Scripts\activate    # Windows

# Install dependencies
pip install -r server/requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Set up environment variables
cp server/.env.example server/.env
# Edit .env and add your API keys
```

## 📋 Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes
- Write clean, documented code
- Follow existing code style
- Add tests for new features
- Update documentation if needed

### 3. Run Tests
```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=server --cov-report=html
```

### 4. Code Quality Checks
```bash
# Format code
make format

# Run linters
make lint

# Run security checks
make security
```

### 5. Commit Changes
```bash
git add .
git commit -m "feat: Add new feature description"
# Use conventional commits format
```

### 6. Push and Create PR
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub.

## 📝 Coding Standards

### Python Style Guide
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use descriptive variable names

### Example:
```python
async def process_content(url: str, question: str) -> Dict[str, Any]:
    """
    Process content and generate answer.
    
    Args:
        url: The content URL to process
        question: User's question about the content
        
    Returns:
        Dictionary containing answer and metadata
        
    Raises:
        ValueError: If URL is invalid
    """
    # Implementation
    pass
```

### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: Add PDF processing support
fix: Resolve YouTube transcript extraction bug
docs: Update API documentation
test: Add integration tests for web scraping
```

## 🧪 Testing Guidelines

### Types of Tests
1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test service interactions
3. **API Tests**: Test HTTP endpoints

### Writing Tests
```python
class TestYouTubeService:
    """Test YouTube processing service"""
    
    def test_extract_video_id(self):
        """Test video ID extraction from URL"""
        url = "https://youtube.com/watch?v=abc123"
        video_id = extract_video_id(url)
        assert video_id == "abc123"
    
    @pytest.mark.integration
    async def test_process_video(self):
        """Test complete video processing"""
        result = await process_video("https://youtube.com/...")
        assert "answer" in result
```

### Test Coverage
- Aim for >80% code coverage
- All new features must include tests
- Critical paths require comprehensive testing

## 📚 Documentation

### Code Documentation
- Docstrings for all functions, classes, methods
- Include type hints
- Explain complex logic with comments

### API Documentation
- Update OpenAPI schema if adding endpoints
- Include request/response examples
- Document error codes and responses

### README Updates
- Update features list for new functionality
- Add usage examples
- Update installation instructions if needed

## 🔍 Code Review Process

### Before Requesting Review
- [ ] All tests pass
- [ ] Code is formatted and linted
- [ ] Documentation is updated
- [ ] No merge conflicts
- [ ] Commit messages follow convention

### During Review
- Be responsive to feedback
- Make requested changes promptly
- Ask questions if unclear
- Keep discussions focused

## 🐛 Bug Reports

### Good Bug Report Includes:
1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: How to trigger the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, etc.
6. **Logs/Screenshots**: Error messages or visual evidence

### Template:
```markdown
**Description**
Brief description of the bug

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: Windows 11
- Python: 3.11.5
- Browser: Chrome 120

**Logs**
```
Error logs here
```
```

## 💡 Feature Requests

### Good Feature Request Includes:
1. **Problem Statement**: What problem does it solve?
2. **Proposed Solution**: How would you solve it?
3. **Alternatives**: Other solutions considered?
4. **Use Case**: Real-world examples?

## 🎯 Areas for Contribution

### Good First Issues
- Documentation improvements
- Adding tests
- Bug fixes
- Code refactoring

### Advanced Contributions
- New content source support (Twitter, Reddit, etc.)
- Performance optimizations
- New LLM integrations
- Advanced RAG features

## 📞 Getting Help

- 💬 [GitHub Discussions](https://github.com/P-Saroha/Agent-For-YT-Video/discussions)
- 🐛 [Issue Tracker](https://github.com/P-Saroha/Agent-For-YT-Video/issues)
- 📧 Email: parveensaroha@example.com

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
