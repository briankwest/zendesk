#!/bin/bash

# Base URL for the swaig_cli
BASE_URL="https://server.ngrok.io/swaig"

# Test case for creating a new Zendesk ticket
swaig_cli --url $BASE_URL --function create_ticket --json '{
  "subject": "Test Ticket",
  "comment_body": "This is a test ticket.",
  "requester_name": "John Doe",
  "requester_email": "john.doe@example.com",
  "priority": "high"
}'

# Test case for updating an existing Zendesk ticket
swaig_cli --url $BASE_URL --function update_ticket --json '{
  "ticket_id": 12345,
  "status": "open",
  "priority": "urgent",
  "comment_body": "Updating the ticket with additional information.",
  "public": true
}'

# Test case for closing a Zendesk ticket
swaig_cli --url $BASE_URL --function close_ticket --json '{
  "ticket_id": 12345
}'

# Test case for adding a comment to a Zendesk ticket
swaig_cli --url $BASE_URL --function add_comment --json '{
  "ticket_id": 12345,
  "public": false
}'

# Test case for retrieving details of a Zendesk ticket
swaig_cli --url $BASE_URL --function get_ticket --json '{
  "ticket_id": 12345
}'

# Test case for verifying a support PIN for a user
swaig_cli --url https://admin:password@briankwest.ngrok.io/swaig --function verify_support_pin --json '{
  "caller_phone_number": "+19184249378",
  "entered_pin": 123456
}'

# Test case for retrieving ticket numbers for the authenticated user
swaig_cli --url $BASE_URL --function get_current_user_tickets --json '{
  "caller_phone_number": "+1234567890",
  "status": "open",
  "priority": "high"
}'