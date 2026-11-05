# Cyber Sales Deployment Workflow

Complete step-by-step guide from DevOps coordination to production deployment.

## Prerequisites from DevOps

Before starting deployment, you need these values from DevOps:

### 1. ECR Repository URLs
**Request**: "Can you create two ECR repositories for the cyber sales application?"

**Repos needed**:
- `<account-id>.dkr.ecr.us-east-1.amazonaws.com/cyber-sales-web`
- `<account-id>.dkr.ecr.us-east-1.amazonaws.com/cyber-sales-cronjob`

**Why**: Docker images must be pushed to ECR for EKS to pull them

### 2. Terraform Cloud Workspace
**Request**: "Can you create a Terraform Cloud workspace?"

**Name**: `production-cyber-sales`

**Why**: Terraform stores state in Terraform Cloud, needs workspace to track infrastructure

### 3. Domain Confirmation
**Request**: "Is `cyber-reports.hedgeye.com` available as a subdomain?"

**Alternative**: "Any preference for the subdomain name?"

**Why**: ALB Ingress will create DNS entry for this domain

### 4. Production Approval
**Request**: "Confirmed this should go to PRODUCTION (not staging)?"

**Impact**: Will be accessible to real users at hedgeye.com domain

**Security**: Will contain real production payment data

## Complete Deployment Checklist

### Phase 0: Repository Setup

- [ ] **Create GitHub repository**
  ```bash
  cd /Users/fkchang/work/cyber_sales
  git init
  git add .
  git commit -m "Initial commit: Cyber Sales K8s deployment"
  git remote add origin git@github.com:hedgeye/<repo-name>.git
  git push -u origin main
  ```

- [ ] **Share repo with DevOps** for Terraform review
  - Send link to GitHub repo
  - Point them to `terraform/` directory
  - Ask them to review before proceeding

### Phase 1: Get Prerequisites from DevOps

- [ ] **Request ECR repositories** (see above)
- [ ] **Request Terraform Cloud workspace** (see above)
- [ ] **Confirm domain availability** (see above)
- [ ] **Get production deployment approval** (see above)

### Phase 2: Build and Push Docker Images

- [ ] **Build web server image**
  ```bash
  cd /Users/fkchang/work/cyber_sales

  # Build for x86 (AWS EKS requirement)
  docker build --platform linux/amd64 -t cyber-sales-web .
  ```

- [ ] **Build cronjob image**
  ```bash
  # Build cronjob image
  docker build --platform linux/amd64 -f Dockerfile.cronjob -t cyber-sales-cronjob .
  ```

- [ ] **Login to ECR**
  ```bash
  # Get ECR_REPO from DevOps (e.g., 123456789.dkr.ecr.us-east-1.amazonaws.com)
  ECR_REPO=<from-devops>

  aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin $ECR_REPO
  ```

- [ ] **Tag and push web server**
  ```bash
  docker tag cyber-sales-web:latest $ECR_REPO/cyber-sales-web:latest
  docker push $ECR_REPO/cyber-sales-web:latest
  ```

- [ ] **Tag and push cronjob**
  ```bash
  docker tag cyber-sales-cronjob:latest $ECR_REPO/cyber-sales-cronjob:latest
  docker push $ECR_REPO/cyber-sales-cronjob:latest
  ```

### Phase 3: Deploy with Terraform

- [ ] **Initialize Terraform**
  ```bash
  cd terraform/

  # Requires Terraform Cloud workspace: production-cyber-sales
  terraform init
  ```

- [ ] **Plan deployment** (review what will be created)
  ```bash
  terraform plan \
    -var="app_image=$ECR_REPO/cyber-sales-web:latest" \
    -var="reports_user=hedgeye" \
    -var="reports_pass=YOUR_SECURE_PASSWORD"
  ```

- [ ] **Apply deployment**
  ```bash
  terraform apply \
    -var="app_image=$ECR_REPO/cyber-sales-web:latest" \
    -var="reports_user=hedgeye" \
    -var="reports_pass=YOUR_SECURE_PASSWORD"
  ```

- [ ] **Save Terraform outputs** (needed for Phase 4)
  ```bash
  terraform output namespace      # e.g., "cyber-sales"
  terraform output pvc_name       # e.g., "cyber-sales-data"
  terraform output app_url        # e.g., "https://cyber-reports.hedgeye.com"
  ```

### Phase 4: Deploy CronJob

- [ ] **Update k8s/cronjob.yaml with Terraform outputs**
  ```yaml
  # Line 7: Update namespace (from terraform output)
  namespace: cyber-sales

  # Line 49: Update image URL
  image: <ECR_REPO>/cyber-sales-cronjob:latest

  # Line 82: Update PVC name (from terraform output)
  claimName: cyber-sales-data
  ```

- [ ] **Deploy ServiceAccount**
  ```bash
  kubectl apply -f k8s/serviceaccount.yaml
  ```

- [ ] **Deploy CronJob**
  ```bash
  kubectl apply -f k8s/cronjob.yaml
  ```

### Phase 5: Verification

- [ ] **Test web server is running**
  ```bash
  kubectl get pods -n cyber-sales
  # Should show 2 pods running
  ```

- [ ] **Test URL is accessible**
  ```bash
  URL=$(cd terraform && terraform output -raw app_url)

  # Should return 401 without auth
  curl $URL

  # Should return 200 with auth
  curl -u hedgeye:YOUR_PASSWORD $URL
  ```

