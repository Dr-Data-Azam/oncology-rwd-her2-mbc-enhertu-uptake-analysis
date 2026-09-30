# /create-spec

Optional lightweight brief before building a phase. Use it only if the phase
has real ambiguity (e.g. competing clinical definitions). Skip it for mechanical
phases (ingest, report generation).

## Steps

1. State what the phase will produce (outputs, tables, config keys, ADRs).
2. List any decisions that need Azam's input before code is written.
3. Get a go / adjust response, then build.

No branches, no formal spec files, no tech-spec document. The ADRs written
during the phase are the permanent record of decisions made.

## Usage

```
/create-spec 03-biomarker-derivation
```
