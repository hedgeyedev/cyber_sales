# How the CronJob Connects to Admin-Web

Technical deep-dive on the Kubernetes ServiceAccount authentication mechanism.

## The Question

"How does the cronjob pod authenticate to Kubernetes so it can run kubectl commands to exec into the admin-web pod?"

## The Short Answer

Kubernetes **automatically** provides authentication credentials to every pod via **ServiceAccounts**. The cronjob pod doesn't need your personal kubeconfig or any manually-created credentials. When the cronjob pod starts, Kubernetes injects a token into the pod's filesystem, and kubectl inside the pod automatically uses this token.

## The Complete Flow

### Step 1: ServiceAccount Creation

When you apply `k8s/serviceaccount.yaml`, you create:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cyber-sales-data-fetcher
  namespace: cyber-sales
```

This creates an **identity** in Kubernetes (like a "service user account").

### Step 2: RBAC Permissions

The ServiceAccount alone has **no permissions**. You grant it permissions using RBAC (Role-Based Access Control):

```yaml
# Role: What actions are allowed?
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: admin-pod-exec
  namespace: hedgeye-apps-vf4dc  # Where admin-web lives
rules:
- apiGroups: [""]
  resources: ["pods", "pods/exec"]
  verbs: ["get", "list", "create"]  # Can get pods, exec into them
```

```yaml
# RoleBinding: Who gets these permissions?
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cyber-sales-can-exec-admin
  namespace: hedgeye-apps-vf4dc
roleRef:
  kind: Role
  name: admin-pod-exec
subjects:
- kind: ServiceAccount
  name: cyber-sales-data-fetcher  # This ServiceAccount gets the permissions
  namespace: cyber-sales
```

This says: "The `cyber-sales-data-fetcher` ServiceAccount can get/list/exec pods in the `hedgeye-apps-vf4dc` namespace."

### Step 3: CronJob Uses ServiceAccount

In `k8s/cronjob.yaml`, you specify which ServiceAccount the pod should use:

```yaml
spec:
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: cyber-sales-data-fetcher  # Use this identity
```

### Step 4: Kubernetes Injects Credentials

When the cronjob pod starts, Kubernetes **automatically**:

1. **Generates a token** for the ServiceAccount
2. **Mounts it into the pod** at a well-known path:
   ```
   /var/run/secrets/kubernetes.io/serviceaccount/token
   ```
3. **Mounts the CA certificate** for the Kubernetes API:
   ```
   /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
   ```
4. **Mounts the namespace** the pod is running in:
   ```
   /var/run/secrets/kubernetes.io/serviceaccount/namespace
   ```

**You don't have to do any of this manually.** Kubernetes does it automatically for every pod.

### Step 5: kubectl Finds Credentials Automatically

Inside the cronjob pod, when you run:

```bash
kubectl exec -it admin-web-587c7f58d-xxx -n hedgeye-apps-vf4dc -- rails console
```

kubectl **automatically**:

1. Checks if it's running inside a Kubernetes pod (by looking for `/var/run/secrets/kubernetes.io/serviceaccount/`)
2. Reads the token from `/var/run/secrets/kubernetes.io/serviceaccount/token`
3. Reads the CA cert from `/var/run/secrets/kubernetes.io/serviceaccount/ca.crt`
4. Uses these to authenticate to the Kubernetes API server
5. Sends the API request: "Execute this command in admin-web pod"
6. Kubernetes API checks: "Does the `cyber-sales-data-fetcher` ServiceAccount have permission to exec into pods in namespace `hedgeye-apps-vf4dc`?"
7. RBAC says: "Yes, the RoleBinding grants this permission"
8. API allows the exec operation
9. Command runs inside admin-web pod
10. Output is returned to cronjob pod

## Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ CronJob Pod (cyber-sales namespace)                            │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Process: ./refresh_analysis.sh                            │ │
│  │                                                            │ │
│  │ 1. Runs: kubectl exec admin-web-xxx -- rails console     │ │
│  │                                                            │ │
│  │ 2. kubectl checks: /var/run/secrets/.../token exists?    │ │
│  │    ✓ Yes → Use in-cluster authentication                 │ │
│  │                                                            │ │
│  │ 3. kubectl reads:                                         │ │
│  │    - Token:     /var/run/secrets/.../token               │ │
│  │    - CA cert:   /var/run/secrets/.../ca.crt              │ │
│  │    - Namespace: /var/run/secrets/.../namespace           │ │
│  │                                                            │ │
│  │ 4. kubectl sends HTTPS request to Kubernetes API:        │ │
│  │    POST /api/v1/namespaces/hedgeye-apps-vf4dc/           │ │
│  │         pods/admin-web-xxx/exec                           │ │
│  │    Authorization: Bearer <token>                          │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    (HTTPS + Token)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Kubernetes API Server                                           │
│                                                                 │
│  1. Receives request with Bearer token                         │
│  2. Validates token signature using CA cert                    │
│  3. Extracts identity: "cyber-sales-data-fetcher" ServiceAccount│
│  4. Checks RBAC:                                               │
│     - Does this ServiceAccount have permission?                │
│     - Role: admin-pod-exec in hedgeye-apps-vf4dc              │
│     - RoleBinding: cyber-sales-can-exec-admin                  │
│     - Verbs: get, list, create on pods/exec                   │
│  5. ✓ Permission granted                                       │
│  6. Forwards exec request to kubelet on node running admin-web │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                        (gRPC to kubelet)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Admin-Web Pod (hedgeye-apps-vf4dc namespace)                   │
│                                                                 │
│  1. Kubelet receives exec request from API server              │
│  2. Starts Rails console process inside admin-web container:   │
│     $ rails console                                             │
│  3. Cronjob can now send Ruby commands:                        │
│     > RecurringPayment.where(...)                              │
│  4. Results are streamed back through API server to cronjob   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                      (Results flow back)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ CronJob Pod                                                     │
│                                                                 │
│  1. Receives data from Rails console                           │
│  2. Saves JSON to /app/recurring_payments.json (EFS volume)    │
│  3. Runs Python scripts to generate HTML reports               │
│  4. Saves HTML to /app/*.html (EFS volume)                     │
│  5. Web server pods see new files (same EFS volume mounted)    │
└─────────────────────────────────────────────────────────────────┘
```

