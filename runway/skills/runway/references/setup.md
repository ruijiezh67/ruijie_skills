# Setup: record the rate-limit windows

`pace.py` needs samples. Claude Code passes the live rate-limit windows only to
the status line command, so `snap.py` runs as the status line, saves a sample
to `~/.claude/runway/samples.jsonl` and prints a short status line.

Requirements: a claude.ai Pro or Max subscription (the `rate_limits` field is
absent on API keys), Python 3 on PATH.

The user edits `~/.claude/settings.json` themselves (it is outside the
project):

```json
{
  "statusLine": {
    "type": "command",
    "command": "python /absolute/path/to/runway/skills/runway/scripts/snap.py",
    "refreshInterval": 300
  }
}
```

`refreshInterval` keeps samples coming while a session is idle. If a status
line already exists, keep it and add `snap.py` as a second line, or have the
existing script pipe its stdin to `snap.py`.

The first sample appears after the first model response in a session. Samples
are about 120 bytes. At most one unchanged sample is written per 5 minutes,
so a full day of use is roughly 35 KB.

Without the status line: ask the user to run `/usage` and paste the numbers.
Plan from those, and say the burn rate is unknown.
