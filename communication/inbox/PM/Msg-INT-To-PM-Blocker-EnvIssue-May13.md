<message>
<id>Msg-INT-To-PM-Blocker-May13-d4e5f6</id>
<sender>INT</sender>
<recipient>PM</recipient>
<cc>BE,QA</cc>
<type>BLOCKER_REPORT</type>
<subject>BLOCKER: Python Environment Issues Preventing Dependency Installation and Testing (PR #46)</subject>
<related_issue>#13, #15, #47</related_issue>
<related_pr>#46, #143</related_pr>
<content>
I am reporting a blocker preventing progress on tasks related to PR #46 (Paper Trading Risk Integration) and environment verification.

**Problem:**

After merging `develop` into the feature branch (`INT/feature/15-paper-trading-risk-integration`) to incorporate the Werkzeug fix (PR #143), I attempted to install dependencies using `pip install -r requirements.txt`. This failed due to two issues:

1.  **`psycopg2-binary` Build Failure:** The initial attempt failed because `pg_config` was not found, preventing the build of `psycopg2-binary`. This indicates missing PostgreSQL development headers in the environment.
2.  **`distutils` Module Not Found:** After temporarily commenting out `psycopg2-binary` to proceed, the installation failed again, this time with `ModuleNotFoundError: No module named 'distutils'`. This error occurred during the build process for other packages (likely pandas/numpy via setuptools) and typically happens in Python 3.12+ where `distutils` has been removed from the standard library and needs to be installed separately (usually via `setuptools`).

**Impact:**

- Cannot install required project dependencies.
- Cannot run integration tests (`tests/unit/integration/`) to verify the fix for PR #46.
- Cannot verify WebSocket connectivity using the provided script (`stream_adapter_verification.py`) as it relies on installed dependencies.
- Cannot address the broker API credential configuration task (ENV-5) effectively without a working environment.
- This blocks the completion of PR #46 and hinders the integration testing scheduled for May 12 as per `MAY10_13_TESTING_COORDINATION.md`.

**Resolution Required:**

The core Python environment needs attention:
1.  Ensure PostgreSQL development tools (including `pg_config`) are available in the system PATH.
2.  Ensure `setuptools` is installed and up-to-date in the Python environment to provide `distutils` for packages that require it.

This likely requires intervention from whoever manages the base development environment setup.

Work on Issue #13/#15 (PR #46) and related verification tasks is blocked until the environment issues are resolved.

Estimated effort lost due to blocker: ~1 PU
</content>
</message> 