# ChainProof Demo Script

## Demo goal

Show that changing any registered AI artifact causes verification to fail.

## Steps

1. Train the model with `backend/train_model.py`.
2. Hash generated files with `backend/hash_files.py`.
3. Register the hashes on-chain.
4. Open the Streamlit UI.
5. Upload the original files.
6. Show verification success.
7. Change one value in `data/dataset.csv`.
8. Upload the changed dataset.
9. Show verification failed.

## Key explanation

The blockchain does not store the full model or dataset. It stores only hashes, which act as digital fingerprints.
