
## 2026-10-15 LaTeX builds
- Pattern: I counted warnings in a stale main.log/PDF and called the build clean; a literal "\n" in a caption had actually broken it.
- Rule: delete main.pdf before building, check the build's exit code, and grep the PDF text for "[?]". Never trust a log/PDF without confirming it is newer than main.tex.
- Rule: a number quoted from a table must come from a table built by the CURRENT code (check file mtimes against the code edits); recompute when in doubt.
