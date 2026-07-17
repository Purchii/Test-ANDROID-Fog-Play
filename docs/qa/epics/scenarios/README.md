# TASK-041…055 scenario catalogs

Total rows: `307`.

Schema fields:

```text
scenario_id
priority
surface_ids
lane
category
title
preconditions
steps
expected_oracle
negative_or_boundary
automation_target
evidence_required
safety_class
blocking_rule
```

Scenario IDs are immutable. Deletion or semantic repurposing requires a migration
record. New rows may be appended with unique IDs.

All P0 rows must be implemented and terminally classified in their task.
