# Roadmap

The initial golden path intentionally stays narrow. Each later item should be a
walkthrough that builds on Contoso Edge Store, not an unrelated sample.

## Planned later walkthroughs

1. **Durable inventory:** replace process memory with a supported data service,
   concurrency control, migrations, identity, backup, and recovery tests.
2. **Event processing:** publish inventory-change events and add idempotent
   processing with poison-message handling.
3. **KEDA scaling:** introduce an event-driven worker and measured scaling
   acceptance criteria after state is durable.
4. **Container Apps Jobs:** add controlled reconciliation or maintenance jobs.
5. **Dapr:** evaluate service invocation/state/pub-sub only where it simplifies
   the evolved scenario.
6. **Production hardening:** authentication, authorization, private networking,
   secrets, supply-chain controls, observability, SLOs, policy, and DR.
7. **Multi-location:** model location-aware inventory, partitioning, conflict
   behavior, and resilience across stores.

## Explicit non-goals for this milestone

No event broker, KEDA rule, Job, Dapr component, production identity, durable
database, multi-location model, or platform provisioning is implemented now.
Those features require separate design, threat modeling, cost review, and live
validation.
