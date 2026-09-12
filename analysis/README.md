Token-level analysis like lemmatisation or postagging can go here.

[Link to google sheet w/ lemmatization in progress](https://docs.google.com/spreadsheets/d/1u0OokpNZQAOxcr0HQaTV1Sk9LifvG8mpWWqNjylh-xY/edit?usp=sharing).

## Automatic lemmatisation runs

`text/chambers.txt` (12,032 tokens) run through several lemmatisers so the
outputs can be compared. Scripts live in `scripts/lemmatize/`.

| file | tool | notes |
| --- | --- | --- |
| `tokens.txt` | – | `index ref form normalised`; the token list every run shares |
| `lemmas-morpheus.txt` | [Morpheus](https://github.com/perseids-tools/morpheus-perseids-api) | no disambiguation: first of all possible analyses; every analysis is in `raw/morpheus.jsonl` |
| `lemmas-cltk.txt` | [CLTK](https://github.com/cltk/cltk) 1.5 default Greek pipeline (OdyCy spaCy model) | contextual tagger |
| `lemmas-cltk-stanza.txt` | CLTK `GreekStanzaProcess` (Stanza, Perseus treebank) | contextual tagger |
| `lemmas-dilemma.txt` | [Dilemma](https://github.com/open-greek/dilemma) 1.2 tagger + lemmatiser | contextual tagger |
| `lemmas-compare.txt` | – | side by side lemma/POS per token, `Y`/`N` agreement flag |
| `lemmas-majority.txt` | – | one row per token by majority vote over the four (ties → dilemma › cltk-stanza › morpheus › cltk); vote details in `raw/majority.jsonl` |
| `raw/<tool>.jsonl` | – | the tool's own output per token (UD features, deprels, all Morpheus analyses…) |

### Format of `lemmas-<tool>.txt`

One token per line, space separated, MorphGNT-style codes:

```
index form normalised pos parse form-parse lemma
15 ἐστιν), ἐστίν V- 3PAI-S-- ------- εἰμί
```

* `form` – as printed, punctuation attached
* `normalised` – `greek-normalisation` output (grave → acute, elision and
  movable-nu resolved, lowercased unless the lemma is a proper noun)
* `pos` – `N-` noun, `V-` verb, `A-` adjective/numeral, `RA` article, `RP`
  personal pronoun, `RD` demonstrative, `RR` relative, `RI`
  interrogative/indefinite, `D-` adverb, `C-` conjunction, `P-` preposition,
  `X-` particle, `I-` interjection, `--` unknown
* `parse` – 8 columns: person, tense (`P I F A X=perfect Y=pluperfect`),
  voice (`A M P`), mood (`I D=imperative S O N=infinitive P=participle`),
  case, number, gender, degree (`C S`); `-` when not applicable / not given
* `form-parse` – always `-------` here (in MorphGNT this is the
  form-level parse; none of these tools produce it)
* `lemma` – `-` when the tool gave nothing

The tools' native tag sets are converted to these codes in
`scripts/lemmatize/common.py` (UD features) and `run_morpheus.py`
(Morpheus vocabulary); anything a tool does not report is `-`.

### Re-running

```
python -m venv .venv && .venv\Scripts\activate
pip install greek-normalisation cltk
pip install "dilemma-nlp[onnx,tagger-onnx] @ git+https://github.com/open-greek/dilemma.git"
python -m dilemma download            # ~5.5 GB into ~/.cache/dilemma
docker run -d --name morpheus -p 1500:1500 perseidsproject/morpheus-perseids-api:latest

cd scripts/lemmatize
python make_tokens.py
python run_morpheus.py                # caches API responses in analysis/raw/morpheus-cache.json
python run_cltk.py                    # spaCy/OdyCy; see docstring for installing the model wheel
python run_cltk.py stanza             # downloads the Stanza grc model on first run
python run_dilemma.py
python compare.py --disagree 30
python majority.py
```

Set `PYTHONUTF8=1` on Windows so the scripts can print Greek.
