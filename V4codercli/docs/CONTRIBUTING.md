# Contributing to RR4 Complete Enhanced v4 CLI

We welcome contributions to the RR4 Complete Enhanced v4 CLI project! This document provides guidelines for contributing to the project.

## 🎯 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contributing Guidelines](#contributing-guidelines)
5. [Submitting Changes](#submitting-changes)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Issue Reporting](#issue-reporting)

## 📜 Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

### Our Standards

- **Be respectful**: Treat everyone with respect and kindness
- **Be inclusive**: Welcome newcomers and encourage diverse perspectives
- **Be collaborative**: Work together to solve problems
- **Be professional**: Maintain professional conduct in all interactions

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Git**
- **Basic understanding of network automation**
- **Familiarity with Cisco IOS/IOS XE/IOS XR**

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork locally**:
   ```bash
   git clone https://github.com/yourusername/V4codercli.git
   cd V4codercli
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/original/V4codercli.git
   ```

## 🛠️ Development Setup

### 1. Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .
```

### 3. Environment Configuration

```bash
# Configure environment for testing
python3 rr4-complete-enchanced-v4-cli.py configure-env
```

### 4. Verify Setup

```bash
# Run basic tests
python3 -m pytest tests/

# Test import functionality
python3 -c "from V4codercli import rr4_complete_enchanced_v4_cli_core; print('Setup OK')"
```

## 📋 Contributing Guidelines

### Code Style

- **Follow PEP 8** coding standards
- **Use meaningful variable names**
- **Add docstrings** to all functions and classes
- **Include type hints** where appropriate
- **Keep functions focused** and single-purpose

### Example Code Style:

```python
def collect_layer_data(self, connection: Any, hostname: str, platform: str,
                      output_handler: OutputHandler) -> Dict[str, Any]:
    """Collect layer data from network device.
    
    Args:
        connection: Network device connection object
        hostname: Device hostname
        platform: Device platform (ios, iosxe, iosxr)
        output_handler: Output handler instance
        
    Returns:
        Dictionary containing collection results
        
    Raises:
        ConnectionError: If device connection fails
        ValueError: If invalid parameters provided
    """
```

### Commit Guidelines

- **Use conventional commits**: `type(scope): description`
- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- **Keep commits atomic**: One logical change per commit
- **Write descriptive messages**

### Examples:

```bash
feat(collector): add support for Juniper devices
fix(bgp): resolve neighbor counting issue
docs(readme): update installation instructions
test(igp): add OSPF neighbor parsing tests
```

## 🔄 Submitting Changes

### 1. Branch Strategy

```bash
# Create feature branch
git checkout -b feature/add-juniper-support

# Create bugfix branch
git checkout -b fix/ospf-neighbor-parsing

# Create documentation branch
git checkout -b docs/api-documentation
```

### 2. Making Changes

1. **Make your changes** in focused, logical commits
2. **Test your changes** thoroughly
3. **Update documentation** if needed
4. **Add tests** for new functionality

### 3. Pull Request Process

1. **Update your branch** with latest upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request** with:
   - **Clear title and description**
   - **Link to related issues**
   - **Screenshots** (if UI changes)
   - **Test results**

### Pull Request Template:

```markdown
## Description
Brief description of changes

## Related Issues
Fixes #123
Related to #456

## Changes Made
- Added support for feature X
- Fixed bug in component Y
- Updated documentation for Z

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Documentation updated

## Screenshots (if applicable)
[Add screenshots here]
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test file
python3 -m pytest tests/test_collectors.py

# Run with coverage
python3 -m pytest --cov=V4codercli tests/

# Run integration tests
python3 -m pytest tests/integration/
```

### Writing Tests

- **Unit tests** for individual functions
- **Integration tests** for component interaction
- **Mock external dependencies** (network devices)
- **Test both success and failure cases**

### Test Structure:

```python
import pytest
from unittest.mock import Mock, patch
from V4codercli.rr4_complete_enchanced_v4_cli_tasks.igp_collector import IGPCollector

class TestIGPCollector:
    def setup_method(self):
        """Setup test fixtures."""
        self.collector = IGPCollector()
        self.mock_connection = Mock()
    
    def test_collect_ospf_neighbors(self):
        """Test OSPF neighbor collection."""
        # Setup
        mock_output = "Neighbor ID     Pri   State           Interface\n1.1.1.1         1     Full/DR         GigabitEthernet0/0"
        self.mock_connection.send_command.return_value = mock_output
        
        # Execute
        result = self.collector._analyze_igp_output("show ip ospf neighbor", mock_output, {})
        
        # Assert
        assert result['ospf_neighbors'] > 0
```

## 📖 Documentation

### Documentation Requirements

- **Update README.md** for major changes
- **Add docstrings** to all new functions/classes
- **Update CHANGELOG.md** for all changes
- **Create examples** for new features
- **Update troubleshooting guide** for common issues

### Documentation Standards

- **Use clear, concise language**
- **Include code examples**
- **Add screenshots where helpful**
- **Keep examples up-to-date**
- **Use proper markdown formatting**

## 🐛 Issue Reporting

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check troubleshooting guide**
3. **Test with latest version**
4. **Gather debugging information**

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## Environment
- Python version: 3.x.x
- OS: Ubuntu 20.04
- Package versions: (paste output of `pip list | grep -E "(netmiko|nornir)"`)

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Error Messages
```
Paste full error traceback here
```

## Additional Context
Any other relevant information
```

### Feature Request Template

```markdown
## Feature Description
Clear description of the requested feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other approaches you've considered

## Additional Context
Any other relevant information
```

## 🎯 Areas for Contribution

### High Priority

- **Additional platform support** (Juniper, Arista, etc.)
- **Enhanced parsing capabilities**
- **Performance optimizations**
- **Error handling improvements**

### Medium Priority

- **API integration**
- **Real-time monitoring features**
- **Enhanced reporting**
- **Configuration validation**

### Documentation

- **Tutorial creation**
- **API documentation**
- **Video guides**
- **Translation to other languages**

## 🔧 Development Guidelines

### Adding New Collectors

1. **Create collector module** in `rr4_complete_enchanced_v4_cli_tasks/`
2. **Implement required methods**:
   ```python
   def collect_layer_data(self, connection, hostname, platform, output_handler):
       """Collect data for this layer."""
       pass
   
   def get_layer_info(self):
       """Return layer information."""
       pass
   ```

3. **Add platform-specific commands**
4. **Update task executor mapping**
5. **Add comprehensive tests**
6. **Update documentation**

### Modifying Core Components

- **Maintain backward compatibility**
- **Add comprehensive tests**
- **Update all affected documentation**
- **Consider performance impact**
- **Follow existing patterns**

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Documentation**: Check existing docs first

### Maintainer Response

- **Bug reports**: 24-48 hours
- **Feature requests**: 1-2 weeks
- **Pull requests**: 3-5 days

## 🏆 Recognition

Contributors are recognized in:
- **CHANGELOG.md** for significant contributions
- **README.md** contributors section
- **Release notes** for major features

Thank you for contributing to RR4 Complete Enhanced v4 CLI! 🎉 