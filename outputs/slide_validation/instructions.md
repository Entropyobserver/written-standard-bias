# SLIDE Validation Annotation Instructions

Goal: independently check whether SLIDE written-standard labels are reliable on the petroleum-domain sentences used in the paper.

Annotate only the written standard of the Norwegian sentence. Do not judge translation adequacy, fluency, terminology quality, or whether the sentence is a good reference.

Use exactly one label:

- nb_only: the sentence is clearly Bokmal only.
- nn_only: the sentence is clearly Nynorsk only.
- mixed: the sentence contains clear cues from both Bokmal and Nynorsk.
- uncertain: the sentence is too short, mostly names/numbers/terms, ambiguous between standards, or otherwise not safely classifiable.

Fill only `human_label_nb_only_nn_only_mixed_uncertain` and optional `notes`. The model/source metadata and SLIDE scores are intentionally hidden from the annotation sheet.

This sample is stratified by SLIDE label to test classifier reliability. It should not be used to estimate how frequent each written standard is in the corpus.
