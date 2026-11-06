# GoreeCloud Projects — tracked import credential preflight

**Status:** offline regression check on an attributed Plane source import;
not a complete supply-chain or secrets audit. The initial public import and
all production use remain subject to separate security, privacy, licensing,
authorization, and deployment acceptance.

## Scope and method

`tests/test_tracked_import_credential_preflight.py` uses Python's standard
library and `git ls-files -z`. It checks the **currently tracked** source
tree only, without contacting a registry, GitHub API, email service, secret
vault, or network endpoint.

Four focused checks fail on:

1. Tracked private-key-like filenames, personal credential stores, or a
   non-example `.env` file (the imported `.env.example` templates are allowed).
2. Literal private-key block headers or GitHub personal-access-token-like
   markers in small text files.
3. AWS access-key-ID-shaped strings other than the **known public AWS
   documentation example** in the upstream OpenAPI attachment example.
4. Static `.npmrc` auth token assignments instead of environment-variable
   interpolation.

The checks never print token contents; failure messages contain **only
relative tracked paths and line numbers**. Exact marker patterns are limited
to high-confidence shapes to avoid silently blocking the Plane import on
generic variable names and OAuth credential fields.

The source scan skips files larger than 2 MB and files with NUL bytes.
Sensitive filenames are checked independently of content size.

## Actual verification on November 5, 2026

The imported `GoreeCloud/projects` public `main` branch contained
**5,170 tracked paths** at the reviewed commit. Read-only preflight found
seven credential-adjacent configuration filenames, consisting of six
`.env.example` templates and the root `.npmrc`, and no tracked private-key
files of the checked extensions.

A high-confidence text scan found **one AWS-access-key-shaped identifier**.
Targeted readback confirmed it is the **published AWS example ID** within a
`drf-spectacular` `OpenApiExample` describing a sample attachment response
in `apps/api/plane/api/views/issue.py`. Its adjacent policy and signature
fields also contain explicit example placeholders; this is not evidence of
an exposed real key. The example is intentionally allowlisted only at this
specific source path.

No private-key block markers or GitHub PAT-shaped markers were detected
within the tested text-file and size limits.

The four committed Python `unittest` regressions passed **4/4** in a clean
detached GitHub-source checkout, using Python 3 without third-party packages
or network access. These results are limited to the stated marker patterns
and do not prove that all secrets, credentials, runtime values, built
artifacts, current deployments, commit history, or SaaS integrations are safe.

## Limitations and release gates

- **Not** a broad credential detector or entropy scan; only documented
  high-confidence signatures and tracked path classes are covered.
- No scanning of Git history, previous commits, other branches, untracked
  local files, GitHub secrets or cloud config, connected devices, email,
  images, binaries, database dumps, archives, or files over 2 MB.
- URL query params and arbitrary third-party access keys can have formats
  outside the checked patterns; review secrets management separately.
- Dynamic config values, secret rotation, CI/registry token permissions,
  dependency integrity, code execution and business-logic authorization
  are outside this check.
- Treat any future positive as a potential secret; avoid pasting matched
  values in public issues or logs. Confirm whether a finding is a
  documentation sample or actual key, and rotate/revoke through an
  authorized owner if a live key is verified.
- Keep security releases gated on full independent source/dependency review,
  actual Django/PostgreSQL tests, cache/publication revocation, and
  rights-cleared branding.

**Run from the repository root:**

```sh
python3 -m unittest discover -s tests -p 'test_tracked_import_credential_preflight.py' -v
```

No production systems, remote services, workflows or secret stores are
modified by the test.
