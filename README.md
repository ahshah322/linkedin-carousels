# linkedin-carousels

Public PDFs for Ali Husnain Shah's LinkedIn carousel posts (posted via Buffer).

- `template/` the 5 finished slide files (cover, concept A, concept B, comparison, call to action). Copy them to a work folder, change only the text, code and table for the new topic, keep the styling.
- `assets/` C# logo, violet .NET logo, profile photo used by the slides.
- `tools/render.py` renders a folder of slide files to a PDF: `npm install` then `python3 tools/render.py <slides_dir> <out_pdf>` (needs google-chrome and Pillow).
- `dotnet/` finished PDFs, one per topic, e.g. `dotnet/class-vs-struct.pdf`. Buffer reads them through the raw.githubusercontent.com link.
