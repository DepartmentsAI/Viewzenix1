# Branch Cleanup Instructions

The following Git commands should be executed to clean up the merged branches listed in `/communication/inbox/PM/branches-to-delete.md`.

## Local Branch Cleanup

```bash
# Switch to develop branch
git checkout develop
git pull origin develop

# Delete local branches that have been merged
git branch -d BE/communication/may8-testing-response
git branch -d BE/communication/may8-testing-response-v2
git branch -d BE/communication/may8-testing-response-v3
git branch -d BE/communication/testing-phase-may8
git branch -d BE/feature/10-order-execution-engine
git branch -d BE/feature/15-risk-management
git branch -d BE/feature/15-risk-management-system
git branch -d BE/feature/2-flask-webhook-api
git branch -d BE/fix/environment-issues

git branch -d FE/communication/release-readiness-confirmation
git branch -d FE/communication/testing-comms-update
git branch -d FE/communication/testing-phase-support
git branch -d FE/docs/ui-documentation
git branch -d FE/docs/ui-documentation-and-messages
git branch -d FE/docs/update-pr-tracker
git branch -d FE/docs/update-pr-tracker-2
git branch -d FE/feature/12-dashboard-order-tracking
git branch -d FE/feature/3-react-dashboard-foundation
git branch -d FE/fix/frontend-environment

git branch -d INT/feature/13-paper-trading-adapter
git branch -d INT/feature/4-alpaca-adapter

git branch -d QA/feature/14-order-execution-tests
git branch -d QA/feature/15-risk-management-tests
git branch -d QA/feature/5-e2e-test-framework
git branch -d QA/task/environment-readiness-may8
git branch -d QA/task/update-pr-tracker
git branch -d QA/task/webhook-test-fixtures
git branch -d QA/test/environment-readiness-check
git branch -d QA/test/final-testing-prep

git branch -d PM/chore/emergency-env-fix-docs
git branch -d PM/chore/update-pr-tracker
git branch -d PM/chore/update-pr-tracker-20
git branch -d PM/chore/update-user-stories-status
git branch -d PM/communication/int-pr-feedback
git branch -d PM/docs/update-decision-log
git branch -d PM/feature/release-prep
git branch -d PM/feature/user-stories
git branch -d PM/fix/pr-tracker-update
git branch -d PM/task/15-risk-management-assignments
git branch -d PM/task/assignments-may3
git branch -d PM/task/final-testing-prep-may8
git branch -d PM/task/issue-updates-may5
git branch -d PM/task/may8-cleanup
git branch -d PM/task/may8-pr-updates
git branch -d PM/task/may8-testing-emergency
git branch -d PM/task/merge-branches-batch1
git branch -d PM/task/next-steps-may7
git branch -d PM/task/release-update-may6
git branch -d PM/task/update-pr-tracker
git branch -d PM/task/update-pr-tracker-batch1
git branch -d PM/task/update-pr-tracker-merged-prs
git branch -d PM/update/pr-tracker-may7
git branch -d PM/task/branch-cleanup-may8
```

## Remote Branch Cleanup

```bash
# Delete remote branches
git push origin --delete BE/communication/may8-testing-response
git push origin --delete BE/communication/may8-testing-response-v2
git push origin --delete BE/communication/may8-testing-response-v3
git push origin --delete BE/communication/testing-phase-may8
git push origin --delete BE/feature/10-order-execution-engine
git push origin --delete BE/feature/15-risk-management
git push origin --delete BE/feature/15-risk-management-system
git push origin --delete BE/feature/2-flask-webhook-api
git push origin --delete BE/fix/environment-issues

git push origin --delete FE/communication/release-readiness-confirmation
git push origin --delete FE/communication/testing-comms-update
git push origin --delete FE/communication/testing-phase-support
git push origin --delete FE/docs/ui-documentation
git push origin --delete FE/docs/ui-documentation-and-messages
git push origin --delete FE/docs/update-pr-tracker
git push origin --delete FE/docs/update-pr-tracker-2
git push origin --delete FE/feature/12-dashboard-order-tracking
git push origin --delete FE/feature/3-react-dashboard-foundation
git push origin --delete FE/fix/frontend-environment

git push origin --delete INT/feature/13-paper-trading-adapter
git push origin --delete INT/feature/4-alpaca-adapter

git push origin --delete QA/feature/14-order-execution-tests
git push origin --delete QA/feature/15-risk-management-tests
git push origin --delete QA/feature/5-e2e-test-framework
git push origin --delete QA/task/environment-readiness-may8
git push origin --delete QA/task/update-pr-tracker
git push origin --delete QA/task/webhook-test-fixtures
git push origin --delete QA/test/environment-readiness-check
git push origin --delete QA/test/final-testing-prep

git push origin --delete PM/chore/emergency-env-fix-docs
git push origin --delete PM/chore/update-pr-tracker
git push origin --delete PM/chore/update-pr-tracker-20
git push origin --delete PM/chore/update-user-stories-status
git push origin --delete PM/communication/int-pr-feedback
git push origin --delete PM/docs/update-decision-log
git push origin --delete PM/feature/release-prep
git push origin --delete PM/feature/user-stories
git push origin --delete PM/fix/pr-tracker-update
git push origin --delete PM/task/15-risk-management-assignments
git push origin --delete PM/task/assignments-may3
git push origin --delete PM/task/final-testing-prep-may8
git push origin --delete PM/task/issue-updates-may5
git push origin --delete PM/task/may8-cleanup
git push origin --delete PM/task/may8-pr-updates
git push origin --delete PM/task/may8-testing-emergency
git push origin --delete PM/task/merge-branches-batch1
git push origin --delete PM/task/next-steps-may7
git push origin --delete PM/task/release-update-may6
git push origin --delete PM/task/update-pr-tracker
git push origin --delete PM/task/update-pr-tracker-batch1
git push origin --delete PM/task/update-pr-tracker-merged-prs
git push origin --delete PM/update/pr-tracker-may7
git push origin --delete PM/task/branch-cleanup-may8
```

**Note**: Some branches might not be present locally or might be protected from deletion. If you encounter errors, continue with the next command. Force deletion with `-D` instead of `-d` may be required if a branch hasn't been fully merged. 