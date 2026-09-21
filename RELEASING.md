# Releasing EditableFlask

## One-time PyPI setup

In the PyPI project settings for `EditableFlask`, add a Trusted Publisher with:

- Owner: `MahirShah07`
- Repository: `EditableFlask`
- Workflow: `publish.yml`
- Environment: `pypi`

Create a matching GitHub environment named `pypi`. Requiring approval for that
environment is recommended so an accidental tag cannot publish a release.

## Publish a release

1. Update the version in `pyproject.toml` and `EditableFlask/__init__.py`.
2. Add the release notes to `CHANGELOG.md`.
3. Merge the change after CI passes.
4. Create and push the matching tag, for example `v2.0.0`.

The `Publish to PyPI` workflow builds the wheel and source distribution,
validates both with Twine, and uploads them using short-lived OIDC credentials.
