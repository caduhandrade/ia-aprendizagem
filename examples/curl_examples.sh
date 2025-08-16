#!/bin/bash

# IA Aprendizagem API - Curl Examples
# Make sure the API server is running on localhost:49152

echo "🚀 IA Aprendizagem API Examples"
echo "==============================="

API_BASE="http://localhost:49152"

echo "1. Health Check"
echo "curl -X GET $API_BASE/health"
curl -X GET "$API_BASE/health" | jq
echo -e "\n"

echo "2. Create Session"
echo "curl -X POST $API_BASE/sessions"
SESSION_RESPONSE=$(curl -s -X POST "$API_BASE/sessions")
SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')
echo $SESSION_RESPONSE | jq
echo "Session ID: $SESSION_ID"
echo -e "\n"

echo "3. Ask Question (without session)"
echo "curl -X POST $API_BASE/ask -H 'Content-Type: application/json' -d '{\"query\":\"Hello!\"}'"
curl -X POST "$API_BASE/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"Hello!"}' \
  --max-time 5
echo -e "\n\n"

echo "4. Ask Question with Session"
echo "curl -X POST $API_BASE/ask -H 'Content-Type: application/json' -d '{\"query\":\"What is AI?\",\"session_id\":\"$SESSION_ID\"}'"
curl -X POST "$API_BASE/ask" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"What is AI?\",\"session_id\":\"$SESSION_ID\"}" \
  --max-time 5
echo -e "\n\n"

echo "5. Follow-up Question"
echo "curl -X POST $API_BASE/ask -H 'Content-Type: application/json' -d '{\"query\":\"Tell me more\",\"session_id\":\"$SESSION_ID\"}'"
curl -X POST "$API_BASE/ask" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Tell me more\",\"session_id\":\"$SESSION_ID\"}" \
  --max-time 5
echo -e "\n\n"

echo "6. Get Session History"
echo "curl -X GET $API_BASE/sessions/$SESSION_ID/history"
curl -X GET "$API_BASE/sessions/$SESSION_ID/history" | jq
echo -e "\n"

echo "7. Delete Session"
echo "curl -X DELETE $API_BASE/sessions/$SESSION_ID"
curl -X DELETE "$API_BASE/sessions/$SESSION_ID" | jq
echo -e "\n"

echo "✅ Examples completed!"