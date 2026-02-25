# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

French PGO Auctions Dashboard — a web application with a Python backend and Vue.js frontend for managing/displaying auction data.

## Tech Stack

- **Backend**: Latest stable Python, async-friendly libraries preferred
- **Frontend**: Latest stable Vue.js, responsive and mobile-friendly
- **Database**: PostgreSQL for actual development; SQLite for proof-of-concept or quick mock-ups

## Project Structure

```
src/
  backend/    # Python backend
  frontend/   # Vue.js frontend
tests/        # Test suite
docs/         # Documentation
```

## Development Rules

### Python
- Always use a virtual environment. If not using one, ask before installing anything.
- Follow PEP8 style. Always use double quotes for strings.
- Check for linting errors before committing or marking a task complete.

### Local Services
When starting local services in development, print the service name, port, and PID.

### Data
Never delete live data.

## PR Checklist

Before committing: lint, type check, and unit tests must all be green.
