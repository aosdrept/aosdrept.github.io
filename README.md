# AOSD website

The bilingual public website of Asociația Ovidiană a Studenților la Drept,
hosted at [aosdrept.github.io](https://aosdrept.github.io/).

## For content editors

Open the [editor guide](https://aosdrept.github.io/admin/) and follow its link to
[Pages CMS](https://app.pagescms.org/). Choose `aosdrept.github.io` on `main`, then
**Evenimente și proiecte**. Add an entry, complete the shared details and both
language sections, and save. Enable **Publică pe site** when it is ready.

The website generates the homepage announcement and the events archive from the
same entry. No HTML, Git commands or local software are needed for routine editing.
Dates and links are shared. Romanian and English text must be supplied and reviewed.
The newest featured announcement appears on the homepage; if none is selected,
the most recently published entry is used. Entries are grouped by year in the archive.

All saved files and uploads are public in the GitHub repository, even with
**Publică pe site** switched off. That switch controls website visibility only.
Never save private drafts, personal data, signatures or unapproved photographs.
Mark an activity completed only after verification; passing its date does not
change its status automatically. For cancellation, select **Anulat** and explain
in both languages. Hiding an entry preserves its file and stable link for reuse.
Renaming and deletion are disabled in the activity editor to avoid accidental loss.

The editor does not expose governing PDFs, legal notices or site layout as content
fields. Media uploads are restricted to `assets/uploads/`; that is an editor
configuration, not a replacement for GitHub access controls.

## One-time connection

1. In repository **Settings → Pages → Build and deployment**, choose
   **GitHub Actions** as the source. The `Publish website` workflow builds and deploys `dist/`.
2. Sign into [Pages CMS](https://app.pagescms.org/) with the account that owns the
   repository. Install its GitHub App for **only `aosdrept.github.io`**.
3. Open the repository's `main` branch. `.pages.yml` defines the bilingual editor.
4. Invite approved editors through Pages CMS if needed. Invitations and access
   changes require the association owner's decision; no invitations are sent by this setup.
5. Open the existing event, verify that both language sections and dates load,
   and check the live site after a save. A failed build leaves the last successful
   deployment online; correct the field identified in the workflow's error message.

Connection documentation: [Pages CMS quick start](https://pagescms.org/docs/quick-start/),
[collaborators](https://pagescms.org/docs/configuration/collaborators/),
[GitHub Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Source map

- `.pages.yml`: editor fields, media folder, validation hints and collection list.
- `content/activities/*.json`: one authoritative bilingual entry per activity.
  The filename provides its stable URL fragment; keep existing filenames unchanged.
- `pages/`: page source, including matching `en/` pages and the editor guide.
- `templates/`: announcement and event HTML components.
- `scripts/build.py`: Python standard-library generator, content checks and rich-text sanitisation.
- `scripts/check_site.py`: generated local links, IDs, language anchors and asset checks.
- `tests/test_build.py`: independent fixtures for publishing behavior, not real association data.
- `.github/workflows/publish.yml`: checks every pull request; builds and deploys `main`.
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
