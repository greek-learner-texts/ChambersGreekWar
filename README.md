# Chamber's The Greek War of Independence

This text is being prepared as part of the [Greek Learner Texts Project](https://greek-learner-texts.org/).

## Contributors

* Seumas Macdonald
* Sarah M. Stephens

## Source

Scan available on Archive.org: https://archive.org/details/in.ernet.dli.2015.13619/page/n1/mode/2up
A cleaner scan can be found in the orig folder. 

## Progress

- OCR complete
- First review of OCR & correction is complete

### Current Work: 

* Collating & formatting supplementary material: endnotes, vocabulary, lemmatization, etc. 

### Changes & Contributions: 

Proofreading of the core text is extremely welcome!!! 

To submit changes:
- Edit the source markdown in `drafts/chambers_ocr.md`.
- Run `scripts/normalize.py` and `scripts/gen_txt.py` to create the GTLP-formatted text files.
- Run `scripts/validate.py` to validate the GLTP format. 
- Run `build-html.py` to build the static site html.
- Open a PR! 

If that sounds difficult, just open an issue in the project and I'll try to make the changes asap. 

### To-Do

* OCR & cleanup work on endnotes & other material 
* Formatting 
* Lemmatization

### Notes on the project so far

The Greek text narrative portion of Chambers' reader is composed of 48 chapters broken up into "parts" of twelve chapters each. The GLTP dot format hierarchy used is `Chapter.Paragraph.Line`. Zero-values in dot notation indicate headings. Parts are _not_ currently tracked in the files themselves but can be considered additional metadata. Chapter titles are included in the format of `XX.00.00`. 

## License

This work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).
