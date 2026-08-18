# Orca Detector model card

## Current production model

`random-forest-log-mel-v1` classifies one-second WAV segments as a possible orca call or no call. It uses 128-band log-Mel spectrogram summaries and a 200-tree Random Forest.

## Evaluation

The model was evaluated with a recording-level split, so segments from one WAV do not appear in both training and test data. At its production threshold of 0.40, the held-out test precision is 59.62%, recall is 43.10%, and F1 is 50.04%. The confusion matrix is `[[928, 472], [920, 697]]` with rows `[no_orca, orca]` and columns `[predicted_no_orca, predicted_orca]`.

## Intended use and limitations

Use this model to prioritize audio for review, not to confirm species presence. The local dataset has 606 available WAV recordings out of 2,358 recordings named by the labels, so these metrics do not represent the complete dataset. Human feedback stored by the app is review data for a future retraining cycle; it does not automatically retrain the deployed model.
