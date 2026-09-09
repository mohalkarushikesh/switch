# Fine-tuning pipeline (Azure AI Foundry)

Turns a small dataset of example conversations into a fine-tuned chat model
deployed on Azure AI Foundry, which the backend then serves via
`LLM_PROVIDER=azure`.

## Flow

```
data/sample_raw.jsonl  ──prepare_data.py──▶  data/train.jsonl + data/val.jsonl
                                                      │
                                          finetune_azure.py (upload + job)
                                                      │
                                          fine_tuned_model id  ──▶  deploy in
                                          Azure AI Foundry portal ──▶  backend
```

## 1. Prepare data

The raw dataset (`data/sample_raw.jsonl`) is one example per line:

```json
{"user": "How do I switch to my fine-tuned model?", "assistant": "Set LLM_PROVIDER=azure in backend/.env and restart."}
```

Convert it to the chat format Azure fine-tuning expects (a `messages` array per
line) and split into train/validation:

```bash
python prepare_data.py --input data/sample_raw.jsonl --outdir data --val-split 0.2
```

This writes `data/train.jsonl` and `data/val.jsonl`, validating that every line
has a non-empty user + assistant turn.

## 2. Submit the fine-tuning job

Requires an Azure OpenAI / AI Foundry resource. Set credentials (a `.env` here
or real env vars — see `.env.example`):

```bash
export AZURE_FOUNDRY_ENDPOINT=https://<resource>.openai.azure.com
export AZURE_FOUNDRY_API_KEY=<key>
python finetune_azure.py \
  --train data/train.jsonl \
  --val data/val.jsonl \
  --base-model gpt-4o-mini-2024-07-18
```

The script uploads both files, creates the job, polls until it completes, and
prints the resulting `fine_tuned_model` id.

> On the corp network this step needs outbound access to
> `*.openai.azure.com`. It never contacts `huggingface.co`.

## 3. Deploy & wire up

1. In the Azure AI Foundry portal, deploy the `fine_tuned_model` and give the
   deployment a name.
2. In `backend/.env` set:
   ```
   LLM_PROVIDER=azure
   AZURE_FOUNDRY_ENDPOINT=https://<resource>.openai.azure.com
   AZURE_FOUNDRY_DEPLOYMENT=<your-deployment-name>
   AZURE_FOUNDRY_API_KEY=<key>
   ```
3. Restart the backend. The web app now talks to your fine-tuned model.
