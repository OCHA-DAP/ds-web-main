# ds-web-main

The main app of `datascience.unocha.org`: the Azure Static Web App `chd-ds-web-main`
(OCHA Centre for Humanitarian Data, Data Science team; Unite Apps `OCHA-0187`).

For now it holds a placeholder. Once deployed, every address sends visitors to
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
*Deployment token*, so the token alone is enough.

Changes to `site/` go through pull requests: whatever reaches `main` under `site/` is public.

**Moved here on 2026-11-27.** Until then the knowledge base repo deployed the placeholder,
because the Azure portal had linked the app to that repo and put the token in its secrets
when TSS created the app on 2026-11-24. The token was reset when the deploy moved here, so
the copy in the knowledge base no longer works.

**If the token stops working** (reset in Azure, for example): someone with Contributor on
the app reads the new one and stores it without printing it:

```sh
az staticwebapp secrets list -n chd-ds-web-main -g IMB-CHD-DataScience-EastUS2 \
  --query properties.apiKey -o tsv \
  | gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN -R OCHA-DAP/ds-web-main --env production
```

Then run the workflow by hand from `main`.
