# OS DAGGER

Ask U.S. Army doctrine a question and get an answer that cites the publication and the page.

Ten current publications on operations, planning, deployment, movement, sustainment and command, indexed locally. Retrieval runs on your machine with no key. The answer is written by whatever model you point it at: xAI, OpenAI, Anthropic, or a local model through Ollama with nothing leaving the laptop.

Real output, retrieval only, no model, on the shipped index:

```
> python ask.py --retrieve-only -k 3 "What are the responsibilities of a movement control team?"

[1] FM 4-0, p. 111  similarity 0.637  (Sustainment Operations)
operational objectives. During the execution of large-scale combat operations, movement control prioritizes and synchronizes movements to support actions in the division rear, close, and deep areas. ...

[2] ATP 4-16, p. 16  similarity 0.626  (Movement Control)
... Services, nations, governmental and nongovernmental organizations in the employment of forces or sustainment throughout a theater area of responsibility (AOR). 1-27. During large-scale comb...

[3] ATP 4-16, p. 15  similarity 0.586  (Movement Control)
... Within the competition continuum, movement control activities must be prepared to operate across the range of military operations. Movement control provides the ...
```

With a model configured (here, Grok 4.7 through xAI), `python ask.py "What are the tenets of operations?"` gave this, verbatim, on 2026-10-30:

```
The excerpts list two different sets of tenets.

**Tenets of unified land operations** (ADP 5-0, 31 July 2019). Desirable attributes built into
all plans and operations, directly related to the Army's operational concept. Commanders and
staffs incorporate: simultaneity, depth, synchronization, and flexibility [ADP 5-0, p. 49].

**Tenets of operations / multidomain operations** (ADP 3-0, 21 March 2025; FM 4-0, 20 March 2026).
Desirable attributes built into all plans and operations; commanders use them to inform and assess
courses of action. They are: agility, convergence, endurance, and depth [FM 4-0, p. 22] [ADP 3-0, p. 39].
- Agility: ability to move forces and adjust dispositions and activities more rapidly than the
  enemy; critical to protection and enables speed in large-scale combat [FM 4-0, p. 22] [ADP 3-0, p. 39].
- Convergence: creates opportunities against adaptive, resilient enemies by complementary and
  reinforcing Army and joint effects while preserving combat power [ADP 3-0, p. 39].
- Endurance: absorb enemy attacks and sustain operations over the time and space required to
  accomplish the mission [ADP 3-0, p. 39].

...

The excerpts do not define depth, synchronization, or flexibility, and do not complete the
definition of simultaneity.

Sources:
  FM 5-0, p. 33   Planning and Orders Production  (similarity 0.574)
  ADP 5-0, p. 49  The Operations Process          (keyword match)
  FM 4-0, p. 22   Sustainment Operations          (keyword match)
  ADP 3-0, p. 39  Operations                      (keyword match)
  ...
```

Two things in that answer are the point of the tool. It found that the 2019 ADP 5-0 still carries the older tenets while the 2025 ADP 3-0 carries the current four, and said so instead of blending them. And it closed with what the retrieved pages do not say, rather than filling the gap from memory.

## What is in it

| Pub | Title | Edition |
|---|---|---|
| ADP 3-0 | Operations | Mar 2025 |
| ADP 4-0 | Sustainment | 2019, Change 1 Aug 2026 |
| ADP 5-0 | The Operations Process | 2019 |
| AR 525-93 | Army Deployment and Redeployment | Apr 2026 |
| AR 600-20 | Army Command Policy | Apr 2026 |
| ATP 3-35 | Army Deployment and Redeployment | Mar 2023 |
| ATP 4-16 | Movement Control | Apr 2022 |
| FM 4-0 | Sustainment Operations | Mar 2026 |
| FM 5-0 | Planning and Orders Production | Nov 2024, Change 1 Aug 2025 |
| FM 6-0 | Commander and Staff Organization and Operations | May 2022 |

All ten are the editions the Army Publishing Directorate listed as active on 2026-10-30. Hashes and the reasons two other pubs are left out are in [doctrine/SOURCES.md](doctrine/SOURCES.md).

## Run it

Python 3.10 or newer.

```bash
git clone https://github.com/JosephCirello/os-dagger.git
cd os-dagger
python -m venv .venv && .venv\Scripts\activate      # on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python build_index.py                                # two to three minutes on a laptop; first run downloads an 80 MB embedding model
python ask.py --retrieve-only "principles of sustainment"
```

That last command needs no key and shows you the pages the tool would hand to a model. To get written answers, copy `.env.example` to `.env`, fill in one endpoint, and drop the flag:

```bash
python ask.py "What are the responsibilities of a movement control team?"
python ask.py --pub "FM 6-0" "What goes in paragraph 3 of an operation order?"
python ask.py                                        # interactive
```

## How it works

1. `build_index.py` reads each PDF page by page with pypdf, cuts the text into chunks of about 1,500 characters that never cross a page, and stores them in a local [Chroma](https://www.trychroma.com/) collection under `index/`. Embeddings are Chroma's default small model, run locally.
2. `ask.py` runs two searches and fuses them: the question embedded the same way against the vectors, and a BM25 keyword ranking over every chunk (doctrine lives on exact words: "tenets", "OPORD", "TPFDD", which a small embedding model blurs). The best eight by combined rank (change with `-k`) go to the model with one instruction: answer from these excerpts, cite each one as `[Pub, p. N]`, and say so if the excerpts do not answer the question.
3. The page number in a citation is the PDF page, so you can open the file and go straight to it.

The model never sees the whole publication, only what retrieval found, which keeps it honest and keeps the cost per question small.

## Add your own publications

Put a PDF in `doctrine/` named `SERIES_NUMBER_Title_YYYY-MM-DD.pdf` and rebuild. The series and number become the citation tag. Works for any text PDF: unit SOPs, regulations, FMs you keep on hand.

## Limits

- Scanned PDFs with no text layer index as nothing. All ten shipped here have text.
- Retrieval is by meaning and by keyword, not by paragraph number. "AR 600-20 para 4-14" works less well than "what does the Army say about sexual harassment reporting".
- The answer is only as good as the retrieved pages. When the model says the excerpts do not cover it, raise `-k` or narrow with `--pub`.
- The doctrine is a snapshot. Check the Army Publishing Directorate for changes after the date in `SOURCES.md`.

## License

Code: MIT. The publications are U.S. Government works in the public domain; see `LICENSE` and `doctrine/SOURCES.md`.

Built by Joseph Cirello, U.S. Army veteran, Providence, RI.
