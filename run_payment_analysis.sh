#!/bin/bash

# Script to run recurring payment analysis on production admin-web pod
# This script:
# 1. Finds the first admin-web pod in production
# 2. Copies the Ruby analysis script to the pod
# 3. Executes it via rails runner
# 4. Retrieves the JSON and CSV results

set -e  # Exit on error

CONTEXT="production"
NAMESPACE="hedgeye-apps-vf4dc"
SCRIPT_NAME="recurring_payment_analysis.rb"

echo "=== Recurring Payment Analysis Runner ==="
echo ""

# Find the first admin-web pod
echo "Finding admin-web pod in ${NAMESPACE} (${CONTEXT})..."
POD_FULL=$(kubectl get pods -n ${NAMESPACE} --context ${CONTEXT} -o name | grep admin-web | head -1)

if [ -z "$POD_FULL" ]; then
  echo "ERROR: No admin-web pod found in namespace ${NAMESPACE}"
  exit 1
fi

# Strip the "pod/" prefix
POD=$(echo ${POD_FULL} | sed 's/^pod\///')

echo "Found pod: ${POD}"
echo ""

# Copy the Ruby script to the pod
echo "Copying ${SCRIPT_NAME} to pod..."
kubectl cp ${SCRIPT_NAME} ${POD}:/tmp/${SCRIPT_NAME} --context ${CONTEXT} -n ${NAMESPACE}
echo "✓ Script copied"
echo ""

# Execute via rails runner
echo "Executing analysis via rails runner..."
echo "This may take a few minutes depending on the data volume..."
echo ""
kubectl exec ${POD} --context ${CONTEXT} -n ${NAMESPACE} -- bin/rails runner /tmp/${SCRIPT_NAME}
echo ""
echo "✓ Analysis complete"
echo ""

# Retrieve the JSON file
echo "Retrieving results..."
kubectl cp ${POD}:/tmp/recurring_payments.json ./recurring_payments.json --context ${CONTEXT} -n ${NAMESPACE}
echo "✓ Retrieved recurring_payments.json"

# Retrieve the CSV file
kubectl cp ${POD}:/tmp/recurring_payments.csv ./recurring_payments.csv --context ${CONTEXT} -n ${NAMESPACE}
echo "✓ Retrieved recurring_payments.csv"

echo ""
echo "=== SUCCESS ==="
echo "Files available:"
echo "  - recurring_payments.json"
echo "  - recurring_payments.csv"
echo ""
echo "Next step: Run 'python3 generate_analysis.py' to create the visualization"
