#!/usr/bin/env bash

printf "Retrieving message..."
MESSAGE="$(aws sqs receive-message --queue-url "$SQS_QUEUE_URL")"
printf "Done.\n"
MESSAGE_BODY="$(echo "$MESSAGE" |jq -r '.Messages[].Body')"
RECEIPT_HANDLE="$(echo "$MESSAGE" |jq -r '.Messages[].ReceiptHandle')"
ACCOUNT_ID="$(echo "$MESSAGE_BODY" |jq -r '.AccountId')"
ROLE_TO_ASSUME="$(echo "$MESSAGE_BODY" |jq -r '.RoleToAssume')"
SESSION_DURATION="$(echo "$MESSAGE_BODY" |jq -r '.SessionDuration')"

if [ -z "$SESSION_DURATION" ]; then
  SESSION_DURATION=43200
fi

echo "Receipt handle: $RECEIPT_HANDLE"
echo "Message body: $MESSAGE_BODY"
echo "Account id: $ACCOUNT_ID"
echo "Role to assume: $ROLE_TO_ASSUME"
echo "Session duration: $SESSION_DURATION"

if [ -n "$RECEIPT_HANDLE" ]; then
  printf "Running prowler..."
  ./prowler -A "$ACCOUNT_ID" \
            -R "$ROLE_TO_ASSUME" \
            -T "$SESSION_DURATION" \
            -n \
            -M json,html
  printf "Uploading to S3 (bucket name: '%s')..." "$RESULTS_BUCKET"
  aws s3 cp output/prowler-output-${ACCOUNT_ID}-*.html s3://${RESULTS_BUCKET}/${ACCOUNT_ID}/ && printf "Done.\n" || printf "Failed.\n"
else
  echo "No message found. Exiting..."
  exit 0
fi

printf "Deleting message (receipt handle: '%s')..." "$RECEIPT_HANDLE"
aws sqs delete-message --queue-url "$SQS_QUEUE_URL" --receipt-handle "$RECEIPT_HANDLE" && printf "Done.\n" || printf "Failed.\n"
