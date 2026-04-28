# AGENTS.md

Guide for coding agents working in `ciip-api`.

This file keeps agent behavior consistent across branches, PRs, migrations, tests, and CI for the **Collaborative Information and Innovation Portal (CIIP)** — a centralized digital platform serving youth across Kyrgyzstan.

---

## 1) Non-Negotiable Workflow

- Never start feature work directly on `main`.
- Always create or switch to a dedicated feature branch first.
- Use the repo branch prefix `codex/` unless the user asks for a different naming scheme.
- Keep scope tight. Do not mix unrelated fixes into the same branch unless they are required to make the branch pass.
- Open a PR for feature work.
- Stay with the branch until CI checks are green. If checks fail, fix them instead of stopping after the first implementation.

---

## 2) Definition of Done

A change is not done until all of the following are true:

- Relevant unit tests were added or updated first, then implementation was brought up to make them pass.
- `pre-commit run --all-files` passes.
- `pytest -q` passes, or a narrower test command is used first and then expanded appropriately.
- If migrations changed, `alembic upgrade head` was validated against real Postgres, not just mocked tests.
- The branch is clean and the diff only contains task-relevant changes.

---

## 3) Database and SQL Guidance

- Prefer native SQL and explicit queries over introducing ORM-heavy abstractions.
- For new backend behavior, prefer `asyncpg` queries in controllers and service helpers.
- Keep SQL readable, explicit, and close to the business logic.
- Use Alembic migrations as the schema source of truth.
- When writing migrations, make them portable to vanilla Postgres. CI validates migrations against standard Postgres, not only Supabase.
- Be careful with schema-qualified inserts and deletes. This repo uses `APP_SCHEMA` and migrations must respect it.
- Be careful with Postgres defaults and SQL expressions. Use `sa.text(...)` where appropriate instead of relying on implicit ORM behavior.
- If seed data is added in migrations, make sure it targets the configured schema and works in a real `alembic upgrade head` run.

### CIIP-specific data notes

- Core entities include: `users`, `posts`, `categories`, `opportunities`, `institutions`, `moderation_queue`.
- The `moderation_queue` table tracks pending content submissions. Do not bypass it for institution- or admin-submitted content without explicit authorization logic.
- Category scoping matters: content is tagged by audience (`high_schoolers`, `university_students`, `general_public`). Always include audience filters in queries that surface portal listings.
- Opportunity types (`internship`, `job`, `course`, `volunteer`, `event`) are stored as a Postgres enum. New types require a migration — do not use free-text strings.

---

## 4) Testing Strategy

- Default to test-first for feature work:
  - Add or update the unit test.
  - Run the smallest relevant test.
  - Implement the feature or fix.
  - Expand to nearby tests.
  - Finish with the full relevant suite.
- Prefer small targeted runs first, then broader runs:

```bash
pytest -q tests/unit/path_to_test.py::test_name
pytest -q tests/unit/test_module.py
pytest -q
```

- If CI fails, reproduce the exact failing workflow locally when possible.
- For migration changes, do not trust only import-level or mocked migration tests. Run a real Postgres migration path.
- Moderation and role-gating logic (admin, moderator, institution, user) must be covered by tests. Never ship a new endpoint without at minimum a happy-path and an unauthorized-access test.

---

## 5) Linting and Formatting

- Linting is part of the task, not optional cleanup.
- Run:

```bash
pre-commit run --all-files
```

- The repo uses `ruff`, `ruff-format`, markdownlint, and standard pre-commit hooks.
- If pre-commit rewrites files, review the rewritten diff and rerun until it passes cleanly.

---

## 6) Repo-Specific Architecture Notes

- Stack: FastAPI + asyncpg + Alembic + Supabase Auth.
- Main app entrypoint: `app/main.py`
- Config model: `app/utils/config.py`
- Routers: `app/ciip_api/routers/v1/`
- Business logic lives primarily in `app/controllers/`
- Shared helpers can live in `app/services/`
- Migrations: `migrations/`
- Tests: `tests/`

