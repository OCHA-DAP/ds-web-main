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

The workflow needs the app's deploy key in the repo secret
`AZURE_STATIC_WEB_APPS_API_TOKEN`. Without it, the run skips the deploy and shows a
warning.

Changes go through pull requests. Whatever reaches `main` is public at once.
