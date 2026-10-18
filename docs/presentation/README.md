# Project Presentation Deliverables

The sample attachment was not accessible in this session. These files therefore use
a standard 20-slide bachelor's-project structure rather than claiming to match an
unseen institutional template.

## Files

- [PROJECT_PRESENTATION.pptx](PROJECT_PRESENTATION.pptx): editable 16:9 slide deck with
  actual notebook charts, an architecture diagram, tables, and speaker notes.
- [PROJECT_PRESENTATION.docx](PROJECT_PRESENTATION.docx): editable A4 Word companion,
  organized by slide with charts, tables, and presenter notes. Import into Google Docs.
- [PROJECT_PRESENTATION.md](PROJECT_PRESENTATION.md): Markdown version for manual
  formatting in Google Docs, including relative chart links and presenter notes.
- [content.json](content.json): the shared text source for all three formats.
- `assets/`: PNG charts extracted from the verified executed synthetic-data notebook.

Student names, register numbers, programme, guide, institution, academic year, date,
and institutional logo are bracketed placeholders. There are no invented students,
supervisors, experimental participants, commercial comparisons, or literature-review claims.
The references point to the project's actual tools and repository.

The deck separates strong synthetic categorization results from weak anomaly precision,
states the synthetic-data limitations, and does not claim Docker runtime verification.
Cloud infrastructure appears only as deferred future scope, not current implementation.

## Edit or Regenerate

Office exports are already generated; opening them does not require Python. Edit the
PPTX in PowerPoint/Google Slides or import the DOCX into Google Docs. Presenter notes
are in the PPTX Notes pane and explicitly labelled in the Word/Markdown companions.
The Word file is a slide-organized companion, not an institution-certified thesis report.

For reproducible regeneration, install presentation tools in a separate environment;
they are not dependencies of the finance runtime. Run from the clone root:

```powershell
py -3.14 -m venv .venv-presentation
.\.venv-presentation\Scripts\python.exe -m pip install -r docs/presentation/requirements.txt
.\.venv-presentation\Scripts\python.exe scripts/build_presentation.py
```

Use `python3.14`, `.venv-presentation/bin/python`, and the same arguments on macOS/Linux.
This optional environment is excluded by the root Git ignore rules. The exporter needs
`outputs/finance_demo.executed.ipynb`; if absent, create it using the project's normal
environment and `python scripts/execute_notebook.py` before exporting.

Edit `content.json` before regeneration to preserve placeholder replacements. Rebuilding
overwrites the exported PPTX, DOCX, Markdown, and chart assets. Direct edits made only in
Office exports are not imported back into the JSON source. The text records the verified
seed-42 five-year experiment; if the dataset or modelling changes, update numerical claims
in the source as well as regenerating the charts. The exporter expects the current five
chart outputs in notebook order.

No sample-layout fidelity is claimed until an accessible sample is supplied. Office files
were structurally checked by reopening them. Microsoft PowerPoint rendered all 20 slides
to preview images; title, architecture, table, and model-chart layouts were visually
inspected. Microsoft Word reported 20 pages for the 20 slide sections. Pagination can
still vary with application and installed fonts, so preview the chosen application
before final submission.