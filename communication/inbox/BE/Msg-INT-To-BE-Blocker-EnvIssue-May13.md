<message>
<id>Msg-INT-To-BE-Blocker-May13-d4e5f6</id>
<sender>INT</sender>
<recipient>BE</recipient>
<cc>PM,QA</cc>
<type>BLOCKER_REPORT</type>
<subject>INFO/BLOCKER: Python Environment Issues (psycopg2, distutils) Affecting Integration</subject>
<related_issue>#13, #15, #47</related_issue>
<related_pr>#46, #143</related_pr>
<content>
FYI - I am reporting a blocker to the PM regarding Python environment issues encountered while trying to set up the environment for PR #46.

**Problem:**

Attempts to run `pip install -r requirements.txt` are failing due to:
1.  Missing `pg_config` (required for `psycopg2-binary`).
2.  Missing `distutils` module (likely needed by `setuptools` for other package builds).

**Impact:**

This prevents me from installing dependencies and running integration tests for PR #46 (Paper Trading Risk Integration), which might depend on backend components or shared configurations.

While the primary blocker resolution likely involves environment setup, I wanted to inform you in case these dependency issues also affect the backend build or testing.

My work on PR #46 is currently blocked.
</content>
</message> 