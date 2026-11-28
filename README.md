# ds-web-main

The main app of `datascience.unocha.org`: the Azure Static Web App `chd-ds-web-main`
(OCHA Centre for Humanitarian Data, Data Science team; Unite Apps `OCHA-0187`).

For now it holds a placeholder: every address sends visitors to
[www.unocha.org](https://www.unocha.org/) with a temporary (302) redirect, until the site
has content of its own. The plan for the site (the landing page, which sites move here
and how) is a proposal in the team knowledge base:
[OCHA-DAP/ds-knowledge-base#869](https://github.com/OCHA-DAP/ds-knowledge-base/pull/869).

## What is here

- `site/`: the root of the site. `staticwebapp.config.json` holds the routing rules: the
  redirect of every other address to www.unocha.org, the AA tracker's folder, and the built-in
  sign-in addresses turned off (the main app is public).
- `scripts/assemble.py`: puts the site together in `_site/` before each deploy: `site/` at the
  root, and the AA tracker's open site in `aa-tracker/` (below).
- `.github/workflows/azure-static-web-apps-orange-coast-043ccba0f.yml`: assembles and deploys
  (see Deploying).

## The AA tracker at `/aa-tracker/`

`datascience.unocha.org/aa-tracker/` serves the open site of the AA tracker
([OCHA-DAP/ds-aa-tracking](https://github.com/OCHA-DAP/ds-aa-tracking)), the same pages and
data as [ocha-dap.github.io/ds-aa-tracking](https://ocha-dap.github.io/ds-aa-tracking/),
which stays its main address for now.

- **How it gets here.** The tracker publishes the list of its open files, each with its size
  and SHA-256 (`open-site-files.json`). `scripts/assemble.py` copies every listed file from
  the tracker's GitHub Pages site and checks it against the list. The password-protected
  `dev/` and `admin/` pages are never in the list; their addresses here redirect to GitHub
  Pages.
- **When.** The workflow checks every 30 minutes and deploys when the tracker's list has
  changed, so a tracker publish shows here within about half an hour (GitHub may start
  scheduled runs late). A push to `main` or a run by hand always deploys.
- **If the tracker can't be read**, or a file doesn't match the list, the copy already live
  here is used instead, and the next scheduled run tries again. (GitHub Pages' CDN keeps files
  for up to 10 minutes, so just after a tracker publish old and new files can mix.) If
  neither copy can be read, nothing is deployed: a deploy replaces the whole app, so one
  without the tracker would remove it. A list that holds a name or entry the script won't
  copy stops the run with an error; it is never worked around, so the copy here can't go
  stale unnoticed.
- **`version.json`** at the root records this repo's commit and the tracker's. A scheduled
  run also deploys when the live commit is older than `main`, so a push whose own run was
  dropped from the queue still goes out.
- **Addresses.** `trailingSlash` is `auto`: `/aa-tracker` redirects to `/aa-tracker/` (the
  pages' relative links need the slash), and `page.html` redirects to `page`, which serves
  the same file.
- **Links into the password pages.** The open pages link to `dev/<page>.html`. Here those
  addresses redirect to the development site's front page on GitHub Pages, not to the page
  itself: a Static Web App redirect can't carry the rest of the address.
- **For now** the folder is a second address. Its pages send `X-Robots-Tag: noindex`, so
  search engines keep the GitHub Pages address. Before it becomes the main address: the
  tracker's page-view counter (it counts only on `ocha-dap.github.io`), its proxy's allowed
  origins, `SITE_URL` for its `llms.txt`, and forwarding pages at the old address.
- GitHub turns off scheduled workflows in a public repo after 60 days without a commit. If
  that happens, the tracker stops updating here until the workflow is turned on again.

## Deploying

The workflow assembles the site (above) and deploys it with the app's deployment token, stored as the secret
`AZURE_STATIC_WEB_APPS_API_TOKEN` of the `production` environment. That environment only
accepts deployments from `main`, so a branch can't use the token, even with an edited copy
of the workflow. If the secret is missing, the run fails.

**The deployment authorization policy is *Deployment token*,** so the token alone is
enough. The portal had set it to *GitHub*, under which Azure only accepts deploys that also
carry GitHub's ID token from the linked repo. Azure refused a plain switch ("Cannot update
policy without providing repository token"); on 2026-11-27, with the app unlinked, it
accepted one that also sent a GitHub token and the build properties (app location `site`,
no workflow generated). The workflow file keeps the name Azure gave it,
`azure-static-web-apps-orange-coast-043ccba0f.yml`.

Changes go through pull requests (`main` accepts no direct pushes): whatever reaches `main`
under `site/` is public, and the workflow on `main` can use the token.

**Where it came from.** TSS created the app in the Azure portal on 2026-11-24. The portal
linked it to `OCHA-DAP/ds-knowledge-base` and put the token in that repo's secrets, so
the knowledge base deployed the placeholder until the deploy moved here. When it moved,
the app was unlinked from that repo (it is linked to none now) and the token was reset,
so the copy in the knowledge base no longer works. The knowledge base's own workflow and
secret for this app are removed separately (OCHA-DAP/ds-knowledge-base#883).

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
