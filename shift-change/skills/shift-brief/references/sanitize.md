# Sanitizing a bundle

Everything in the bundle leaves the user's control once sent. Check each included file and each document you wrote.

| Look for | How to find it | Do |
|---|---|---|
| API keys, tokens, passwords | grep: `(?i)(api[_-]?key|secret|token|passw(or)?d|bearer)\s*[:=]`, `sk-[A-Za-z0-9]{20,}`, `ghp_[A-Za-z0-9]{30,}`, `AKIA[0-9A-Z]{16}`, `-----BEGIN .*PRIVATE KEY-----`, `hf_[A-Za-z0-9]{30,}` | remove; point to where the receiver gets their own |
| `.env`, credential files | filenames: `.env*`, `*.pem`, `*.key`, `credentials*`, `*.netrc`, `id_rsa*` | never include; ship `.env.example` with placeholder values |
| Absolute paths with usernames | `/Users/<name>/`, `/home/<name>/`, `C:\Users\<name>\`, `~` expansions in configs | make repo-relative, or `<DATA_DIR>` placeholders documented in START_HERE |
| Internal hosts and URLs | hostnames, IPs, internal dashboards, private repo URLs | keep only if the receiver has access; otherwise describe what it is |
| Personal or private notes | comments and notes with opinions about people, unpublished results not meant for this receiver, grades, reviews | remove; ask the user when unsure |
| Personal data in datasets | names, emails, IDs in included data samples | exclude or use synthetic samples; flag to the user |
| Hidden history | `.git/` folders, notebook outputs with old results, `__pycache__`, editor backups | exclude; strip notebook outputs if they contain anything above |

Before finishing, run one last grep over the whole bundle for the secret patterns and the user's username, and report the result ("0 matches" or the fixes made).
