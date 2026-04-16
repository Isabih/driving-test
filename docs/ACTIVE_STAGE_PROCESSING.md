# Active Stage Processing Logic

Only one bike enters the exam at a time, and only one stage should be active.

## Logic

1. Operator starts exam
2. Backend sets `current_stage_key = figure_8`
3. Vision service activates only Stage 1 cameras
4. On stage completion:
   - Stage 1 status becomes `finished`
   - Backend transitions exam to `zigzag`
   - Vision service closes Stage 1 streams
   - Vision service opens Stage 2 streams
5. Repeat until Stage 4 is finished
6. Exam ends and all processing for that exam stops

## Why this is best

- lower GPU/CPU load
- less bandwidth
- simpler operator workflow
- easier event attribution per stage
- matches the physical exam process
