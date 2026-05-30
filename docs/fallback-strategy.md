# Fallback Strategy

## Segmentation Fallback

Retry 1:
- different preprocessing parameters

Retry 2:
- different segmentation algorithm

If still below threshold:
- send to human review

---

## OCR Fallback

Retry 1:
- different OCR parameters

Retry 2:
- different OCR engine

If still below threshold:
- send to human review

---

## Extraction Fallback

Retry 1:
- stricter prompt
- additional formatting instructions

Retry 2:
- switch LLM model

If still below threshold:
- send to human review