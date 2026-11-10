# IEEE PES GM 2027 submission checklist

Source: https://pes-gm.org/2027-san-francisco/2027-call-for-papers/ (read 2026-11-09).

## Key facts
- Deadline: CONFLICT between official pages. pes-gm.org/2027-san-francisco/2027-call-for-papers/ says 13 November 2026; pes-gm.org/2026-montreal/program-at-a-glance/2027-call-for-papers/ says 10 November 2026. No time zone. Treat 10 November 2026 as the deadline.
- Portal: https://submissions.mirasmart.com/PESGM2027 (MIRA system; one CFP page links a PESGM2026 path, so confirm the 2027 link opens the 2027 call). Raheel creates the account, fills the fields and clicks submit.
- Length: max 5 pages, prepared per the PES Authors Kit (ieee-pes.org). Our PDF: 4 pages, IEEE conference format, letter size, all fonts embedded.
- Decision: "by mid March 2027".
- Conference: 25-29 July 2027, San Francisco. One author must register and pay, and the paper must be presented (usually a poster); unpresented papers are not put in IEEE Xplore.

## Files
- PDF to upload: `paper/main.pdf` (rebuild: `.venv/bin/python -m src.paper && cd paper && rm -f main.pdf && tectonic -X compile main.tex`).

## Portal fields (fill in; exact fields are only visible inside MIRA)
- Title: Predict the Breach, Not the Drop: Control-Aligned Learning for Smoothing AI Training Power Swings
- Author: Sayed Raheel; affiliation and email as on the PDF (confirm before submitting).
- Abstract: copy from the PDF abstract (shorten if MIRA has a word limit).
- Keywords: data centers; AI workloads; ramp rate; load forecasting; power smoothing; energy storage
- Topic: closest Super Session theme is "Large Dynamic Loads on Power System Security".
- Paper type: conference paper (not a Transactions paper, not Part 1/Part 2).
- Copyright form: IEEE electronic copyright, normally after acceptance.

## Before clicking submit
- [ ] Codex review READY (reports/review/pesgm_codex_r1_2026-11-09.md) and fixes applied
- [ ] Author line and email confirmed
- [ ] Open the final PDF and read it once
- [ ] Check the PES Authors Kit for template specifics (margins, PDF eXpress)
