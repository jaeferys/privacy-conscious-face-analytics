# Fairness, robustness, and failure-mode evaluation

The project includes a reproducible evaluation harness but does not commit face
datasets or publish invented benchmark results. It calculates precision,
recall, F1, latency, and throughput from an externally supplied local manifest.
Conditions such as easy/medium/hard, small faces, occlusion, pose, and lighting
are reported only when those labels are present in the supplied annotations.

## WIDER FACE candidate

[WIDER FACE](https://mmlab.ie.cuhk.edu.hk/projects/WIDERFace/) is a standard
face-detection benchmark described in the
[CVPR 2016 paper](https://openaccess.thecvf.com/content_cvpr_2016/html/Yang_WIDER_FACE_A_CVPR_2016_paper.html).
Its validation annotations support Easy, Medium, and Hard evaluation subsets;
the commonly used
[Python evaluation implementation](https://github.com/wondervictor/WiderFace-Evaluation)
lists the corresponding ground-truth files and is MIT licensed.

The evaluation-code license does not automatically license the dataset images.
The official project currently does not present sufficiently clear redistribution
terms for this repository to treat the images as freely redistributable.
Review the official download terms, image provenance, consent implications, and
intended non-production research use before downloading. Keep all images and
annotations under `datasets/`, which is Git-ignored.

## Manifest format

Create a JSON Lines file beside the ignored images:

```json
{"image":"images/example.jpg","boxes":[[10,20,40,50]],"conditions":["hard","small-face","occlusion"]}
```

Each box is `[x, y, width, height]`. Run:

```bash
face-analytics evaluate \
  --manifest datasets/wider-face/validation.jsonl \
  --detector mediapipe \
  --output-prefix reports/evaluation/wider-face
```

The command loads one image at a time, evaluates it in memory, discards the
frame, and writes aggregate JSON and Markdown metrics to an ignored report
directory.

## Fairness boundary and limitations

WIDER FACE does not provide a sufficient ethically grounded demographic-label
scheme for demographic fairness claims in this project. The code does not infer
gender, race, ethnicity, age, emotion, or other sensitive traits. Demographic
fairness is therefore **not measured**.

Condition-level results measure performance only on the supplied labels. Dataset
bias, photographer selection, geographic coverage, event categories, annotation
quality, detector threshold, domain shift to retail/event cameras, and small
sample sizes all limit generalization. Real-world benchmark results remain
pending until a dataset is lawfully obtained and evaluated.
