# GitHub Branch Protection Setup

Use a ruleset for `main` after the initial project publication.

## Recommended ruleset

1. Open **Settings -> Rules -> Rulesets -> New branch ruleset**.
2. Name it `Protect main` and set enforcement to **Active**.
3. Target the default branch or include `main`.
4. Enable:
   - Restrict deletions.
   - Block force pushes.
   - Require a pull request before merging.
   - Require at least 1 approval.
   - Dismiss stale approvals when new commits are pushed.
   - Require conversation resolution.
   - Require status checks to pass.
   - Require branches to be up to date before merging.
   - Require code scanning results.
5. Add these checks after each has completed successfully at least once:
   - `Lint`
   - `Tests (3.11)`
   - `Tests (3.12)`
   - `Artifact Contract`
   - `CodeQL / Analyze (python)`
   - `pip-audit`
   - `Trivy filesystem`
   - `Trivy image`
6. Restrict bypass permission to the repository administrator only. Use bypass
   only for a documented emergency.

## Merge settings

- Prefer squash merge.
- Delete head branches after merge.
- Keep signed commits optional unless a verified signing workflow is available.
- Do not require deployment for this portfolio repository.

## Security settings

Enable Dependabot alerts, Dependabot security updates, secret scanning,
push protection and private vulnerability reporting when available for the
account and repository.

The first publication was explicitly authorized directly to `main`; subsequent
changes should use this protected pull-request workflow.

