# AOSD website

The public, bilingual website of Asociația Ovidiană a Studenților la Drept.
Hosted on [GitHub Pages](https://aosdrept.github.io/), from the `main` branch and repository root.

## File map

- `index.html`: Romanian homepage.
- `en/index.html`: English homepage.
- `evenimente.html`, `en/evenimente.html`: bilingual events and projects record.
- `privacy.html`, `copyright.html`: Romanian visitor and rights notices.
- `en/privacy.html`, `en/copyright.html`: matching English notices.
- `style.css`: shared styles, grouped by component, followed by responsive rules.
- `site.js`: optional navigation, focus and language-switch enhancements.
- `assets/`: the association’s images, favicon and self-hosted Montserrat fonts.
- `documents/`: the four approved association PDFs, shared by both languages.
- `COPYRIGHT.txt`: repository rights notice. The font licence is `assets/fonts/OFL.txt`.
- `.nojekyll`: tells GitHub Pages to serve the static files directly.

## Editing

There is no framework, build step or runtime dependency. Edit the HTML, CSS and
JavaScript directly. Use two-space indentation and keep the existing formatting.
Update the Romanian and English pages together; corresponding sections use the
same IDs so language switching preserves the current section.
The official social links appear in the opening section and in Contact; keep
both locations in both languages in sync when a profile address changes.

Content and navigation work without JavaScript. The mobile menu uses a disclosure
button, not an application-style ARIA menu. Its breakpoint is `70rem` in both
`style.css` and `site.js`; change both if the layout changes. The script keeps the
mobile links after the toggle in DOM order, restores focus on Escape, and moves
focus to the selected section. The desktop header offset follows its actual height.

Sizes use `rem` so browser text preferences are respected. Preserve visible focus,
usable touch targets, the skip link and reduced-motion support when editing.
The current layout has been checked at 320px and with enlarged text; this is not
a claim of full WCAG conformance or a screen-reader audit.

Keep a single stylesheet and script. When either changes, update its `?v=` cache
version in all HTML pages; do not add numbered copies of the assets. Their
history remains available in Git.

## Announcements, events and collaborators

The homepage’s `#noutati` section features one dated announcement and links to
`evenimente.html`. Each event has a stable anchor, an explicit status, dates,
participation details and links to its public sources. Keep the summary and
full record consistent in both languages. Record when the information was checked.
Use absolute deadlines rather than an undated “registration open” label.

When a new announcement is featured, keep earlier event records on the events
page in reverse chronological order, grouped by year. Update changes or
cancellations from the organiser’s public communications. Do not mark an event
completed just because its date has passed; add a report or selected photographs
only once verified and cleared for publication. Do not add invented entries,
private minutes, participant lists or unapproved images to fill the archive.

The homepage’s `#colaborari` section currently names FDSA only, in the context of
the announced moot court. Keep institution names and roles accurate; do not imply
a general endorsement or add collaborators without association approval.
Registration links lead to external organiser forms; there is no embedded form
or submission handling in this repository.

## Preview and release

From this directory, run:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/`. Before publishing, check both languages, keyboard
navigation, mobile menu opening/closing, footer links, PDFs, and layout at narrow
widths and 200% text size. `node --check site.js` checks JavaScript syntax.
Commit the changes, push `main`, then check the Pages deployment in GitHub Actions.
No package installation is needed to preview or publish.

## Documents and privacy

Replace a public PDF only after its association master has been approved and
checked for private data. Maintain one authoritative version. Never commit
unredacted sources, applications, review files or internal association records.

Update both visitor notices before introducing features that change personal-data
processing. The applicant/member privacy PDF has a separate purpose and remains
in the Documents section. Do not add analytics, remote fonts or embedded social
widgets without updating the applicable information and controls.

## Rights

AOSD reserves the rights it holds in protected material, subject to the qualifications
in `COPYRIGHT.txt`. No general open-source licence is granted. Montserrat retains
its SIL Open Font License 1.1 and author notice. Published PDFs remain usable for
the information and membership purposes described in the rights notice.