Important runtime details:

- `request.app.state.pool` is the shared Postgres pool.
- `request.app.state.redis` is the optional Redis client (used for moderation queue notifications and caching opportunity listings).
- The app sets Postgres `search_path` to `APP_SCHEMA`, but migrations and SQL should still be explicit where needed.

### Role model

The platform has four roles enforced at the application layer via Supabase Auth claims:

| Role          | Description                                              |
|---------------|----------------------------------------------------------|
| `admin`       | Full access; can approve/reject moderators and content   |
| `moderator`   | Can approve or reject posts in the moderation queue      |
| `institution` | Can submit verified opportunities on behalf of an org    |
| `user`        | Default; can browse and apply to listed opportunities    |

Always check the role claim from the decoded JWT. Do not rely on user-supplied body fields for role.

---

## 7) CI Snapshot

Current workflows live in `.github/workflows/`:

- `linting.yml`
- `unit-tests.yml`
- `deploy.yml`

What matters most for feature work:

- Linting runs `pre-commit` on GitHub Actions with Python `3.12`.
- Unit tests run on GitHub Actions with Python `3.12`.
- Unit-test CI starts:
  - Postgres `16`
  - Redis `7`
- CI runs:

```bash
alembic upgrade head
pytest
```

Do not assume local success is enough if you skipped migrations or skipped pre-commit.

---

## 8) Local Commands

Useful commands in this repo:

```bash
pip install -r requirements.txt
make start_redis
POSTGRES_URL='postgresql://...' alembic upgrade head
uvicorn app.main:app --reload
pytest -q
pre-commit run --all-files
```

If `python` is not available locally, use `python3`.

---

## 9) Change Discipline

- Read the surrounding code before editing.
- Match existing patterns unless there is a good reason to improve them.
- Do not add a new abstraction layer if explicit code is clearer.
- Do not introduce SQLAlchemy ORM-style data access for new features unless the user explicitly asks for it.
- Keep migrations small and reviewable.
- Keep commits logically grouped.
- Do not revert unrelated user changes.
- When adding or changing API endpoints, update the FastAPI/Scalar docs in the same branch.
- For business endpoints shown in `/reference`, prefer route descriptions with these short sections:
  - `Auth:` whether a bearer token is required and which Supabase token to send.
  - `Business requirement:` what product behavior the endpoint supports.
  - `Frontend note:` implementation details or MVP limitations the client team should know.
- Keep the `Auth:` note concise. Prefer a short form like `Use Authorization: Bearer <access_token> from Supabase Auth` instead of repeating the anon-key / service-role-key warning on every endpoint.
- Add request/response examples for new endpoints when they help frontend engineers integrate faster.

### CIIP-specific endpoint conventions

- All public-facing opportunity and post listing endpoints must support pagination (`limit` / `offset`).
- Filtering by `audience`, `category`, and `opportunity_type` should be composable query params, not separate routes.
- Moderation endpoints (`/moderation/approve`, `/moderation/reject`) must be gated to `moderator` or `admin` roles only.
- AI-assisted features (summarization, tagging suggestions) are routed through `app/services/ai_service.py`. Do not inline external AI API calls in controllers.

---

## 10) Recommended Agent Checklist

Before coding:

- Confirm current branch and working tree state.
- Confirm whether the task belongs on a new feature branch.
- Identify the smallest test to add or update first.
- Check whether the change touches migrations, CI-sensitive SQL, or auth/role-gated routes.
- If the change touches the moderation queue or role logic, flag it for extra review.

Before finishing:

- Run `pre-commit run --all-files`
- Run relevant tests, then `pytest -q`
- If migrations changed, run `alembic upgrade head` against Postgres
- Review `git diff --stat` and `git status`
- Make sure the branch is ready for PR and green checks
