"""Describe a proposed release against the last live deployment for its reviewer.

The report is informational. GitHub's protected github-pages environment enforces
approval; no field in Pages CMS can grant it. Uses only Python's standard library.
"""
import argparse
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    from . import build
except ImportError:
    import build


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root).decode("utf-8")


def github_api(path):
    request = Request("https://api.github.com/" + path, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def live_revision(repository, api=github_api):
    """Skip pending/rejected releases; compare with the version actually online."""
    page = 1
    while True:
        deployments = api(f"repos/{repository}/deployments?environment=github-pages&per_page=100&page={page}")
        if not deployments:
            return None
        for deployment in deployments:
            statuses = api(f"repos/{repository}/deployments/{deployment['id']}/statuses?per_page=1")
            if statuses and statuses[0]["state"] == "success":
                return deployment["sha"]
        page += 1


def saved_entries(root, revision):
    if not revision:
        return {}
    paths = git(root, "ls-tree", "-r", "--name-only", revision, "content/activities").splitlines()
    return {path: json.loads(git(root, "show", f"{revision}:{path}"))
            for path in paths if path.endswith(".json")}


def entry_changes(before, after, changed_paths):
    changes = []
    for path in sorted(before.keys() | after.keys()):
        old, new = before.get(path, {}), after.get(path, {})
        old_visible, new_visible = old.get("visible", False), new.get("visible", False)
        photos_changed = any(photo.get("image", "").lstrip("/") in changed_paths
                             for photo in new.get("photos") or [])
        if old == new and not photos_changed:
            continue
        if old_visible and not new_visible:
            status = "Retras de pe site / Removed from website"
        elif new_visible:
            status = "Actualizat / Updated" if old_visible else "Adăugat / Added"
        else:
            status = "Ciornă exclusă / Draft excluded"
        changes.append((path, status, new or old, new_visible))
    return changes


def timing_notes(entry, now):
    notes = []
    deadline = entry.get("registration_deadline")
    if deadline and build.parse_date(deadline, True) < now and entry["status"] not in ("completed", "cancelled"):
        notes.append("Termenul de înscriere a trecut; verifică linkul și textul. / Registration deadline has passed; review the link and wording.")
    end = entry.get("end_date") or entry.get("date")
    if end and build.parse_date(end) < now.date() and entry["status"] in ("announced", "ongoing"):
        notes.append("Data activității a trecut; confirmă stadiul. / Activity date has passed; confirm its status.")
    if build.parse_date(entry["published_date"]) > now.date():
        notes.append("Data anunțului este în viitor; nu programează publicarea. / Announcement date is in the future; it does not schedule publication.")
    return notes


def report(root, repository, base, head, now=None):
    now = now or datetime.now(build.BUCHAREST)
    entries = build.load_entries(root)
    before, after = saved_entries(root, base), saved_entries(root, head)
    changed_paths = set(git(root, "diff", "--name-only", base, head).splitlines()) if base else set(git(root, "ls-tree", "-r", "--name-only", head).splitlines())
    changes = entry_changes(before, after, changed_paths)
    repo_url = f"https://github.com/{repository}"
    lines = ["# Verificare înainte de publicare / Publication review", "",
             f"Versiune / Revision: `{head}`. Activități incluse / Included activities: **{len(entries)}**.", "",
             "Această versiune nu este aprobată prin salvarea în editor. Administratorul verifică întregul lot și alege **Review deployments → github-pages → Approve and deploy** sau **Reject**.", "",
             "Saving in the editor does not approve this release. Review the whole batch, then approve or reject the deployment. A newer save replaces a pending review; review that new version again.", "",
             "Verifică / Check: corectitudinea informațiilor și traducerilor; datele și linkurile de înscriere; acordul organizatorilor; drepturile asupra imaginilor și absența datelor private. / Facts and translations; dates and registration links; organiser approval; image rights and absence of private data.", ""]
    if base:
        lines += [f"[Modificări față de versiunea live / Changes since the live version]({repo_url}/compare/{base}...{head})", ""]
    else:
        lines += ["Nu există o versiune live identificată; verifică toate fișierele. / No live baseline found; review all files.", ""]
    lines += ["## Modificări de conținut / Content changes", ""]
    if not changes:
        lines += ["Nicio modificare a activităților. Verifică mai jos celelalte fișiere. / Activities are unchanged. Review other changed files below.", ""]
    for path, status, entry, included in changes:
        title = entry.get("ro", {}).get("title") or Path(path).stem
        file_revision = head if path in after else base
        lines += [f"### {escape(status)}", f"<p><strong>{escape(title)}</strong></p>",
                  f"[Fișierul exact / Exact file]({repo_url}/blob/{file_revision}/{quote(path)})", ""]
        if included:
            rendered_entry = {**entry, "id": Path(path).stem}
            for lang in build.LANGUAGES:
                html = build.event_html(rendered_entry, lang)
                html = html.replace('src="/assets/uploads/', f'src="https://raw.githubusercontent.com/{repository}/{head}/assets/uploads/')
                html = html.replace('src="assets/uploads/', f'src="https://raw.githubusercontent.com/{repository}/{head}/assets/uploads/')
                lines += [f"<details><summary>{lang.upper()}</summary>", "", html, "", "</details>", ""]
    lines += ["## Verificări de timp / Time-sensitive checks", "",
              f"Evaluate la / Evaluated at: {now.isoformat(timespec='minutes')} (Europe/Bucharest).", ""]
    notices = [(entry, note) for entry in entries for note in timing_notes(entry, now)]
    for entry, note in notices:
        lines.append(f"<p><strong>{escape(entry['ro']['title'])}</strong>: {escape(note)}</p>")
    if not notices:
        lines.append("Nicio atenționare de dată la această verificare. / No date warnings at this check.")
    lines += ["", "Aceste atenționări nu schimbă automat stadiul, înscrierile sau data publicării. / These warnings do not change status, registration or publication timing automatically.", "",
              "## Toate fișierele modificate / All changed files", ""]
    for path in sorted(changed_paths):
        lines.append(f"<p>{escape(path)}</p>")
    lines += ["", "## Activități incluse / Included activities", ""]
    for entry in entries:
        path = f"content/activities/{entry['id']}.json"
        lines.append(f"<p>{escape(entry['ro']['title'])} / {escape(entry['en']['title'])}</p>\n\n[RO + EN]({repo_url}/blob/{head}/{path})\n")
    result = "\n".join(lines) + "\n"
    if len(result.encode("utf-8")) > 950_000:
        raise ValueError("Review report too large. Reduce the proposed batch before publication.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Explicit comparison revision for local review")
    parser.add_argument("--head", default=os.environ.get("GITHUB_SHA", "HEAD"))
    parser.add_argument("--output", default=os.environ.get("GITHUB_STEP_SUMMARY"))
    parser.add_argument("--check-current", action="store_true")
    args = parser.parse_args()
    repository = os.environ.get("GITHUB_REPOSITORY", "aosdrept/aosdrept.github.io")
    head = git(build.ROOT, "rev-parse", args.head).strip()
    if args.check_current:
        if github_api(f"repos/{repository}/commits/main")["sha"] != head:
            raise ValueError("A newer version exists. Review and approve its run instead.")
        return
    base = args.base or live_revision(repository)
    result = report(build.ROOT, repository, base, head)
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()
