# ds-web-main

The main app of `datascience.unocha.org`: the Azure Static Web App `chd-ds-web-main`
(OCHA Centre for Humanitarian Data, Data Science team; Unite Apps `OCHA-0187`).

For now it holds a placeholder. Every address sends visitors to
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

**For now the placeholder is deployed from the knowledge base repo, not from here.** When
TSS created the app in the Azure portal on 2026-11-24, the portal put its deploy key in the
secrets of `OCHA-DAP/ds-knowledge-base`, and nobody on the team can read the key from Azure
yet. So the KB's workflow `azure-static-web-apps-orange-coast-043ccba0f.yml` deploys the same
placeholder. **To move here:** once the key can be read from Azure, copy it into this repo's
secret `AZURE_STATIC_WEB_APPS_API_TOKEN`, run this repo's deploy, and delete the KB's
workflow and its `AZURE_STATIC_WEB_APPS_API_TOKEN_*` secrets.

The workflow needs the app's deploy key in the repo secret
`AZURE_STATIC_WEB_APPS_API_TOKEN`. Without it, the run skips the deploy and shows a
warning.

Changes go through pull requests. Whatever reaches `main` is public at once.
