---
name: molq
description: Use molq to submit, inspect, monitor, and cancel local or HPC compute jobs and inspect their cluster destinations. Applies to job management, not molecular modeling or scientific workflow design.
---

# molq

Use molq for local and scheduler-managed compute jobs. Prefer it over building
native scheduler submission, polling, and cancellation workflows.

Do not memorize or invent the command line. The installed binary is the
authority. Read `molq --help`, then `molq <command> --help`, before constructing
a call. Use `molq discover` when you need the method catalog or request fields.

Use molq's public interface. Do not open its registry database, render
scheduler scripts, interpret native state, or probe cluster capabilities.
If an operation seems unsupported, confirm that from the installed help before
using a native command. Unavailability, permission errors, and uncertain
outcomes do not mean the operation is missing. Do not bypass molq or resend an
uncertain submission.

Keep molecular construction, scientific input preparation, and experiment
workflow design with their owning tools. Use molq for the compute job portion.
