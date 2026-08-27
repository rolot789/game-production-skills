# Reference Search Policy

## Purpose

Define how `art-style-builder` researches additional visual references without allowing search volume, popularity, or source bias to overpower user intent.

## Search precondition

Do not search merely because search is available. Search only when at least one of the following is true:

- a production-significant style dimension is unresolved,
- a user reference has a gap that requires supporting evidence,
- existing references conflict and external evidence can clarify alternatives,
- current reference corpus coverage is insufficient for a requested revision,
- a category such as UI/environment needs a scoped style override,
- a blocked/unavailable critical reference needs a replacement.

Before new search, inspect `reference-corpus.yaml` and `reference-search-history.yaml` for reusable evidence.

## Search modes

### Reference-anchored search

Inputs:
- user-provided references,
- dimensions each user reference governs,
- unresolved/missing dimensions,
- locked rules that must not drift.

Search objective:
- find supporting evidence for missing dimensions,
- find attributable production breakdowns that clarify technique,
- find category-specific references that remain compatible with the user anchor.

Do not search for a replacement overall style unless the user asks to reopen direction.

### Exploratory search

Inputs:
- structured Style Intent Model,
- GameSpec visual/readability constraints,
- confirmed positive/negative rules.

Search objective:
- expose a small number of meaningfully different but compatible visual directions,
- gather concrete evidence for line, shape, palette, texture, lighting, UI, etc.,
- let the user progressively narrow the style.

## Source weighting

Use source tiers as a ranking prior, not an absolute truth. Relevance to the actual unresolved dimension still matters.

### Tier S — user evidence

Highest priority for governed dimensions:
- user-uploaded references,
- user-designated identity/style anchors,
- project-owned art already approved by the user.

These are not overridden by web-discovered references unless the user reopens the decision.

### Tier A — primary / attributable sources

Prefer strongly:
- official developer or publisher sites,
- official game pages, press kits, art books/pages, devlogs,
- official artist portfolio sites,
- attributable professional portfolios,
- GDC / GDC Vault visual-development and art-direction material.

Use these when provenance, production context, or actual game identity matters.

### Tier B — professional discovery sources

Useful for visual discovery and portfolio evidence:
- ArtStation,
- Behance,
- 80 Level production/art interviews,
- Steam official store screenshots,
- itch.io developer/project pages,
- studio or artist blogs/devlogs.

Prefer original project/artist pages over mirrors/reposts.

### Tier C — secondary discovery

Use cautiously:
- design galleries,
- curated inspiration blogs,
- general image-search results with attributable origin.

These may generate query leads but should not outrank primary evidence.

### Tier D — discovery only by default

Strongly down-rank:
- Pinterest-like boards,
- unattributed reposts,
- low-resolution collages,
- watermarked mirrors,
- pages dominated by unknown/generated images,
- results with unclear authorship or source chain.

Do not use these as production-critical locked anchors when attributable alternatives exist.

## Candidate scoring

Rank candidates by a combination of:

- unresolved-dimension relevance,
- consistency with locked user intent,
- provenance/attribution quality,
- visual accessibility,
- production/context value,
- diversity relative to already collected evidence,
- conflict risk with existing locks.

A candidate with high overall beauty but low relevance to the pending dimension should rank low.

## Query construction

Construct queries from explicit style dimensions rather than vague aesthetic phrases.

Prefer:

```text
stylized game UI hand drawn low texture readability portfolio
2D game environment irregular crayon line restrained palette art direction
indie game character simple silhouette tactile pastel texture devlog
```

over:

```text
beautiful indie game art
cool hand drawn style
```

When reference-anchored, include only the dimensions that need expansion. Avoid broad queries that invite style drift.

## Query memory and deduplication

Store each search attempt in `reference-search-history.yaml` with:
- normalized intent,
- dimensions,
- domains/source tiers,
- query strings,
- returned reference IDs,
- rejected reasons,
- timestamp when available,
- semantic/query fingerprint.

Before executing a materially similar query, reuse previous results unless:
- availability changed,
- the user changed the target dimension,
- previous coverage was insufficient,
- freshness is actually relevant.

## Search budget

Default guidance, not a hard universal cap:

```text
Initial exploration:
  up to ~4–6 focused queries
  curate ~12–24 corpus candidates
  present only ~3–6 at a time

Delta loop:
  normally <=2 focused queries
  add <=6–8 candidates

Branch reset:
  normally <=4 focused queries
  add <=12–16 candidates
```

Do not spend the full budget if corpus coverage becomes sufficient earlier.

## Corpus coverage

Estimate whether each important dimension has sufficient evidence.

Example dimensions:
- line,
- palette,
- texture,
- character shape,
- environment structure,
- UI,
- lighting,
- materials.

Coverage is sufficient when the user can make or has already made a stable decision from accessible, relevant evidence. It is not merely a count of images.

## Accessibility resolution

For each result classify:

- `PREVIEWABLE`
- `DOWNLOADABLE`
- `LINK_ONLY`
- `BLOCKED`
- `UNAVAILABLE`

Rules:
- do not bypass access controls,
- do not claim visual verification when only metadata/text was available,
- do not make a critical anchor depend solely on an inaccessible image,
- if a user can access a critical reference but the agent cannot, ask for an accessible copy when necessary,
- prefer a corpus replacement before launching a broad new search.

## User presentation

Present curated reference boards, not raw result dumps.

A reference board should group candidates by the pending decision cluster and include:
- preview if supported,
- reference ID,
- source,
- selected dimensions,
- why it is relevant,
- explicit non-governing/rejected dimensions,
- accessibility warning if necessary.

The user should be able to select combinations such as:
- line from REF-003,
- palette from USER-REF-001,
- UI cleanliness from REF-011.

## Copyright / storage behavior

Discovery does not imply permission to redistribute source images.

Default project persistence should favor:
- canonical URL,
- provenance,
- reference ID,
- fingerprints/metadata,
- user feedback,
- governed dimensions.

Use temporary runtime previews where available. Do not automatically commit third-party reference image files into the user's game repository.
