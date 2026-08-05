# References {#sec:references}

Bibliography lives in [`manuscript/references.bib`](references.bib) and is read
by Pandoc with `--natbib` during PDF render. Every key cited in the prose
resolves there, and the cross-reference test
(`tests/test_manuscript_formalisms.py`) fails the build if one does not.

The sources cited in this manuscript are [@bond_ops] (the package identity
record), the gate toolchain [@pytest], [@coveragepy], [@ruff] and [@mypy], and
the figure stack [@matplotlib] with the colourblind-safe palette of
[@wong2011].

The four toolchain entries are software records rather than dated
publications: they carry no publication year because the versions that matter
are the ones pinned in this package's `uv.lock`, not a release date.
