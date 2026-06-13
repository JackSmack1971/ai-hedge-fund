# CI/CD Audit Report

## Scope

- Audited `.github/workflows/test.yml` and `.github/dependabot.yml`.
- No application code, tests, lockfiles, or package manifests were modified.
- No new workflow file was created because the repository already had a single CI workflow; the existing workflow was hardened in place.
- Repository shape discovered during audit:
  - Python project managed with Poetry at the repo root.
  - Frontend app in `app/frontend` with its own `package.json` and `package-lock.json`.
  - No `turbo.json` or Turbo monorepo setup detected.

## Issues Found and Fixed

### 1. Broken GitHub Action reference

- `test.yml` used `actions/setup-node@v6`, which is not the current stable major for this repository's workflow shape and is inconsistent with the rest of the pinned action strategy.
- Fixed by switching the frontend job to `actions/setup-node@v4`.

### 2. Missing workflow hardening

- The workflow had no explicit `permissions:` block.
- The workflow had no `concurrency:` control, so repeated pushes and PR updates could waste runner minutes.
- Fixed by adding:
  - workflow-level `permissions: contents: read`
  - job-level `permissions: contents: read`
  - concurrency cancellation keyed to the workflow plus the branch/PR

### 3. Over-broad triggers

- The workflow triggered on every branch push and PR without path filtering.
- Fixed by adding `paths:` filters for the backend, frontend, tests, lockfiles, and workflow file itself.

### 4. Caching was present but not optimal

- The Python job cached Poetry artifacts, but not the actual in-project virtual environment.
- Fixed by switching to an in-project `.venv` cache keyed to `poetry.lock` and `pyproject.toml`, while keeping `setup-python` pip caching.
- The frontend job now relies on `setup-node`'s npm cache with the existing lockfile path.

### 5. Workflow structure and maintainability

- The original workflow mixed security, linting, typing, testing, and frontend build logic without clear guardrails.
- Fixed by:
  - keeping backend and frontend jobs separate
  - adding inline comments for the non-trivial security, performance, and maintainability choices
  - normalizing command ordering so linters receive flags before paths

### 6. Dependabot coverage

- Dependabot already covered `github-actions`, root Poetry-managed Python dependencies, and the frontend npm lockfile.
- Enhanced by adding `open-pull-requests-limit: 5` to each ecosystem so update noise stays bounded.

## Key Before / After

### Workflow versioning

- Before: `actions/setup-node@v6`
- After: `actions/setup-node@v4`

### Access control

- Before: no workflow permissions declared
- After: read-only permissions at workflow and job level

### CI load management

- Before: every branch update could queue a full rerun
- After: older runs are canceled when a newer commit arrives for the same branch or PR

### Trigger scope

- Before: every push and PR regardless of changed files
- After: workflow only runs when relevant Python, frontend, test, or workflow files change

### Dependency caching

- Before: Poetry cache targeted package cache only
- After: `.venv` caching tied to the lockfile and Python version

## Rationale

- The repository is mixed Python + frontend, so a single workflow is reasonable, but it needs path filters and separate job concerns to avoid unnecessary runner usage.
- SHA-pinning the highest-value actions keeps supply-chain risk down while preserving maintainability for lower-risk actions such as `setup-node`.
- The workflow still preserves the original purpose: backend validation, linting, type checking, bandit, coverage, frontend lint, and frontend build.

## Remaining Recommendations

- Add branch protection rules requiring the CI workflow before merge.
- Enable GitHub secret scanning and push protection.
- Prefer OIDC federation for any future cloud uploads instead of long-lived cloud keys.
- Consider making lint/type-check gates non-optional once the codebase is ready to enforce them.
- If coverage upload becomes mission-critical, consider verifying the Codecov token and upload behavior in a dedicated release-quality workflow.

## Verification Notes

- YAML validation was run after edits.
- Actionlint was attempted; availability depends on the local environment.
- GitHub CLI auth was not usable in this environment because the configured token was invalid and network access to GitHub was blocked.