## Key Security Points

### 1. No Manual Credentials Needed

You **never** have to:
- Copy your personal kubeconfig into the container
- Create access keys or tokens manually
- Store credentials in environment variables
- Mount secret files

Kubernetes handles **all** credential management automatically.

### 2. Least Privilege

The ServiceAccount has **only** the permissions it needs:

```yaml
# Can do:
✓ Get pods in hedgeye-apps-vf4dc namespace
✓ List pods in hedgeye-apps-vf4dc namespace
✓ Exec into pods in hedgeye-apps-vf4dc namespace

# Cannot do:
✗ Delete pods
✗ Modify pods
✗ Access other namespaces
✗ Create/delete deployments
✗ Access secrets
✗ Modify RBAC rules
```

### 3. Automatic Token Rotation

Kubernetes automatically rotates ServiceAccount tokens periodically. You never have to worry about expired credentials.

### 4. Audit Trail

All kubectl exec operations are logged by the Kubernetes API server:
- Who (which ServiceAccount)
- What (exec into which pod)
- When (timestamp)
- Result (success/failure)

## Testing the Connection

You can verify the ServiceAccount has the correct permissions **before** deploying the cronjob:

```bash
# Test if the ServiceAccount can exec into admin-web pods
kubectl auth can-i create pods/exec \
  --as=system:serviceaccount:cyber-sales:cyber-sales-data-fetcher \
  -n hedgeye-apps-vf4dc

# Should return: yes
```

```bash
# Test if the ServiceAccount can delete pods (should be denied)
kubectl auth can-i delete pods \
  --as=system:serviceaccount:cyber-sales:cyber-sales-data-fetcher \
  -n hedgeye-apps-vf4dc

# Should return: no
```

## Debugging Connection Issues

If the cronjob can't connect to admin-web, check:

### 1. ServiceAccount Exists

```bash
kubectl get serviceaccount -n cyber-sales cyber-sales-data-fetcher
```

### 2. RBAC Bindings Exist

```bash
kubectl get role -n hedgeye-apps-vf4dc admin-pod-exec
kubectl get rolebinding -n hedgeye-apps-vf4dc cyber-sales-can-exec-admin
```

### 3. Token is Mounted

Exec into the cronjob pod and check:

```bash
kubectl exec -it <cronjob-pod> -n cyber-sales -- ls -la /var/run/secrets/kubernetes.io/serviceaccount/

# Should show:
# ca.crt
# namespace
# token
```

### 4. kubectl Can Reach API Server

From inside the cronjob pod:

```bash
kubectl exec -it <cronjob-pod> -n cyber-sales -- kubectl cluster-info

# Should show Kubernetes API server URL
```

### 5. Permissions Are Correct

From inside the cronjob pod:

```bash
kubectl exec -it <cronjob-pod> -n cyber-sales -- \
  kubectl auth can-i create pods/exec -n hedgeye-apps-vf4dc

# Should return: yes
```

## Comparison: ServiceAccount vs Personal kubeconfig

| Aspect | ServiceAccount (cronjob) | Personal kubeconfig (your laptop) |
|--------|--------------------------|-----------------------------------|
| **Credentials** | Auto-generated token | AWS IAM / OIDC token |
| **Location** | Auto-mounted by K8s | ~/.kube/config file |
| **Rotation** | Automatic | Manual (aws eks update-kubeconfig) |
| **Permissions** | RBAC (limited) | Cluster admin (usually) |
| **Scope** | Single namespace | Cluster-wide |
| **Audit** | ServiceAccount name | Your username |
| **Expiration** | Auto-renewed | Can expire (need re-auth) |
| **Security** | Least privilege | High privilege |

## Why This Design?

Kubernetes uses ServiceAccounts for pods because:

1. **Security**: Each pod gets only the permissions it needs
2. **Automation**: No manual credential management
3. **Rotation**: Credentials rotate automatically
4. **Audit**: Clear trail of which service did what
5. **Isolation**: Compromised pod can't do more than its ServiceAccount allows
6. **Portability**: Same pod works in any Kubernetes cluster (no hardcoded credentials)

## Summary

**The cronjob authenticates to Kubernetes using:**
1. A **ServiceAccount** (identity)
2. An **auto-generated token** (credential)
3. **RBAC rules** (permissions)

**You never have to:**
- Create credentials manually
- Mount your personal kubeconfig
- Store secrets in environment variables

**Kubernetes automatically:**
- Generates tokens
- Mounts them into pods
- Rotates them periodically
- Validates them for every API request

**kubectl inside the pod:**
- Automatically finds the token at `/var/run/secrets/kubernetes.io/serviceaccount/token`
- Uses it to authenticate to the Kubernetes API
- Sends exec requests to admin-web pod
- Streams results back to cronjob

This is the **standard Kubernetes pattern** for pod-to-pod communication and pod-to-API authentication. It's secure, automatic, and requires zero manual credential management.

---

**Last Updated:** November 14, 2025
**Environment:** Production Kubernetes
**Created By:** Forrest Chang
