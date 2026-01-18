#!/data/data/com.termux/files/usr/bin/bash
echo "HHI Governance Maturity Report"
echo "================================"
while IFS=, read -r repo a d e ev c t; do
  [ "$repo" = "repo" ] && continue
  echo ""
  echo "Repo: $repo"
  echo "Score: $t / 10"
  if [ "$t" -ge 8 ]; then
    echo "Status: AUDIT-READY"
  elif [ "$t" -ge 5 ]; then
    echo "Status: SOFT GOVERNANCE"
  else
    echo "Status: NON-GOVERNED"
  fi
done < governance_scores.csv
