# AI Coding Agent Instructions

## Project Architecture

This is a **hybrid Django + Playwright testing project** with a specific dual-purpose structure:

- **Root level**: Django backend (`manage.py`, `config/`) for web application
- **`pw_tests/` subdirectory**: Isolated Node.js/Playwright testing suite for E2E testing

This architecture intentionally separates concerns while keeping both components in one repository for development convenience.

## Key Structural Decisions

### Django Backend (`/config/`)
- Uses Django's default project structure with `config` as the project name
- Standard Django 5.2+ configuration in `config/settings.py`
- No custom apps created yet - this appears to be the base Django setup

### Playwright Testing (`/pw_tests/`)
- **Completely separate Node.js project** with its own `package.json`
- Uses TypeScript configuration (`playwright.config.ts`)
- Configured for multi-browser testing (Chromium, Firefox, WebKit)
- HTML reporter enabled by default

## Critical Developer Workflows

### Initial Project Setup
```bash
# Clone repository and initial setup
git clone <repository-url>
cd Tests_Playwright
python -m venv venv                 # Create virtual environment
source venv/bin/activate            # Activate virtual environment
pip install -r requirements.txt     # Install Python dependencies
cp .env.example .env               # Copy environment variables template
# Edit .env file with your specific configuration values
python manage.py migrate           # Setup database
python manage.py createsuperuser   # Create admin user

# Setup Playwright
cd pw_tests/
npm install                        # Install Node.js dependencies
npx playwright install            # Install browser binaries
cd ..                             # Return to project root
```

### Django Development
```bash
# From project root - ALWAYS activate virtual environment first
source venv/bin/activate                              # Activate Python virtual environment (REQUIRED)
cp .env.example .env                                  # Copy environment template (first time only)
python manage.py migrate                             # Apply database migrations
python manage.py createsuperuser                     # Create admin user
python manage.py runserver                           # Start Django dev server
python manage.py import_playwright_results           # Import Playwright test results to dashboard
```

### Playwright Testing
```bash
# Navigate to testing directory first
cd pw_tests/
npx playwright test                 # Run all tests
npx playwright test --headed        # Run with browser UI
npx playwright show-report         # View HTML report
npx playwright install             # Install browser binaries
```

## Project-Specific Patterns

### Directory Navigation
- **Always change to `pw_tests/` directory** before running Playwright commands
- Django commands run from project root
- The testing suite is designed to test the Django application

### Test Organization
- Test files in `pw_tests/tests/` follow `.spec.ts` naming convention
- Example test (`example.spec.ts`) demonstrates basic Playwright patterns

### Configuration Patterns
- Playwright config uses conditional CI settings (`process.env.CI` checks)
- Trace collection enabled only on first retry for performance
- Multi-browser testing configured but can be reduced for development

## Integration Points

### Django ↔ Playwright Integration
- Playwright tests are designed to test the Django web application
- No direct integration - tests run against deployed Django server
- Consider adding `baseURL: 'http://localhost:8000'` to Playwright config for Django testing

### Development Workflow
1. Start Django server: `python manage.py runserver`
2. In separate terminal: `cd pw_tests && npx playwright test`
3. View results in `pw_tests/playwright-report/`

## File Structure Quick Reference

**IMPORTANT**: Always update this structure when creating new files or directories to maintain accurate project documentation.

```
├── manage.py                          # Django entry point
├── .env                              # Environment variables (DO NOT COMMIT)
├── .env.example                      # Environment template (safe to commit)
├── requirements.txt                  # Python dependencies
├── config/                           # Django project settings
│   ├── settings.py                  # Main Django configuration
│   └── urls.py                      # URL routing
├── testing_dashboard/                # Django app for test result visualization
│   ├── models.py                    # Database models (TestRun, TestCase, TestSuite)
│   ├── views.py                     # Dashboard views and logic
│   ├── admin.py                     # Django admin configuration
│   ├── urls.py                      # App URL patterns
│   ├── templates/                   # HTML templates with Tailwind CSS
│   │   └── testing_dashboard/
│   │       ├── base.html           # Base template with navigation
│   │       └── dashboard.html      # Main dashboard view
│   ├── management/commands/         # Custom Django management commands
│   │   └── import_playwright_results.py  # Import test results from JSON
│   └── migrations/                  # Database migrations
├── pw_tests/                        # Playwright testing suite (separate Node.js project)
│   ├── package.json                # Node.js dependencies
│   ├── playwright.config.ts        # Playwright configuration with JSON reporter
│   ├── tests/                      # Test files (.spec.ts)
│   │   └── example.spec.ts         # Example test
│   ├── test-results/               # JSON results (imported by Django)
│   │   └── results.json            # Generated by JSON reporter
│   └── playwright-report/          # Generated HTML reports
└── venv/                           # Python virtual environment
```

## Common Gotchas
- Don't run `npm` commands from project root - they belong in `pw_tests/`
- Activate Python virtual environment before Django commands: `source venv/bin/activate`
- Playwright browser binaries need separate installation: `npx playwright install`

## Maintenance Instructions for AI Agents
- **Always update** the `File Structure Quick Reference` section when creating new files or directories
- **Document new patterns** in `Project-Specific Patterns` if introducing new conventions
- **Add new commands** to `Critical Developer Workflows` if they become essential to the project
- **Update integration points** if adding new connections between Django and Playwright
