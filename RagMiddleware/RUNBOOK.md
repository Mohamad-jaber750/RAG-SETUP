# RAG Middleware Runbook

## Python RAG API Is Down

1. Confirm the Python service health directly at `GET http://127.0.0.1:8000/api/health`.
2. Check middleware logs for upstream timeout or 5xx warnings.
3. Verify `RagApi:BaseUrl` points to the active Python API host.
4. Restart the Python API if local; escalate to the RAG API owner if shared infrastructure is down.
5. Tell UI users that RAG responses are temporarily unavailable; do not expose upstream stack traces.

## Rotate RAG API Credential

1. Create the new API key/token in the Python RAG API owner system.
2. Update `RagApi:BearerToken` or `RagApi:ApiKey` in User Secrets, environment variables, or Key Vault.
3. Restart the middleware service if the deployment does not reload configuration.
4. Verify `POST /api/chat` succeeds through the middleware.
5. Revoke the old credential after the new value is confirmed working.

## Revoke Google OAuth Secret

1. Rotate the OAuth client secret in Google Cloud Console.
2. Update `Authentication:Google:ClientSecret` in User Secrets, environment variables, or Key Vault.
3. Restart the middleware service.
4. Test `GET /api/auth/login/google` from a clean browser session.
5. Record the rotation date and reason in the team security log.

## Audit Log Retention

Keep audit logs for 90 days by default unless legal/compliance requirements say otherwise. Export or archive older logs before deletion if the team needs incident history.
