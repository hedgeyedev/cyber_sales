# Cyber Sales Reports - K8s Deployment Guide

Deployment using Hedgeye's InfraV2 Terraform pattern for AWS EKS.

## Prerequisites

### 1. Get from DevOps

- [ ] **ECR Repository URL** - Where to push Docker images
- [ ] **Terraform Cloud Workspace** - Create `staging-cyber-sales`
- [ ] **kubeconfig.yaml** - For staging cluster (place in `terraform/` directory)
- [ ] **Verify admin-web namespace** - Confirm it's still `hedgeye-apps-vf4dc`

### 2. Local Setup

```bash
# Install AWS CLI and configure
aws configure

# Install Terraform
brew install terraform

# Install Docker
# (for building x86 images on Mac)
```

## Deployment Steps

### Phase 1: Deploy Web Server (Terraform)

#### 1. Build and Push Web Server Image

```bash
cd /Users/fkchang/work/cyber_sales

# Build for x86 (AWS EKS requirement)
docker build --platform linux/amd64 -t cyber-sales-web .

# Tag for ECR
docker tag cyber-sales-web:latest <ECR_REPO>/cyber-sales-web:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ECR_REPO>

# Push
docker push <ECR_REPO>/cyber-sales-web:latest
```

#### 2. Deploy with Terraform

```bash
cd terraform/

# Initialize
terraform init

# Plan (review what will be created)
terraform plan \
  -var="app_image=<ECR_REPO>/cyber-sales-web:latest" \
  -var="reports_user=hedgeye" \
  -var="reports_pass=YOUR_SECURE_PASSWORD"

# Apply
terraform apply \
  -var="app_image=<ECR_REPO>/cyber-sales-web:latest" \
  -var="reports_user=hedgeye" \
  -var="reports_pass=YOUR_SECURE_PASSWORD"
```

#### 3. Get Outputs

```bash
# Save these for Phase 2
terraform output namespace      # e.g., "cyber-sales"
terraform output pvc_name       # e.g., "cyber-sales-data"
terraform output app_url        # e.g., "https://cyber-reports.staging.hedgeye.cloud"
```

#### 4. Test Web Server

```bash
# Get the URL
URL=$(terraform output -raw app_url)

# Test (should return 401 without auth)
curl $URL

# Test with auth (should return 200)
curl -u hedgeye:YOUR_PASSWORD $URL
```

### Phase 2: Deploy Data Refresh CronJob

#### 1. Build and Push CronJob Image

```bash
cd /Users/fkchang/work/cyber_sales

# Build for x86
docker build --platform linux/amd64 -f Dockerfile.cronjob -t cyber-sales-cronjob .

# Tag and push
docker tag cyber-sales-cronjob:latest <ECR_REPO>/cyber-sales-cronjob:latest
docker push <ECR_REPO>/cyber-sales-cronjob:latest
```

#### 2. Update CronJob Manifest

Edit `k8s/cronjob.yaml`:

```yaml
# Line 7: Update namespace (from terraform output)
namespace: cyber-sales

# Line 49: Update image URL
image: <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/cyber-sales-cronjob:latest

# Line 82: Update PVC name (from terraform output)
claimName: cyber-sales-data
```

#### 3. Deploy ServiceAccount and CronJob

```bash
cd /Users/fkchang/work/cyber_sales

# Apply ServiceAccount (gives cronjob kubectl access)
kubectl apply -f k8s/serviceaccount.yaml

# Apply CronJob
kubectl apply -f k8s/cronjob.yaml
```

#### 4. Test CronJob Manually

```bash
# Trigger a manual run (don't wait for 6am)
kubectl create job --from=cronjob/refresh-cyber-reports manual-test-1 -n cyber-sales

# Watch the job
kubectl get jobs -n cyber-sales -w

# Check logs
kubectl logs -n cyber-sales job/manual-test-1 -f

# Verify reports were generated
kubectl exec -n cyber-sales deploy/cyber-sales -- ls -lh /app/*.html
```

## Verification Checklist

