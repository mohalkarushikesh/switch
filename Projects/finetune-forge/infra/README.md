# Infrastructure (AWS)

CloudFormation for hosting the React frontend on Amazon S3 as a static website.

## Deploy the hosting bucket

```bash
aws cloudformation deploy \
  --template-file cloudformation/s3-static-site.yaml \
  --stack-name finetune-forge-site \
  --parameter-overrides BucketName=finetune-forge-<your-unique-suffix>
```

Then read back the public URL:

```bash
aws cloudformation describe-stacks \
  --stack-name finetune-forge-site \
  --query "Stacks[0].Outputs" --output table
```

Use the `BucketNameOut` value as the `DEPLOY_BUCKET` for the CI/CD pipeline
(see [`../ci/README.md`](../ci/README.md)).

## Notes

- The bucket serves objects publicly for static-website hosting; `index.html`
  is also the error document so client-side routes resolve to the app shell.
- **Hardening option:** put CloudFront + Origin Access Control in front and make
  the bucket private. Left out here to match the brief's "hosted on S3" scope.
