#!/bin/bash
# Read-only pull of plan pricing config (no customer data) from production admin-web.
set -e
CONTEXT="production"; NAMESPACE="hedgeye-apps-vf4dc"
POD=$(kubectl get pods -n ${NAMESPACE} --context ${CONTEXT} -o name | grep admin-web | head -1 | sed 's/^pod\///')
kubectl cp plan_pricing_analysis.rb ${POD}:/tmp/plan_pricing_analysis.rb --context ${CONTEXT} -n ${NAMESPACE}
kubectl exec ${POD} --context ${CONTEXT} -n ${NAMESPACE} -- bash -c "bin/rails runner /tmp/plan_pricing_analysis.rb"
kubectl cp ${POD}:/tmp/plan_pricings.json ./plan_pricings.json --context ${CONTEXT} -n ${NAMESPACE}
