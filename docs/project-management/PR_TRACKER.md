# Pull Request Tracker

## Current Status (as of May 13, 2025)

We are in the final testing phase before our scheduled release. This document tracks all pull requests and their status.

## PRs Ready for Merge

| PR # | Title | Branch | Creator | Status | Reviewers | Priority |
|------|-------|--------|---------|--------|-----------|----------|
| #139 | [PM] Add environment documentation | PM/docs/merge-environment-docs | curworkv9 | Open (1/2 checks failing) | - | High |
| #138 | [PM] Update release documentation | PM/docs/release-readiness-may10 | curworkv9 | Open (1/2 checks failing) | - | High |
| #136 | [BE] Update communication files | BE/fix/integration-logger-warning-method | curworkvvv | Open (1/2 checks failing) | PM, INT, QA | High |
| #135 | docs(qa): update PR tracker | QA/docs/update-pr-tracker-env-verification | - | Open (1/2 checks failing) | - | Medium |
| #134 | docs(testing): add environment verification | QA/docs/135-env-verification-steps | - | Open (1/2 checks failing) | - | Medium |

## Critical PRs In Progress

| PR # | Title | Branch | Creator | Status | Blockers | Priority |
|------|-------|--------|---------|--------|----------|----------|
| #46 | INT: Integrate Risk Management | INT/feature/15-paper-trading-risk-integration | - | Open (failing tests) | Test failures | Critical |
| #132 | feat(integration): Implement WebSocket | INT/feature/15-risk-market-data-websocket | - | Open | - | High |
| #130 | feat(integration): Add WebSocket | INT/feature/46-risk-websocket-implementation | - | Open | - | High |
| #128 | fix(integration): Update werkzeug | INT/fix/46-werkzeug-dependency-fix | - | Open | - | High |

## Recently Merged PRs

| PR # | Title | Branch | Merged Date | Associated Issues |
|------|-------|--------|-------------|-------------------|
| #91 | Health Check Endpoints | - | May 7, 2025 | #45 |
| #90 | UI Component Enhancements | - | May 7, 2025 | #38 |
| #87 | Broker Configuration Fixes | - | May 6, 2025 | #22 |
| #40 | Backend Risk Management | - | May 5, 2025 | #15 |
| #36 | Dashboard Order Tracking | - | May 4, 2025 | #12 |

## Merge Plan (May 13)

1. Merge documentation PRs first (#138, #139, #135, #134)
2. Address failing checks on BE PR #136
3. Focus team efforts on fixing the critical INT PR #46
4. After INT PR #46 is fixed, merge dependency fix PR #128
5. Then proceed with WebSocket implementation PRs (#130, #132)

## PR Status Definitions

- **Ready for Merge**: Approved, all tests passing
- **Needs Review**: PR is complete but waiting for review
- **In Progress**: Work is ongoing
- **Blocked**: Cannot proceed due to dependencies or issues 