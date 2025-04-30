<message>
<sender>PM</sender>
<recipient>BE</recipient>
<type>TASK_ASSIGNMENT</type>
<subject>Implement Flask API with webhook endpoint (Issue #2)</subject>
<reference>#2</reference>

I'm assigning you the task of implementing the initial Flask API with a webhook endpoint to receive TradingView alerts as outlined in Issue #2.

**Requirements:**
- Create a basic Flask application structure
- Implement a `/webhook` endpoint that accepts POST requests
- Add initial JSON schema validation for TradingView payloads
- Return appropriate HTTP status codes
- Add basic logging

**References:**
- Trading webhook specification in `trading_webapp_spec.md`
- Architecture document in `/docs/architecture/ARCHITECTURE.md`

Please create a new branch following the naming convention: `BE/feature/2-flask-webhook-api`

Estimated effort: 2 PUs

Let me know if you need any clarification.
</message> 