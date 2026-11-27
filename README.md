# ds-web-main

The main app of `datascience.unocha.org`: the Azure Static Web App `chd-ds-web-main`
(OCHA Centre for Humanitarian Data, Data Science team; Unite Apps `OCHA-0187`).

For now it holds a placeholder: every address sends visitors to
[www.unocha.org](https://www.unocha.org/) with a temporary (302) redirect, until the site
has content of its own. The plan for the site (the landing page, which sites move here
and how) is a proposal in the team knowledge base:
[OCHA-DAP/ds-knowledge-base#869](https://github.com/OCHA-DAP/ds-knowledge-base/pull/869).

## What is here

- `site/`: what the app serves. `staticwebapp.config.json` holds the redirect and turns
  off the built-in sign-in addresses, since the main app is public.
- `.github/workflows/deploy.yml`: deploys `site/` to `chd-ds-web-main` when a change to
  `site/` or the workflow reaches `main`, or when run by hand from `main`.

## Deploying

`.github/workflows/deploy.yml` deploys `site/` with the app's deployment token, stored as
the secret `AZURE_STATIC_WEB_APPS_API_TOKEN` of the `production` environment. That
environment only accepts deployments from `main`, so a branch can't use the token, even
with an edited copy of the workflow. The app's deployment authorization policy is
*Deployment token*, so the token alone is enough. If the secret is missing, the run fails.

Changes to `site/` go through pull requests: whatever reaches `main` under `site/` is
public, and anyone who can push to `main` can use the token.

**Where it came from.** TSS created the app in the Azure portal on 2026-11-24. The portal
linked it to `OCHA-DAP/ds-knowledge-base` and put the token in that repo's secrets, so
the knowledge base deployed the placeholder until the deploy moved here. When it moved,
the token was reset, so the copy in the knowledge base no longer works.

**If the token stops working** (reset in Azure, for example): someone with Contributor on
the app reads the new one and stores it without printing it, checking it isn't empty:

```sh
TOKEN=$(az staticwebapp secrets list -n chd-ds-web-main -g IMB-CHD-DataScience-EastUS2 \
  --subscription OCHA-PROD --query properties.apiKey -o tsv) \
  && [ -n "$TOKEN" ] \
  && printf '%s' "$TOKEN" | gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN -R OCHA-DAP/ds-web-main --env production
unset TOKEN
```

Then run the workflow by hand from `main`, and check that its *Deploy* step ran.
