## Summary

<!-- Brief description of what this PR does and why -->

## Changes

-

## Checklist

### General
- [ ] PR title is concise and descriptive
- [ ] No secrets, credentials, or API keys are committed

### Python (backend)
- [ ] `ruff check` passes with no warnings
- [ ] New/changed endpoints have tests and all pass with `pytest`
- [ ] Pydantic models are used for request/response validation

### TypeScript (frontend)
- [ ] `npm run check` passes with no type errors
- [ ] No `any` types introduced without justification
- [ ] UI changes tested in at least one modern browser

### Terraform (infrastructure)
- [ ] `terraform fmt -check` passes
- [ ] `terraform validate` passes
- [ ] Plan output reviewed — no unintended resource destroys or replacements
