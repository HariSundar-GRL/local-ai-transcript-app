# Mind-map Feature Tests

This document describes the unit tests for the mind-map generation feature.

## Overview

The mind-map feature allows users to generate visual mind-maps from transcribed text using AI and Graphviz. The backend tests provide comprehensive coverage of the core functionality.

## Prerequisites

- **Python 3.12+**
- **pytest and test dependencies** (installed via `pip install -e ".[dev]"`)

## Backend Tests (`backend/test_mindmap.py`)

### Test Coverage

#### TranscriptionService Tests

- ✅ **Successful mind-map generation**: Validates DOT code generation from text
- ✅ **Markdown removal**: Ensures code blocks are stripped from LLM output
- ✅ **Empty text handling**: Tests behavior with empty input
- ✅ **LLM error handling**: Validates fallback mind-map on errors

#### API Endpoint Tests (`/api/mindmap`)

- ✅ **Successful SVG generation**: Tests complete flow from text to SVG
- ✅ **Service not ready**: Validates 503 error when service uninitialized
- ✅ **Graphviz not found**: Tests FileNotFoundError handling
- ✅ **Graphviz execution errors**: Validates error handling for invalid DOT code
- ✅ **Timeout handling**: Tests subprocess timeout scenarios
- ✅ **Invalid requests**: Validates request validation
- ✅ **Empty text**: Tests edge case handling

#### Integration Tests

- ✅ **DOT code validation**: Ensures generated code is valid Graphviz syntax
- ✅ **Method availability**: Validates service API

### Running Backend Tests

```bash
cd backend

# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest test_mindmap.py -v

# Run with coverage
pytest test_mindmap.py --cov=. --cov-report=html

# Run specific test class
pytest test_mindmap.py::TestMindMapAPI -v

# Run specific test
pytest test_mindmap.py::TestMindMapAPI::test_mindmap_endpoint_success -v
```

## Test Results

**13 tests** - All passing ✅
**Coverage**: 78% across app.py, transcription.py, and test files

## Test Dependencies

- `pytest`: Test framework
- `pytest-cov`: Coverage reporting
- `pytest-asyncio`: Async test support
- `httpx`: HTTP client for FastAPI testing

## Configuration Files

- `backend/pytest.ini`: Pytest configuration and coverage settings
- `backend/pyproject.toml`: Package configuration with dev dependencies

## CI/CD Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Backend Tests
  run: |
    cd backend
    pip install -e ".[dev]"
    pytest test_mindmap.py --cov --cov-report=xml
```

## Coverage Goals

- **Backend**: Aim for >90% coverage of mind-map related code (currently at 78%)

## Mock Strategy

### Backend Mocks

- **OpenAI Client**: Mocked to avoid actual API calls
- **Whisper Model**: Mocked to skip model loading
- **Subprocess**: Mocked for Graphviz execution

## Common Issues

1. **Graphviz not installed**: Tests mock subprocess calls
2. **OpenAI API errors**: Tests use mocked responses
3. **Async test issues**: Use `pytest-asyncio` markers

## Future Improvements

- [ ] Add E2E tests for complete user flow
- [ ] Add visual regression tests for mind-map rendering
- [ ] Add performance benchmarks
- [ ] Add stress tests for large mind-maps
- [ ] Add frontend component tests when Node.js is upgraded to v24+
