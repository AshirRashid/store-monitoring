cut -d',' -f1 status.csv | sort -g | more | tail -n1 | wc -c
cut -d',' -f1 timezone.csv | sort -g | more | tail -n1 | wc -c
cut -d',' -f1 business_hours.csv | sort -g | more | tail -n1 | wc -c