- [ ] **Trigger manual cronjob run** (don't wait for 6am)
  ```bash
  kubectl create job --from=cronjob/refresh-cyber-reports manual-test-1 -n cyber-sales
  ```

- [ ] **Watch job progress**
  ```bash
  kubectl get jobs -n cyber-sales -w
  ```

- [ ] **Check job logs**
  ```bash
  kubectl logs -n cyber-sales job/manual-test-1 -f
  ```

- [ ] **Verify reports were generated**
  ```bash
  kubectl exec -n cyber-sales deploy/cyber-sales -- ls -lh /app/*.html
  ```

- [ ] **Visit URL in browser**
  - Open `https://cyber-reports.hedgeye.com`
  - Login with hedgeye/password
  - Verify index.html loads with all reports
  - Spot-check 2-3 individual reports

### Phase 6: Stakeholder Communication

- [ ] **Share URL with Hayley (CFO) and team**
  ```
  Subject: Cyber Sales Reports Now Available via URL

  Hi Hayley,

  The cyber sales analysis reports are now available at:
  https://cyber-reports.hedgeye.com

  Login credentials:
  - Username: hedgeye
  - Password: [provided separately]

  The reports refresh automatically every morning at 6am EST with the latest data.

  No more daily ZIP files needed!

  Let me know if you have any questions.

  - Forrest
  ```

- [ ] **Monitor first automated cronjob run** (next day at 6am)
  ```bash
  # Check cronjob history
  kubectl get jobs -n cyber-sales

  # Check latest job logs
  kubectl logs -n cyber-sales job/refresh-cyber-reports-<timestamp> -f
  ```

- [ ] **Verify reports update daily**
  - Check reports for fresh data after 6am runs
  - Verify timestamp in reports matches current date

### Phase 7: Cleanup Old Workflow

- [ ] **Decommission daily ZIP workflow**
  - Stop running `refresh_analysis.sh` manually
  - Archive old ZIP files
  - Update any documentation referencing ZIP files

- [ ] **Update documentation**
  - Add production URL to team wiki
  - Document login credentials in password manager
  - Share troubleshooting guide with team

## Potential DevOps Questions

### Q: "Why do you need two ECR repositories?"
**A**: We have two separate Docker images:
1. `cyber-sales-web` - Sinatra web server (serves HTML reports)
2. `cyber-sales-cronjob` - Data refresh job (runs kubectl to extract data)

They have different dependencies (cronjob needs kubectl, web server doesn't).

### Q: "Why does the cronjob need kubectl access?"
**A**: The data lives in the production database, accessed via admin-web pod. The cronjob runs `kubectl exec` into admin-web to execute Rails console commands and extract payment data. This is safer than giving the cronjob direct database credentials.

### Q: "What permissions does the ServiceAccount need?"
**A**: Limited RBAC permissions:
- `get`, `list`, `create` on `pods` and `pods/exec` in `hedgeye-apps-vf4dc` namespace only
- Cannot modify pods, cannot access other namespaces
- See `k8s/serviceaccount.yaml` for full RBAC configuration

### Q: "Why production and not staging?"
**A**: The data source (admin-web) is in production. We need access to the production database to generate accurate reports. The app itself is read-only (just serving static HTML), so production deployment is safe.

### Q: "What's the cost impact?"
**A**: Approximately $16.30/month:
- EFS storage (~1GB): $0.30
- ALB: $16.00
- EKS pods: Included in existing cluster cost

### Q: "Can we restrict access to internal network only?"
**A**: Yes, we can change the ALB scheme from `internet-facing` to `internal` in `terraform/kubernetes.tf` line 153. HTTP Basic Auth provides first layer of protection for internet-facing deployment.

### Q: "What happens if the cronjob fails?"
**A**:
- Job history is kept (last 3 successful + 3 failed jobs)
- Old reports remain accessible (web server keeps serving last successful run)
- Can manually trigger job: `kubectl create job --from=cronjob/refresh-cyber-reports manual-fix`
- Logs available: `kubectl logs -n cyber-sales job/<job-name>`

### Q: "How do we update the application code?"
**A**:
1. Make code changes
2. Rebuild Docker image: `docker build --platform linux/amd64 -t cyber-sales-web .`
3. Push to ECR: `docker push $ECR_REPO/cyber-sales-web:latest`
4. Restart deployment: `kubectl rollout restart deployment/cyber-sales -n cyber-sales`

### Q: "What's the rollback plan?"
**A**:
```bash
# Delete CronJob
kubectl delete -f k8s/cronjob.yaml
kubectl delete -f k8s/serviceaccount.yaml

# Destroy Terraform resources
cd terraform/
terraform destroy

# No impact on admin-web or other production services
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

## Monitoring and Maintenance

**Daily Checks:**
- Verify reports are updating (check timestamp)
- Monitor cronjob success rate: `kubectl get jobs -n cyber-sales`

**Weekly Checks:**
- Review pod health: `kubectl get pods -n cyber-sales`
- Check logs for errors: `kubectl logs -n cyber-sales deploy/cyber-sales --tail=100`

**Monthly Checks:**
- Review EFS storage usage: `kubectl describe pvc cyber-sales-data -n cyber-sales`
- Verify SSL certificate is valid (ACM auto-renews, but check)

**Optional: CloudWatch Alerts**
- Alert on cronjob failures
- Alert on pod restarts
- Alert on high error rates

## Success Metrics

After deployment is complete, you should have:
- ✅ Web server running with 2 replicas
- ✅ HTTPS URL accessible at `https://cyber-reports.hedgeye.com`
- ✅ Authentication working (hedgeye/password)
- ✅ All 14+ reports visible on index.html
- ✅ CronJob created and scheduled for 6am daily
- ✅ Manual test job succeeded
- ✅ Reports showing fresh data
- ✅ No more daily ZIP file workflow needed
- ✅ Stakeholders have access to URL
- ✅ Saved 5-10 min/day of manual work (40+ hours/year)

---

**Last Updated:** November 14, 2025
**Environment:** Production
**Created By:** Forrest Chang
