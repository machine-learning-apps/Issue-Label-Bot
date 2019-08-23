#!/bin/sh
curl -X POST -H "Content-Type: application/json" -H "X-GitHub-Event: issues" -H "X-Hub-Signature: sha1=fakedontneedfortesting" -d "@payload.json" http://localhost:3000/event_handler
curl -X POST -H "Content-Type: application/json" -H "X-GitHub-Event: issues" -H "X-Hub-Signature: sha1=fakedontneedfortesting" -d "@payload2.json" http://localhost:3000/event_handler