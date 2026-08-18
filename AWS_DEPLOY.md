# Production deployment: ECS Fargate + RDS PostgreSQL

The local Compose stack is for development only. Production uses:

```text
Browser -> Application Load Balancer -> ECS Fargate app -> private RDS PostgreSQL
```

## Before creating AWS resources

1. Create a billing budget alert.
2. Use one AWS Region for ECR, ECS, RDS, Secrets Manager, and CloudWatch.
3. Build and test locally with `docker compose up -d --build`.
4. Keep `PUBLIC_HISTORY_ENABLED=false` for the anonymous public demo.

## Production configuration

- Store the complete `DATABASE_URL` in AWS Secrets Manager, not in source code.
- Give the ECS task role permission to read only that secret.
- Send container logs to CloudWatch.
- Keep RDS private. Its security group must allow port 5432 only from the ECS task security group.
- Put the Application Load Balancer in front of ECS; it is the only public component.

## Container image

Build and push a versioned image to ECR from this workspace. The trained model is intentionally excluded from Git but included in the local Docker build.

```powershell
$Region = "us-west-2"
$Repository = "orcapath"
$Version = "1.0.0"
$AccountId = aws sts get-caller-identity --query Account --output text

aws ecr create-repository --repository-name $Repository --region $Region
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"
docker build -t "orcapath:$Version" .
docker tag "orcapath:$Version" "$AccountId.dkr.ecr.$Region.amazonaws.com/$Repository`:$Version"
docker push "$AccountId.dkr.ecr.$Region.amazonaws.com/$Repository`:$Version"
```

Use `aws/ecs-task-definition.example.json` as a template when creating the ECS task definition. Replace all placeholder ARNs, image URL, Region, and log-group name.

## After deployment

Use `/api/health` as the load-balancer health check. Test a WAV upload, a feedback submission, and CloudWatch logs before sharing the public URL.
