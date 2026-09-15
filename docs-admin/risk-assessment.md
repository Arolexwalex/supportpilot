# Risk Assessment: SupportPilot

Data handled: Fictional help-center docs (low sensitivity); real user questions (treat as sensitive)
Third-party exposure: Questions sent to Google's Gemini API — governed by Google's API data policy
Cost risk: Mitigated by rate limiting (10/minute) and Gemini's free-tier caps
Container security: Base image (python:3.13-slim) scanned via Docker Scout; rebuilt periodically for patches
Residual risk accepted: No automated CI image scanning yet; personal/learning project scope