# Recovery Requirements

Recovery must not depend on the candidate policy functioning correctly.

Before any host activation, the following must be documented and rehearsed:

- a boot path that does not load the candidate policy;
- access to the previous known-good signed package;
- a way to identify the installed package and loaded profile revisions;
- commands to return selected profiles to complain mode or unload them;
- a way to restore policy files and repository configuration;
- offline access to the instructions;
- preservation of relevant logs without publishing sensitive contents; and
- independent readback after rollback.

Recovery instructions must name exact targets. They must not use destructive
wildcards, broad recursive deletion, or assume that networking and the normal
desktop are available.

This document is a requirements statement, not a host recovery procedure.
Host-specific commands will be added only after they are tested in the intended
recovery environment.
