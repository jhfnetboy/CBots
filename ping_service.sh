#!/bin/bash

# Script to periodically ping the PythonAnywhere web app to keep it alive.

URL="https://jhfnetboy.pythonanywhere.com/"
INTERVAL_SECONDS=900 # Ping every 15 minutes (900 seconds)

while true
do
  TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
  echo "[$TIMESTAMP] Pinging $URL ..."
  
  # Use curl to ping the URL, follow redirects (-L), silent mode (-s),
  # discard output (-o /dev/null), and print HTTP status code (-w). Timeout after 10s.
  STATUS_CODE=$(curl -L -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$URL")
  
  if [ "$STATUS_CODE" -eq 200 ]; then
    echo "[$TIMESTAMP] Ping successful (Status Code: $STATUS_CODE)"
  else
    echo "[$TIMESTAMP] Ping failed (Status Code: $STATUS_CODE)"
  fi
  
  echo "[$TIMESTAMP] Sleeping for $INTERVAL_SECONDS seconds..."
  sleep $INTERVAL_SECONDS
done 