# sf-skills-qm (slim)

Slim mirror of [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) for YC QM skill-pack import.

QM pack limits: 5000 files / 32MB. Upstream repo is ~7k files / larger — this tree keeps skill markdown and small text assets only.

Source: forcedotcom/sf-skills (Apache/salesforce licensing per upstream).

## QM size trims (Oct 2026)

QM keeps every skill's files in its `skills` table and re-reads and copies that table every 30 seconds and on every turn. Two reference-heavy skills from this pack made up about 23MB of a 41MB table and were stalling QM core's event loop (health check flaps, Slack pong timeouts). They are trimmed here:

- `platform-data-and-tooling-api-context-get`: the offline per-object JSON corpus (`assets/enterprise_api`, `assets/tooling_api`, about 17MB, 2,130 files) and `examples/` were removed. `SKILL.md` now tells agents to describe the target org live with `sf sobject describe --sobject <Object> [--use-tooling-api] --target-org <alias> --json | jq ...`. The index table is kept as a catalogue of standard object names.
- `platform-metadata-api-context-get`: all 599 metadata types are kept, with fields, required flags, sub-types and sample XML. The raw `wsdl_segment` XSD text was replaced by compact digests: `wsdl_enums` (every enumeration's allowed values) and `wsdl_types` (complex types not documented in `fields`/`sub_types`, e.g. `CustomField` -> `ValueSet`, and the schema of result types like `AsyncResult`). JSON is written compact. About 5.5MB to 3.5MB.

There is no automated upstream sync in this repo; the tree was copied from upstream by hand. **After any refresh from forcedotcom/sf-skills, run `tools/apply_qm_slim.sh` before committing**, or the bulk comes back. It is idempotent.

To undo the trims, revert the trim commit (or PR) and re-sync the pack in QM.
