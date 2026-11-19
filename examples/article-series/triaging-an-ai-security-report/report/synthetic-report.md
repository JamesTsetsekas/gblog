# SYNTHETIC EXAMPLE REPORT. Not a real vulnerability report, not about any real project.

Written for this exercise in the style of a long, confident, machine-assisted submission. The "minishare" library it describes exists only in this directory.

---

**Title:** Critical remote code execution via path traversal in minishare `download()`

**Summary.** The `download()` function in `minishare` is vulnerable to a severe path traversal that allows an unauthenticated remote attacker to read arbitrary files anywhere on the server and achieve remote code execution. This affects all deployments. CVSS 9.8.

**Details.**

- **C1.** `_safe_path` validates containment with `candidate.startswith(base)`. A string prefix check is not a path containment check, so a directory whose name begins with the base directory's name passes it.
- **C2.** Using `../` sequences an attacker can read any file on disk, for example `../outside/secret.txt`.
- **C3.** If the user supplies an absolute path, `os.path.join` discards the base directory, so `/etc/passwd` can be read directly.
- **C4.** An embedded null byte in the path truncates it at the C layer, bypassing `startswith` entirely. Example: `readme.txt%00/../../public-private/secret.txt`.
- **C5.** The helper `_legacy_read` performs no containment check whatsoever and can read any file.

**Impact.** Full compromise of the host. Reading arbitrary files exposes credentials, which leads to code execution.

**Remediation.** Rewrite the module.

*(Nothing in the original report supplied a runnable reproducer, an affected version list, or a call path from a public entry point to the code in C5.)*
