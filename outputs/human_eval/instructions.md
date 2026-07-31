# Human Evaluation Instructions

## Task

For each English source sentence, evaluate two Norwegian translations: System A
and System B. The system identities are hidden. Please score System A and
System B independently before choosing a preference.

## Target Use Case

Assume the intended deployment setting is Bokmal petroleum-domain translation.
The preferred output should preserve the source meaning and use natural Bokmal.

## Adequacy

Adequacy measures how well the translation preserves the meaning of the English
source. Do not penalize a translation for being Nynorsk or mixed-standard when
scoring adequacy.

- 2 = Meaning is fully or almost fully preserved. Minor style differences or
  harmless wording changes are acceptable.
- 1 = Meaning is partly preserved, but there is an omission, mistranslation,
  awkward phrase, or terminology problem that affects part of the sentence.
- 0 = Meaning is wrong, misleading, severely incomplete, or difficult to
  understand.

## Bokmal Conformity

Bokmal conformity measures whether the Norwegian output is natural Bokmal. Do
not judge meaning here except when the output is so unnatural that the written
standard cannot be assessed.

- 2 = Natural Bokmal, with standard Bokmal spelling, morphology, and wording.
- 1 = Mixed, weakly diagnostic, or mostly understandable but contains some
  Nynorsk forms, non-standard forms, or awkward Bokmal.
- 0 = Clearly not Bokmal, mostly Nynorsk, strongly mixed, or unnatural /
  non-standard Norwegian.

## Preference

Choose A, B, or Tie for the target use case: Bokmal petroleum-domain
translation.

- Choose A if System A is better overall for this use case.
- Choose B if System B is better overall for this use case.
- Choose Tie if both are equally good, equally bad, or the difference is too
  small to matter.

When choosing preference, prioritize:

1. Adequacy: the translation should preserve the source meaning.
2. Bokmal conformity: if adequacy is similar, prefer the more natural Bokmal
   output.
3. Domain terminology and fluency: prefer correct petroleum terminology and
   natural technical style.

## Notes

Use the notes column only when something is unclear, difficult, or important to
explain. Notes are optional.
