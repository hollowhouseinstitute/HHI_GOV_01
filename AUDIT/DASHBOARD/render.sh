#!/data/data/com.termux/files/usr/bin/bash
echo "HHI Governance Audit Results"
echo "============================"
while IFS=, read -r s a d e ev c t; do
  [ "$s" = "system" ] && continue
  echo ""
  echo "System: $s"
  echo "Score: $t / 10"
  if [ "$t" -ge 8 ]; then
    echo "Status: AUDIT-READY"
  elif [ "$t" -ge 5 ]; then
    echo "Status: SOFT GOVERNANCE"
  else
    echo "Status: NON-GOVERNED"
  fi
done < scores.csv
