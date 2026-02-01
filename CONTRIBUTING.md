# Contributing to Enterprise RAG System

Thank you for your interest in contributing to the Enterprise RAG System! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/bambusoe02/rag-chatbot.git
   cd rag-chatbot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   # Backend
   python -m uvicorn backend.main:app --reload
   
   # Frontend
   streamlit run frontend/app.py
   ```

## 📝 Development Guidelines

### Code Style

- **Python 3.11+**: Use type hints for all functions
- **Black**: Code formatting - run `black .` before committing
- **Flake8**: Linting - follow PEP 8 style guide
- **MyPy**: Type checking - run `mypy .` to verify types

### Testing

- Write tests for new features using pytest
- Run tests: `pytest tests/ -v`
- Run tests with coverage: `pytest tests/ -v --cov=. --cov-report=html`
- Aim for 70%+ test coverage for new code
- Use `pytest-asyncio` for async function tests

### Commit Messages

Follow conventional commits format:
- `feat: add new feature`
- `fix: resolve bug`
- `docs: update documentation`
- `refactor: improve code structure`
- `test: add tests`
- `chore: update dependencies`

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**
   - Write clean, tested code
   - Update documentation if needed
   - Follow code style guidelines

3. **Run checks before submitting**
   ```bash
   black .
   flake8 .
   mypy . --ignore-missing-imports
   pytest tests/ -v
   ```

4. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

## 🐛 Reporting Bugs

When reporting bugs, please include:
- **Description**: Clear description of the bug
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: Python version, OS, Ollama version
- **Error messages**: Full error traceback if applicable

## 💡 Suggesting Features

When suggesting features:
- **Use case**: Describe the problem you're trying to solve
- **Proposed solution**: How you envision the feature working
- **Alternatives**: Other solutions you've considered
- **Additional context**: Any other relevant information

## 🔒 Security Issues

**Do not** open public issues for security vulnerabilities. Instead, email security concerns to: bambusoe@gmail.com

## 📚 Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Update API documentation
- Keep CHANGELOG.md updated (if applicable)

## ✅ Code Review Checklist

Before submitting PR, ensure:
- [ ] Code follows style guidelines (Black, Flake8)
- [ ] All tests pass
- [ ] Type hints are added
- [ ] No print statements (use logging)
- [ ] Error handling is implemented
- [ ] Documentation is updated
- [ ] No hardcoded secrets or API keys
- [ ] Environment variables are documented

## 🎯 Areas for Contribution

We welcome contributions in:
- **New features**: RAG improvements, new document formats, UI enhancements
- **Bug fixes**: Any issues you encounter
- **Documentation**: Improvements to docs, examples, tutorials
- **Testing**: Increase test coverage
- **Performance**: Optimizations and improvements
- **Security**: Security enhancements
- **Docker/K8s**: Deployment improvements

## 📞 Questions?

Feel free to:
- Open an issue for questions
- Email: bambusoe@gmail.com
- Check existing issues and discussions

Thank you for contributing to Enterprise RAG System! 🎉

