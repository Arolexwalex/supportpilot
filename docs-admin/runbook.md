# RUNBOOK: SupportPilot Issues

## /ask returning errors
1. Check Render's live logs (Render dashboard → your service → Logs).
2. If "authentication error" from Gemini — check if GOOGLE_API_KEY expired or was rotated.
3. If ChromaDB error — check ingestion ran successfully on latest deploy (see startup logs).
4. If rate limit — check whether this is real traffic growth or a runaway caller.

## Slack alert fired
1. Visit https://supportpilot-r3t5.onrender.com/health directly to confirm it's actually down.
2. Check Render dashboard for a failed deploy or crashed service.
3. If Render itself is down, check status.render.com.
4. If unresolved in 15 minutes, redeploy manually from Render dashboard.