#!/bin/bash

# Analyze a specific Cyber November year
# Usage: ./analyze_cyber_november.sh 2023
#        ./analyze_cyber_november.sh 2024
#        ./analyze_cyber_november.sh 2025

set -e  # Exit on error

YEAR=$1

if [ -z "$YEAR" ]; then
    echo "ERROR: Please specify a year"
    echo "Usage: $0 YEAR"
    echo "Example: $0 2024"
    exit 1
fi

CONTEXT="production"
NAMESPACE="hedgeye-apps-vf4dc"
SCRIPT_NAME="recurring_payment_analysis.rb"

echo "======================================"
echo "  Cyber November $YEAR Analysis"
echo "======================================"
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

# Execute via rails runner with CYBER_YEAR env var
echo "Executing analysis for Cyber November ${YEAR}..."
kubectl exec ${POD} --context ${CONTEXT} -n ${NAMESPACE} -- bash -c "CYBER_YEAR=${YEAR} bin/rails runner /tmp/${SCRIPT_NAME}"
echo ""
echo "✓ Analysis complete"
echo ""

# Retrieve the JSON file
echo "Retrieving results..."
kubectl cp ${POD}:/tmp/recurring_payments.json ./recurring_payments_${YEAR}.json --context ${CONTEXT} -n ${NAMESPACE}
echo "✓ Retrieved recurring_payments_${YEAR}.json"

# Retrieve the CSV file
kubectl cp ${POD}:/tmp/recurring_payments.csv ./recurring_payments_${YEAR}.csv --context ${CONTEXT} -n ${NAMESPACE}
echo "✓ Retrieved recurring_payments_${YEAR}.csv"

echo ""
echo "Generating visualization for ${YEAR}..."
python3 generate_analysis.py recurring_payments_${YEAR}.json recurring_payment_analysis_${YEAR}.html
echo ""

echo "======================================"
echo "  ✓ COMPLETE - Cyber November ${YEAR}"
echo "======================================"
echo ""
echo "Files generated:"
echo "  - recurring_payments_${YEAR}.json"
echo "  - recurring_payments_${YEAR}.csv"
echo "  - recurring_payment_analysis_${YEAR}.html"
echo ""
