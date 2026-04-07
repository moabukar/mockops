# MockOps

Interactive CLI tool for DevOps interview preparation. 190+ scenario-based questions across 12 topics, with difficulty tracking and mock interviews.

[![Build Status](https://github.com/moabukar/mockops/workflows/CI/badge.svg)](https://github.com/moabukar/mockops/actions)
[![Docker Pulls](https://img.shields.io/docker/pulls/moabukar/mockops)](https://hub.docker.com/r/moabukar/mockops)

## Quick Start

```bash
# Homebrew
brew tap moabukar/tap
brew install mockops

# Docker
docker run -it --rm moabukar/mockops practice aws

# pip
pip install git+https://github.com/moabukar/mockops.git
mockops practice aws --count 10
```

## Topics

| Topic | Questions | Topic | Questions |
|-------|-----------|-------|-----------|
| Kubernetes | 30 | Ansible | 15 |
| AWS | 27 | Networking | 12 |
| Linux | 17 | Git | 11 |
| Azure | 15 | Terraform | 11 |
| Monitoring | 15 | CI/CD | 11 |
| Security | 15 | Docker | 13 |

Difficulty split: 58 easy, 72 medium, 62 hard. Total: 192 questions.

## Usage

```bash
# Practice by topic and difficulty
mockops practice <topic> --difficulty <easy|medium|hard> --count <number>

# Focus on weak areas
mockops weak-areas
mockops review-mistakes

# Mock interview
mockops interview --count 20

# View progress
mockops analytics --topic <topic>

# Quick single question
mockops quick

# AWS scenario prep with free-text grading (Claude on Bedrock)
mockops aws-scenario --count 3 --region us-east-1

# Reset progress
mockops reset
```

Set `AWS_REGION` and your AWS credentials/profile in the environment for Bedrock access. Optionally override model with `MOCKOPS_BEDROCK_MODEL_ID`.

## Docker

```bash
# Practice a topic
docker run -it --rm moabukar/mockops practice kubernetes

# Run a mock interview
docker run -it --rm moabukar/mockops interview --count 15

# Export results
docker run -v $(pwd):/export -it --rm moabukar/mockops practice aws --export /export/results.json

# Persistent progress
docker run -it --rm -v mockops-data:/home/devops-interviewer/.mockops moabukar/mockops practice aws
```

## Development

```bash
make setup          # Install dependencies
make test           # Run tests
make docker-build   # Build Docker image
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for adding questions, reporting issues, and development setup.

## License

MIT
