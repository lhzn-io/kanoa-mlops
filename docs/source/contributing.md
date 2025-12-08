# Contributing Guide

Thank you for contributing to kanoa-mlops! This guide will help you contribute benchmark results, bug fixes, and new features.

## Quick Links

- **Report a Bug**: [GitHub Issues](https://github.com/lhzn-io/kanoa-mlops/issues)
- **Request a Feature**: [GitHub Discussions](https://github.com/lhzn-io/kanoa-mlops/discussions)
- **Submit Benchmark Results**: See [Submitting Benchmark Results](#submitting-benchmark-results)
- **Add Model Support**: See [Model Support Guide](model-support.md)

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/kanoa-mlops.git
cd kanoa-mlops

# Add upstream remote
git remote add upstream https://github.com/lhzn-io/kanoa-mlops.git
```

### 2. Set Up Development Environment

```bash
# Create conda environment
conda env create -f environment.yml
conda activate kanoa-mlops

# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
# or
git checkout -b docs/your-documentation-update
```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run specific integration test
python3 tests/integration/test_ollama_gemma3.py

# Run linting
make lint
```

### Code Style

We use:

- **Ruff** for linting and formatting
- **Type hints** where applicable
- **Docstrings** for all public functions

```bash
# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat: add support for OLMo-3 model
fix: resolve GPU memory leak in vLLM
docs: update quickstart guide
style: fix linting issues
test: add benchmark for Jetson Thor
chore: update dependencies
```

## Submitting Benchmark Results

We welcome benchmark results from different hardware configurations!

### 1. Run Benchmarks

```bash
cd tests/integration

# Run benchmark suite (3 iterations)
python3 run_benchmark_suite_ollama.py  # or other suite
```

### 2. Document Your Setup

Create a results file in `docs/results/`:

**Filename format**: `<model>-<hardware>.md`

Example: `gemma3-4b-jetson-thor.md`

**Template**:

```markdown
# [Model Name] on [Hardware]

## Hardware

- **Platform**: [e.g., NVIDIA Jetson Thor]
- **GPU**: [Model and VRAM]
- **CPU**: [Model]
- **RAM**: [Amount]
- **Storage**: [Type]

## Software

- **OS**: [Version]
- **CUDA**: [Version]
- **Docker**: [Version]
- **Runtime**: [Ollama/vLLM version]

## Model Configuration

- **Model**: [Full model name]
- **Quantization**: [None/INT8/INT4]
- **Context Length**: [tokens]
- **Batch Size**: [number]

## Performance Results

### Throughput

| Metric | Value |
|--------|-------|
| Mean | XX.X tok/s |
| StdDev | X.X tok/s |
| Min | XX.X tok/s |
| Max | XX.X tok/s |

### Resource Usage

- **GPU Memory**: XX GB / XX GB (XX%)
- **GPU Utilization**: XX%
- **System RAM**: XX GB / XX GB
- **Power Draw**: XX W

### Latency

- **Time to First Token**: XXX ms
- **Per-Token Latency**: XX ms

## Test Details

- **Date**: YYYY-MM-DD
- **Benchmark Suite**: [run_benchmark_suite_*.py]
- **Number of Runs**: 3
- **Test Duration**: XX minutes

## Observations

[Any notable behaviors, thermal performance, stability notes]

## Raw Results

\`\`\`json
{
  "summary": {
    "mean_throughput": XX.X,
    "std_throughput": X.X,
    "min_throughput": XX.X,
    "max_throughput": XX.X
  }
}
\`\`\`
```

### 3. Submit PR

```bash
git add docs/results/your-results.md
git commit -m "docs: add benchmark results for [Model] on [Hardware]"
git push origin your-branch
```

## Adding New Features

### 1. Discuss First

For major features, open a GitHub Discussion or Issue first to:

- Validate the approach
- Avoid duplicate work
- Get early feedback

### 2. Implement

- Write tests first (TDD recommended)
- Follow existing code patterns
- Add documentation
- Update relevant guides

### 3. Test Thoroughly

```bash
# Run full test suite
make test

# Run linting
make lint

# Test on your hardware
make serve-ollama  # or relevant service
python3 tests/integration/test_*.py
```

### 4. Document

- Update relevant `.md` files
- Add docstrings to new functions
- Update `README.md` if needed
- Add examples if applicable

## Submitting Pull Requests

### PR Checklist

- [ ] Tests pass locally (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with `main`

### PR Template

```markdown
## Description

[Brief description of changes]

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Benchmark results
- [ ] Performance improvement

## Testing

- [ ] Tested locally on [hardware]
- [ ] All tests pass
- [ ] Linting passes

## Hardware Tested

- **Platform**: [e.g., RTX 5080, Jetson Thor]
- **OS**: [Version]
- **CUDA**: [Version]

## Benchmark Results (if applicable)

| Metric | Before | After |
|--------|--------|-------|
| Throughput | XX tok/s | YY tok/s |

## Additional Notes

[Any other relevant information]
```

## Review Process

1. **Automated Checks**: GitHub Actions will run tests and linting
2. **Maintainer Review**: A maintainer will review your PR
3. **Feedback**: Address any requested changes
4. **Merge**: Once approved, your PR will be merged!

## Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully

### Be Helpful

- Help others in Issues and Discussions
- Share your knowledge and experience
- Document your findings

### Be Collaborative

- Give credit where it's due
- Build on others' work
- Share benchmark results openly

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/lhzn-io/kanoa-mlops/discussions)
- **Bugs**: [GitHub Issues](https://github.com/lhzn-io/kanoa-mlops/issues)
- **Chat**: [Discord/Slack if available]

## Recognition

Contributors are recognized in:

- `CONTRIBUTORS.md`
- Release notes
- Documentation credits

Thank you for contributing to kanoa-mlops! 🚀

## See Also

- [Model Support Guide](model-support.md)
- [Quickstart Guide](quickstart.md)
- [Benchmarking Guide](../tests/integration/README.md)
- [Code of Conduct](../../CODE_OF_CONDUCT.md)
