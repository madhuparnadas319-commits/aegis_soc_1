# Existing AEGIS n8n workflow

Your `AEGIS SOC - Governed Investigation Workflow` already exists inside your
Docker n8n instance and has successfully executed the Autonomous and HITL
pathways. Do not replace it with a fabricated template.

In n8n, export **your actual workflow** to a JSON file and save it as:

`aegis-soc/workflows/aegis_soc_workflow.json`

The three routes are:

- `[A] Autonomous` → `Autonomous Outcome` → `Respond Autonomous`
- `[H] HITL` → `Human Review Queue` → `Respond HITL`
- `[E] Escalation` → `Escalation Queue` → `Respond Escalation`

All three `Respond to Webhook` nodes should use **First Incoming Item**.

The `/webhook-test/aegis-triage` URL only works while n8n is listening. For
regular dashboard use, publish the workflow and set `AEGIS_N8N_WEBHOOK_URL`
to its production URL. Never commit n8n credentials or private workflow tokens.

The Escalation branch has been constructed, but the user deliberately skipped
its final end-to-end live test. Do not describe it as verified until tested.
