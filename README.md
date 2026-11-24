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

**For now the placeholder is deployed from the knowledge base repo, not from here.** When
TSS created the app in the Azure portal on 2026-11-24, the portal linked it to
`OCHA-DAP/ds-knowledge-base` and put its deployment token in that repo's secrets. Nobody
on the team can read the token from Azure yet, so the KB's workflow
`azure-static-web-apps-orange-coast-043ccba0f.yml` deploys the same placeholder.

**To move the deploy here** (needs Contributor on the app):

1. Switch the app's deployment authorization policy from *GitHub* to *Deployment token*
   (portal: Settings > Configuration > Deployment configuration). Under *GitHub*, deploys
   are checked against the repo the app is linked to (the KB), so a deploy from here may
   be refused. If the setting can't be changed, the fallback is to recreate the app with
   no repo link; its default hostname would then change, and so would the DNS record and
   custom domain for `datascience.unocha.org`.
2. Reset the deployment token (Azure portal: Overview > Manage deployment token), so the
   copy in the KB stops working. In this repo, create the environment `production` with
   deployment branches limited to `main`, and store the new token there as the
   environment secret `AZURE_STATIC_WEB_APPS_API_TOKEN`. A branch then can't use the
   token, even with an edited copy of the workflow.
3. Remove the *Get an ID token* step and the `github_id_token` input from the workflow;
   they are only needed under the *GitHub* policy.
4. Run the deploy, check the redirect, then delete the KB's workflow and its
   `AZURE_STATIC_WEB_APPS_API_TOKEN_*` secrets, and unlink the app from the KB.

Until the token is set, the workflow skips the deploy and shows a warning. Changes to
`site/` should go through pull requests: once the token is set, whatever reaches `main`
under `site/` is public.
