# Delivering the bundle

Anything that others can see (a push, an issue, a copy on a shared server) happens only after the user confirms. Show them exactly what will be sent and where.

## Zip (chat apps, email, cloud drive)

```bash
python -c "import shutil; shutil.make_archive('<task-slug>-brief', 'zip', '.', '<task-slug>-brief')"
```
Report the file size. If it is over ~25 MB, something large slipped past the manifest; move it to manifest-only.

## Git branch + GitHub issue (receiver works in the same repo)

1. Branch from the commit the task starts at: `git switch -c brief/<task-slug>`.
2. Put the bundle's docs at `briefs/<task-slug>/` (the included files are already in the repo, so the manifest can point to their paths instead of copies).
3. Commit, then, **after the user confirms**, push and open an issue:
   ```bash
   git push -u origin brief/<task-slug>
   gh issue create --title "<task title>" --body-file briefs/<task-slug>/START_HERE.md --assignee <handle>
   ```
4. Give the user the issue URL to send.

For a receiver without repo access, a secret gist works for the documents only: `gh gist create --desc "<title>" <files>` (secret by default; anyone with the link can read it).

## Shared server or cluster

1. Copy the bundle to a shared location the receiver can read, e.g. `/lab/shared/briefs/<task-slug>/`.
2. Check permissions: `ls -ld` on each directory in the path and `ls -l` on the files; group-readable (`g+r`, and `g+x` on directories) for the shared group. Don't `chmod` anything outside the bundle.
3. Manifest-only data that is already on the server can be referenced in place. Check that the receiver can read it rather than copying it.
4. Give the user the path to send.
