# SOP: Adding a New Document to SupportPilot

1. Add the new .txt file (UTF-8 encoded) to docs/.
2. Commit and push to main.
3. CI/CD runs tests automatically; Render redeploys automatically on push.
4. Ingestion re-runs on container start, embedding the new document.
5. Test with a relevant question via the live UI to confirm it's retrievable.