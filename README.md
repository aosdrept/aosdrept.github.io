# AOSD website

The bilingual public website of Asociația Ovidiană a Studenților la Drept,
hosted at [aosdrept.github.io](https://aosdrept.github.io/).

## For content editors

Use the [Romanian guide](https://aosdrept.github.io/admin/) or
[English guide](https://aosdrept.github.io/en/admin/) and the
[Pages CMS editor](https://app.pagescms.org/aosdrept/aosdrept.github.io/main/collection/activities).
Invited members can sign in by email without a GitHub account.

Choose **Add an entry** in **Evenimente și proiecte**. A new draft needs a Romanian
title; leave **Include în versiunea propusă** off until both languages are ready.
Then enable it and click **Save**. That prepares a release for review; it does not
publish it. Existing content changes also require approval. Switching the inclusion
option off removes an activity in the next approved release; it does not retain
an older version of that individual activity in that release.

Dates and links are shared. Romanian and English text must be supplied and reviewed.
The newest featured announcement appears on the homepage; if none is selected,
the most recently published entry is used. The archive groups entries by year.
Technical checks and generation are automatic; publication needs approval.

Saved files and uploads are public on GitHub even before approval and even with
inclusion switched off. Never save private drafts, signatures, personal records
or unapproved photographs. Unused uploads are excluded from the deployed website.
Mark an activity completed only after confirmation; passing its date does not
change its status or close an external registration form. Dates do not schedule
publication. No automatic translation, daily reminder or social posting is configured.

## Administrator review

1. Open the latest [Publish website run](https://github.com/aosdrept/aosdrept.github.io/actions/workflows/publish.yml).
2. Read **Publication review** in its summary. It compares the candidate with the
   last successful live deployment, including all intervening saves. Review the
   linked diff, both languages, photographs, withdrawals and date warnings.
3. Confirm the facts, translations, organiser agreement, image rights and absence
   of private data. Approval covers the **whole website version**, not one entry.
4. Select **Review deployments → github-pages → Approve and deploy**, or **Reject**.
5. After successful deployment, check the public website in both languages.

A newer save cancels a pending release and needs fresh review. The deployment also
checks that its commit is still the head of main before publishing. Rejection or
failed checks leave the last successful deployment online. A future announcement
date produces a warning, not scheduled publication. Date warnings run on saves or
manual workflow runs; they do not send messages or decide an event's outcome.

## Approval and access configuration

The approval gate is a GitHub setting, **not** an editable CMS boolean:

- **Settings → Pages → Build and deployment:** source **GitHub Actions**.
- **Settings → Environments → github-pages:** required reviewer **aosdrept**;
  administrator bypass disabled; deployment branch restricted to **main**.
- Self-review prevention stays off while aosdrept is the sole reviewer, allowing
  that administrator to review their own maintenance releases. Members cannot
  approve through their email-only CMS account. Use individual GitHub accounts
  when designating additional administrators; do not share the owner's password.
- Pages CMS GitHub App is connected to this repository. Its **Collaborators** page
  manages member invitations. No extra invitations are sent by this setup.

Keep the environment rule enabled. Copying the repository files to another
repository does **not** recreate GitHub environment protections; configure them
before publishing there. The editor exposes activities and uploaded photos, not
site code, governing PDFs or legal notices. Its schema is not a substitute for
repository access controls.

Reference: [GitHub deployment approvals](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/review-deployments),
[environment configuration](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments),
[Pages CMS collaborators](https://pagescms.org/docs/configuration/collaborators/).

## Source map

- `.pages.yml`: editor fields, media folder, validation hints and collection list.
- `content/activities/*.json`: one authoritative bilingual entry per activity.
  The filename provides its stable URL fragment; keep existing filenames unchanged.
- `pages/`: page source, including matching `en/` pages and the editor guide.
- `templates/`: announcement and event HTML components.
- `scripts/build.py`: Python standard-library generator, content checks and rich-text sanitisation.
- `scripts/check_site.py`: generated local links, IDs, language anchors and asset checks.
- `scripts/review.py`: immutable release summary, live baseline comparison, date warnings and stale-release protection.
- `tests/`: independent fixtures for content generation and review behavior.
- `.github/workflows/publish.yml`: checks changes; builds main and waits for environment approval before deployment.
- `style.css`, `site.js`: shared, human-readable styling and navigation.
- `assets/`: public brand images, uploaded photographs and self-hosted fonts.
- `documents/`: the four approved association PDFs, used by both languages.
- `COPYRIGHT.txt`: rights notice; font licence in `assets/fonts/OFL.txt`.
- `dist/`: generated public website, ignored by Git. Do not edit it directly.

There is no JavaScript framework, package installation, database or runtime API.
Python 3.9+ builds static HTML before publication. Only public pages, assets and
approved documents go into the deployment artifact; source content stays in GitHub.

## Local preview and checks

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/check_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:8765/`. Rebuild after changes. Check both languages, keyboard
navigation, mobile layout, enlarged text and uploaded-image descriptions.
`node --check site.js` checks JavaScript syntax. The GitHub Actions workflow runs
validation before deployment; it does not commit generated HTML back into the source.

Keep two-space indentation in HTML/CSS/JSON and four-space indentation in Python.
When CSS or JS changes, update its cache version in `pages/`; do not create numbered
copies. Shared section IDs preserve the current section when switching languages.
The navigation breakpoint is `70rem` in both CSS and JS. Preserve visible focus,
usable touch targets, the skip link, reduced-motion support and no-JS navigation.

## Security maintenance

Every HTML page sets a Content Security Policy and a `no-referrer` policy.
Scripts, styles, fonts and images load from this site; inline scripts, embeds,
forms and background connections are blocked. Keep these policies before other
resources in the page head. The generated-site check rejects missing policies,
inline code and unexpected scripts. Revisit the policy deliberately if adding
new features; do not enable `unsafe-inline` to silence an error.

Editor links must use HTTPS (rich text may also contain email links). Photos must
use the editor's local upload paths, with at most six images per activity and
10 MB per image. The build rejects symlinks and checks JPEG, PNG or WebP file
signatures. These checks are not a full image decoder or malware scan. Review
image content and permissions before approval, and keep browsers up to date.

GitHub Actions are pinned to full commit hashes. When updating an action, verify
the new commit against its official repository and release, update the adjacent
version comment, and run the checks before approving deployment. Workflow tokens
have job-specific permissions; checkout does not retain credentials.

The HTML policy does not control who may frame the site: `frame-ancestors` needs
an HTTP response header. Other response headers are managed by GitHub Pages,
not these static files. Do not add ineffective HTML substitutes for headers.

## Documents, collaborators and rights

Replace a public PDF only after its association master has been approved and
checked for private data. Maintain one authoritative version. Never commit private
sources, applications, candidate records or internal association minutes.

The collaboration section names **FDSA only**. Its official logo is self-hosted;
its source and third-party ownership are credited in both rights notices.
Do not add collaborators or imply a general institutional endorsement without approval.

The public website has no analytics, social embeds or submission handling.
The editor is an external service linked from `/admin/`, not embedded in public pages.
Update visitor notices before introducing changes to visitor-data processing.

AOSD reserves the rights it holds in protected material, subject to `COPYRIGHT.txt`.
No general open-source licence is granted for AOSD material. Montserrat retains
its SIL Open Font License; the FDSA logo remains its owner's material.
