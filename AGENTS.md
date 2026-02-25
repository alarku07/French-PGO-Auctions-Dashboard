# Project directory
- ignore blackboard.md file

# Data
- Never delete live data

# Development
## Local
- In development when starting local services, print out service name, port and PID of the service
- serve backend on port 8000
- serve frontend on port 3000

# GitHub
## PR checklist
- lint, type check, unit tests - all green before commit

# Tech Stack
- Back-end in latest stable version of Python and FastAPI
- Front-end in latest stable version of Vue.js
- PostgreSQL for database

# Docker
- ALWAYS create and run servies in docker image as regualar non-root user

# Python
- ALWAYS use virtual environment for managing python libraries except for Docker images
- When not using virtual environment ALWAYS ask whether to proceed with installation
- Use PEP8 code style
- ALWAYS use double quotes for strings
- always check for linting errors before commiting code or marking task as complete
- prefer async-friendly libraries
- virtual environment is in .venv folder. ALWAYS ignore the content of .venv directory

# Vue.js
- webpages must be responsive and mobile-friendly
- use Composition API
