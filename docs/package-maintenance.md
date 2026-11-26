# Maintain the bond-ops package

[Project metadata](../pyproject.toml) declares the package identity and Python
compatibility (`>=3.12`). [The lockfile](../uv.lock) records resolved
dependencies. Compare these two files when checking package metadata.

The package declares PyYAML and Matplotlib as runtime dependencies.
The package metadata has no local path dependency overrides.

## Citation and release records

[Citation metadata](../CITATION.cff), [CodeMeta](../codemeta.json), and
[Zenodo metadata](../.zenodo.json) describe this package. Check the
version fields that are present against the project metadata. A repository
metadata file does not establish that a release has been deposited.

For a documentation review, run `git diff --check` and verify the relative
links added by the change against the tracked checkout. These checks
provide evidence about the documentation and package records.
