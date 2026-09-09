# CI/CD (AWS CodePipeline + CodeBuild)

On every push to the tracked branch, CodePipeline pulls the source, CodeBuild
runs [`buildspec.yml`](./buildspec.yml) to build the React app and sync it to
the S3 site bucket.

## Prerequisites

1. The site bucket exists — deploy [`../infra`](../infra/README.md) first and
   note the `BucketNameOut` output.
2. A **CodeStar Connection** to GitHub exists and is *Available*
   (AWS console → Developer Tools → Settings → Connections). Copy its ARN.

## Deploy the pipeline

```bash
aws cloudformation deploy \
  --template-file codepipeline.yaml \
  --stack-name finetune-forge-pipeline \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    GitHubConnectionArn=arn:aws:codestar-connections:...:connection/xxxx \
    RepositoryId=your-org/finetune-forge \
    BranchName=main \
    DeployBucket=finetune-forge-<your-unique-suffix> \
    ViteApiBase=https://api.your-domain.com
```

The first run triggers automatically once the pipeline is created.

## What buildspec.yml does

| Phase        | Action                                                        |
| ------------ | ------------------------------------------------------------- |
| `install`    | Node 20 runtime.                                              |
| `pre_build`  | `cd frontend && npm ci`.                                      |
| `build`      | `npm run build` (bakes in `VITE_API_BASE`).                   |
| `post_build` | `aws s3 sync dist/` to `$DEPLOY_BUCKET`, cache-tuned headers. |

## Local dry-run of the build

You don't need AWS to check the build step itself:

```bash
cd frontend && npm ci && npm run build   # produces frontend/dist/
```
