# Story 8.1: Deployment & Packaging

## Overview

**Priority**: P1 (Nice to Have)  
**Dependencies**: All implementation stories (0.0-7.2)  
**Estimated Effort**: Medium (1-2 days)  
**Layer**: 8 (Deployment)

## Description

Create deployment and packaging strategies to enable distribution and production deployment of the Algarve Padel Market Research Tool. This includes containerization with Docker, packaging for PyPI distribution, and production environment configuration.

## Business Value

- Enables easy distribution to end users
- Simplifies deployment to production environments
- Provides consistent runtime environment
- Supports multiple deployment scenarios (local, cloud, container)
- Professional packaging for potential commercial use

## Input Contract

- Completed, tested codebase (all stories 0.0-7.2 complete)
- All tests passing
- Documentation complete
- Application working locally

## Output Contract

Multiple deployment options:
1. **Docker Container** - Containerized application
2. **PyPI Package** - Installable via pip
3. **Standalone Package** - Bundled application
4. **Cloud Deployment Guide** - Instructions for cloud platforms

## Deliverables

### 1. Dockerfile

Multi-stage Docker build for production deployment:

```dockerfile
# Stage 1: Build environment
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime environment
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY .env.example .env

# Create data directories
RUN mkdir -p data/{raw,processed,cache,exports}

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit app
CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. docker-compose.yml

Docker Compose for easy local deployment:

```yaml
version: '3.8'

services:
  padel-research:
    build: .
    container_name: padel-research-app
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3. setup.py (for PyPI)

Package configuration for pip installation:

```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="padel-research",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Algarve Padel Field Market Research Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/padel-research",
    packages=find_packages(exclude=["tests", "docs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.1.0",
        "googlemaps>=4.10.0",
        "streamlit>=1.27.0",
        # ... other dependencies from requirements.txt
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "padel-collect=scripts.collect_data:main",
            "padel-process=scripts.process_data:main",
        ],
    },
)
```

### 4. Deployment Documentation

Create `docs/DEPLOYMENT.md`:

```markdown
# Deployment Guide

## Deployment Options

### Option 1: Local Installation

See README.md for local setup instructions.

### Option 2: Docker

#### Build and Run
```bash
docker build -t padel-research .
docker run -p 8501:8501 -v $(pwd)/data:/app/data --env-file .env padel-research
```

#### Using Docker Compose
```bash
docker-compose up -d
```

Access at: http://localhost:8501

### Option 3: Cloud Deployment

#### Streamlit Cloud
1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Configure secrets (API keys)
4. Deploy

#### AWS ECS
[Instructions for AWS deployment]

#### Google Cloud Run
[Instructions for GCP deployment]

### Option 4: PyPI Installation

```bash
pip install padel-research
padel-collect
padel-process
streamlit run $(python -c "import padel_research; print(padel_research.__path__[0])")/app/app.py
```

## Production Considerations

### Environment Variables
- Use secrets management (AWS Secrets Manager, GCP Secret Manager)
- Never commit .env files
- Rotate API keys regularly

### Data Storage
- Mount persistent volume for data directory
- Consider cloud storage (S3, GCS) for large datasets
- Backup processed data regularly

### Monitoring
- Set up application monitoring
- Track API usage and costs
- Monitor performance metrics
- Set up error alerting

### Scaling
- Current design: Single-instance deployment
- For multi-user: Consider adding database backend
- For high traffic: Add caching layer (Redis)

## Cost Optimization

### Google API Costs
- Enable caching (default in app)
- Set appropriate cache TTL
- Monitor quota usage
- Consider batch processing

### LLM Costs
- Use cheapest models (gpt-4o-mini, claude-3-5-haiku)
- Cache results
- Only run enrichment when needed
- Estimate: $0.01-0.05 per 100 facilities

## Security Best Practices

1. Never expose API keys in code or logs
2. Use environment variables for all secrets
3. Rotate API keys periodically
4. Restrict API key permissions
5. Use HTTPS in production
6. Implement rate limiting if public-facing
7. Regular security updates for dependencies
```