- [ ] Web server is running: `kubectl get pods -n cyber-sales`
- [ ] URL is accessible: Visit `https://cyber-reports.staging.hedgeye.cloud`
- [ ] Authentication works: Login with hedgeye/password
- [ ] Reports are visible: index.html loads with all 14 reports
- [ ] CronJob created: `kubectl get cronjob -n cyber-sales`
- [ ] Manual job succeeds: `kubectl get jobs -n cyber-sales`
- [ ] Fresh data appears: Reports show latest data after cronjob runs

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Terraform Deployment                                │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ Namespace: cyber-sales                       │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ PVC: cyber-sales-data (10Gi EFS)             │  │
│  │   /app/*.html  ← Reports                     │  │
│  │   /app/cache/  ← Cached data                 │  │
│  └──────────────────────────────────────────────┘  │
│                    ↑              ↑                  │
│  ┌─────────────────┘              └──────────────┐  │
│  │ Deployment: cyber-sales        CronJob (kubectl)│
│  │ - 2 replicas                   - Runs daily 6am│
│  │ - Mounts PVC (read-only)       - Mounts PVC (rw)│
│  │ - Serves HTML via Sinatra      - Exec admin-web│
│  │ - Port 4567                     - Generate HTML│
│  └────────────────────────────────────────────────┘│
│                    ↓                                 │
│  ┌──────────────────────────────────────────────┐  │
│  │ Service + Ingress                            │  │
│  │   https://cyber-reports.staging.hedgeye.cloud│ │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Updating the App

### Update Web Server Code

```bash
# 1. Make changes to app.rb or other files
# 2. Rebuild and push
docker build --platform linux/amd64 -t cyber-sales-web .
docker push <ECR_REPO>/cyber-sales-web:latest

# 3. Restart deployment
kubectl rollout restart deployment/cyber-sales -n cyber-sales

# 4. Watch rollout
kubectl rollout status deployment/cyber-sales -n cyber-sales
```

### Update Data Refresh Logic

```bash
# 1. Make changes to refresh_analysis.sh, Python scripts, etc.
# 2. Rebuild and push cronjob image
docker build --platform linux/amd64 -f Dockerfile.cronjob -t cyber-sales-cronjob .
docker push <ECR_REPO>/cyber-sales-cronjob:latest

# 3. Delete existing cronjob and recreate
kubectl delete cronjob refresh-cyber-reports -n cyber-sales
kubectl apply -f k8s/cronjob.yaml

# 4. Test manually
kubectl create job --from=cronjob/refresh-cyber-reports manual-test-2 -n cyber-sales
```

## Troubleshooting

### Web Server Issues

```bash
# Check pods
kubectl get pods -n cyber-sales

# Check logs
kubectl logs -n cyber-sales deploy/cyber-sales -f

# Describe pod
kubectl describe pod -n cyber-sales <pod-name>

# Exec into pod
kubectl exec -it -n cyber-sales deploy/cyber-sales -- /bin/bash
ls -la /app  # Verify PVC is mounted
```

### CronJob Issues

```bash
# List cronjobs
kubectl get cronjob -n cyber-sales

# List jobs (recent runs)
kubectl get jobs -n cyber-sales

# Check specific job logs
kubectl logs -n cyber-sales job/<job-name>

# Check if ServiceAccount has permissions
kubectl auth can-i create pods/exec --as=system:serviceaccount:cyber-sales:cyber-sales-data-fetcher -n hedgeye-apps-vf4dc
```

### PVC Issues

```bash
# Check PVC status
kubectl get pvc -n cyber-sales

# Describe PVC
kubectl describe pvc cyber-sales-data -n cyber-sales

# Check what's in the volume
kubectl exec -n cyber-sales deploy/cyber-sales -- ls -lh /app
```

### Ingress/URL Issues

```bash
# Check ingress
kubectl get ingress -n cyber-sales

# Describe ingress
kubectl describe ingress cyber-sales -n cyber-sales

# Check ALB
kubectl get ingress cyber-sales -n cyber-sales -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

## Cleanup

```bash
# Delete CronJob
kubectl delete -f k8s/cronjob.yaml

# Delete ServiceAccount
kubectl delete -f k8s/serviceaccount.yaml

# Destroy Terraform resources
cd terraform/
terraform destroy
```

## Cost Estimate

| Resource | Size | Monthly Cost |
|----------|------|--------------|
| EFS Storage | 1GB actual | ~$0.30 |
| EKS pods | 2 replicas | Included in cluster |
| ALB | 1 load balancer | ~$16 |
| **Total** | | **~$16.30/month** |

## Security Notes

- **Credentials**: Use Terraform variables for sensitive data (not checked into git)
- **ServiceAccount**: Limited to exec into admin-web pods only
- **HTTP Basic Auth**: Protects reports from unauthorized access
- **HTTPS**: Automatic via ALB + ACM wildcard certificate
- **Network**: Ingress is internet-facing (adjust if needed for internal-only)

## Next Steps

Once deployed and tested:

1. **Share URL** with Hayley (CFO) and team
2. **Monitor first cronjob run** at 6am
3. **Verify reports update daily**
4. **Decommission daily ZIP workflow**
5. **Optional**: Set up CloudWatch alerts for cronjob failures

## Support

Questions? Issues?
- Check Terraform state: `terraform show`
- Check K8s resources: `kubectl get all -n cyber-sales`
- Contact: Forrest Chang

---

**Last Updated:** November 2025
**Environment:** Staging (AWS EKS)
