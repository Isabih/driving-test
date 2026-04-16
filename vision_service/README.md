# Vision Service Skeleton

This service is intentionally lightweight. It demonstrates the control loop for stage-aware processing.

## What it does

- polls the backend for `GET /live/exams/{exam_id}/stage-view`
- reads the currently active stage
- prints which cameras should be active
- is ready for you to attach your actual OpenCV / detector logic

## Intended production behavior

- only open and analyze streams for the active stage
- close previous stage streams immediately after transition
- generate snapshots and post events to `/exams/{exam_id}/stages/{stage_key}/events`
- upload evidence to `/exams/{exam_id}/events/{event_id}/evidence`