## Acceptance Criteria

### Docker Deployment
- [ ] Dockerfile builds successfully
- [ ] Docker image runs without errors
- [ ] Streamlit app accessible on port 8501
- [ ] Data volumes mount correctly
- [ ] Environment variables passed correctly
- [ ] Health check works
- [ ] Image size optimized (< 1GB)
- [ ] docker-compose.yml works correctly

### Package Distribution
- [ ] setup.py configured correctly
- [ ] Package installs via pip
- [ ] Console scripts work (`padel-collect`, `padel-process`)
- [ ] Package metadata is accurate
- [ ] README renders on PyPI

### Documentation
- [ ] DEPLOYMENT.md created with all deployment options
- [ ] Docker instructions tested
- [ ] Cloud deployment guides provided
- [ ] Security best practices documented
- [ ] Cost optimization tips included

### Production Readiness
- [ ] Environment variables properly configured
- [ ] Secrets management strategy defined
- [ ] Monitoring approach documented
- [ ] Backup strategy outlined
- [ ] Scaling considerations addressed

## Files to Create

```
Dockerfile                      # Docker container definition
docker-compose.yml              # Docker Compose configuration
setup.py                        # PyPI package setup
docs/DEPLOYMENT.md              # Deployment documentation
.dockerignore                   # Docker build exclusions
MANIFEST.in                     # Package inclusion rules
```

## Testing Requirements

### Docker Testing
- [ ] Build image successfully
- [ ] Run container and access Streamlit
- [ ] Test with mounted volumes
- [ ] Test environment variable passing
- [ ] Test health check endpoint
- [ ] Test image on different platforms (AMD64, ARM64)

### Package Testing
- [ ] Install in clean virtual environment
- [ ] Run console scripts
- [ ] Import package modules
- [ ] Verify all files included
- [ ] Test on different Python versions (3.10, 3.11, 3.12)

### Integration Testing
- [ ] Deploy to test environment
- [ ] Run full pipeline in production-like setup
- [ ] Load testing (if applicable)
- [ ] Security scanning

## Implementation Notes

### Docker Best Practices
- Use multi-stage builds to reduce image size
- Don't include development dependencies
- Use specific Python version (not `latest`)
- Run as non-root user for security
- Cache pip dependencies in separate layer

### PyPI Packaging
- Use setuptools (standard, well-supported)
- Include long description from README
- Specify entry points for CLI commands
- Exclude tests and docs from distribution

### .dockerignore

```
.git
.gitignore
venv/
env/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
data/
docs/
tests/
*.md
!README.md
.env
.env.local
```

## Cloud Deployment Options

### Streamlit Cloud (Recommended for MVP)
**Pros**: 
- Free tier available
- Easy integration
- Automatic deployments

**Cons**: 
- Public by default
- Limited resources

### AWS ECS
**Pros**: 
- Full control
- Scalable
- Private by default

**Cons**: 
- More complex setup
- Costs for compute

### Google Cloud Run
**Pros**: 
- Serverless
- Pay per use
- Auto-scaling

**Cons**: 
- Cold start times
- Configuration complexity

## Success Criteria

- [ ] Application can be deployed via Docker in < 10 minutes
- [ ] Docker image builds in < 5 minutes
- [ ] Package can be installed via pip
- [ ] Console scripts work after installation
- [ ] All deployment options documented
- [ ] Production deployment tested
- [ ] Security best practices followed
- [ ] Cost optimization strategies documented

## Future Enhancements

- Kubernetes deployment (k8s manifests)
- Helm charts for Kubernetes
- CI/CD pipelines (GitHub Actions, GitLab CI)
- Automated testing in deployment pipeline
- Blue-green deployment strategy
- Database backend for multi-user support
- API backend with FastAPI
- Authentication and authorization
- Multi-region deployment

## Related Stories

**Depends On**: All stories (0.0-7.2)

**Completes**: Production readiness track

---

**Note**: This is a post-MVP story. Focus on core functionality first, then add deployment capabilities for production use.

