# Azure SRE Agent interactive demo

This is a self-contained, Storylane-style walkthrough for Azure SRE Agent. It uses HTML scenes rather than product screenshots, so it can be reviewed and hosted without a build step.

## Run locally

Open `index.html` directly, or serve the repository:

```powershell
python -m http.server 8000
```

Then browse to `http://localhost:8000/interactive-demo/`.

## GitHub Pages

The repository workflow in `.github/workflows/sre-agent-interactive-demo-pages.yml`
publishes this directory as a standalone GitHub Pages site:

`https://vyomnagrani.github.io/Azure/`

For an official Microsoft experience, use an approved `aka.ms` link as the
stable public entry point.

## Publish with Azure Static Web Apps

Azure Static Web Apps is the better choice when the demo needs a custom domain, deployment environments, authentication, access restrictions, or Azure-native monitoring. Configure the app location as `interactive-demo` and leave the API location empty.

## Add real screenshots or video

The current scenes are safe mock representations of the product journey. To use real media:

1. Capture a stable lab run at one consistent resolution.
2. Redact tenant, subscription, identity, and incident identifiers.
3. Replace a scene's inner markup with an `<img>` or `<video>` element.
4. Preserve the scene's `data-title`, `data-kicker`, `data-description`, and `data-takeaway` attributes.

Use short video only where motion adds meaning: alert arrival, investigation progress, topology generation, mitigation execution, and verification.
