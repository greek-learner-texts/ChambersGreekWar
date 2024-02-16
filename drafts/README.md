Intermediate or helpful checkpoint files can go here. 

`chambers_ocr.md` file is the proofread ocr file.

`chambers_notes_ocr.md` has Chambers' textual notes. Proofreading is complete but the ref tags need to be updated with GLTP ids for linking. 

`greek-english-vocab.md` is proofread vocabulary, in process of being stripped of layout refs and tagged with shortcodes. For the original corrected vocab OCR look in `orig/`.

Checklist: 
- [x] Paragraph & Line numbering appropriately represents the original core text and is in the GLTP format.
- [x] Spelling, accentuation, and punctuation of core text have been updated to match the original text.
- [x] Notes file is OCR corrected.
- [x] Vocab file is OCR corrected.
- [ ] Vocab file is cleaned and marked with shortcodes for analytics and linking (maybe convert to spreadsheet).
- [ ] Core text file has word-level ids to support vocab linking.
- [ ] Create a python script to generate vocab objects for linking.
- [ ] Foreach word in core file, link appropriate vocab object.
- [ ] Foreach note in notes file, link to appropriate line id.
- [ ] Come up with a nice way to render everything as a reader.

Some cleanup stuff that needs to be done (misc. list to track)
- [ ] Fix macrons on vocab
- [ ] Validate vocab - all words have proper spelling, accenting, breathings