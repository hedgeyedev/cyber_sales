# Cyber Sales Deployment - Production Facts

Information discovered from live Kubernetes cluster.

## ✅ Confirmed Facts

### Cluster Information
- **Environment:** Production (not staging)
- **Cluster:** `https://rancher.prod.hedgeye.cloud/k8s/clusters/local`
- **Context:** `production`
- **Your kubectl:** Already configured and working

### Existing Resources
- **Admin Namespace:** `hedgeye-apps-vf4dc` ✅
- **Admin Pods:** `admin-web-587c7f58d-*` (2 replicas running) ✅
- **EFS Storage Class:** `efs-csi` (available, 2y27d old) ✅
- **Storage Provider:** `efs.csi.aws.com` ✅

### What This Means

**Good News:**
1. ✅ You already have kubectl access to production
2. ✅ EFS storage class exists (no setup needed)
3. ✅ Admin-web pods are running and accessible
4. ✅ Namespace is confirmed (`hedgeye-apps-vf4dc`)
5. ✅ No kubeconfig needed - your existing setup works

**Deployment Changes:**
- Target: **Production** (not staging)
- URL will be: `https://cyber-reports.hedgeye.com` (not .staging.hedgeye.cloud)
- Terraform workspace: `production-cyber-sales` (not staging-cyber-sales)

## Questions Still Needed from DevOps

### 1. ECR Repository
**Question:** Where should I push Docker images?

**Format:** `<account-id>.dkr.ecr.us-east-1.amazonaws.com/<repo-name>`

**Likely:** Ask DevOps to create:
- `<account>.dkr.ecr.us-east-1.amazonaws.com/cyber-sales-web`
- `<account>.dkr.ecr.us-east-1.amazonaws.com/cyber-sales-cronjob`

### 2. Terraform Cloud Workspace
**Question:** Can you create Terraform Cloud workspace?

**Name:** `production-cyber-sales`

**Why:** Terraform stores state in Terraform Cloud, needs workspace

### 3. Domain/Ingress
**Question:** Is `cyber-reports.hedgeye.com` available?

**Alternative:** Any preference for subdomain name?

### 4. Production Approval
**Question:** Confirmed this should go to PRODUCTION not staging?

**Impact:** Will be accessible to real users at hedgeye.com domain

## Updated Deployment Plan

### Phase 1: Get ECR Access
```bash
# Ask DevOps for:
ECR_REPO=<account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push web server
docker build --platform linux/amd64 -t cyber-sales-web .
docker tag cyber-sales-web:latest $ECR_REPO/cyber-sales-web:latest
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPO
docker push $ECR_REPO/cyber-sales-web:latest

# Build and push cronjob
docker build --platform linux/amd64 -f Dockerfile.cronjob -t cyber-sales-cronjob .
docker tag cyber-sales-cronjob:latest $ECR_REPO/cyber-sales-cronjob:latest
docker push $ECR_REPO/cyber-sales-cronjob:latest
```

### Phase 2: Deploy with Terraform
```bash
cd terraform/

# Initialize (requires Terraform Cloud workspace: production-cyber-sales)
terraform init

# Plan and apply
terraform apply \
  -var="app_image=$ECR_REPO/cyber-sales-web:latest" \
  -var="reports_user=hedgeye" \
  -var="reports_pass=SECURE_PASSWORD"

# Get outputs
terraform output app_url      # https://cyber-reports.hedgeye.com
terraform output namespace    # cyber-sales
terraform output pvc_name     # cyber-sales-data
```

### Phase 3: Deploy CronJob
```bash
# Update k8s/cronjob.yaml with:
# - namespace from terraform output
# - pvc_name from terraform output
# - image: $ECR_REPO/cyber-sales-cronjob:latest

# Apply
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/cronjob.yaml

# Test manually
kubectl create job --from=cronjob/refresh-cyber-reports test-run -n cyber-sales
kubectl logs -n cyber-sales job/test-run -f
```

## Security Considerations

**Production Deployment Means:**
- Real production data
- Public internet access (https://cyber-reports.hedgeye.com)
- Executives (Hayley, etc.) will use this
- Need strong password for HTTP Basic Auth
- Consider IP whitelisting if internal-only access desired

**CronJob Access:**
- ServiceAccount has kubectl exec permission to production admin-web pods
- Limited scope: Can only exec into admin-web, can't modify
- Reads production database (via admin-web Rails console)
- Writes to isolated EFS volume (can't affect other apps)

## Cost (Production)

| Resource | Size | Monthly Cost |
|----------|------|--------------|
| EFS Storage | ~1GB actual | ~$0.30 |
| EKS pods | 2 replicas | Included |
| ALB | 1 load balancer | ~$16 |
| **Total** | | **~$16.30/month** |

Same as staging, already budgeted in EKS cluster.

## Next Steps

1. **Confirm with team:** This is going to PRODUCTION, correct?
2. **Get ECR repo:** Ask DevOps to create ECR repositories
3. **Get TF workspace:** Ask DevOps to create `production-cyber-sales` workspace
4. **Confirm domain:** `cyber-reports.hedgeye.com` okay?
5. **Deploy:** Follow deployment plan above

## Rollback Plan

If something goes wrong:

```bash
# Delete CronJob
kubectl delete -f k8s/cronjob.yaml
kubectl delete -f k8s/serviceaccount.yaml

# Destroy Terraform resources
cd terraform/
terraform destroy

# No impact on admin-web or other production services
```

**Safe to deploy:** Completely isolated from existing production apps.

---

**Last Updated:** November 12, 2025
**Cluster:** Production
**Created By:** Forrest Chang
