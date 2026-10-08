---
name: platform-data-and-tooling-api-context-get
description: "Field/schema lookup for Salesforce sObjects and Tooling API records via a LIVE describe of the target org (sf sobject describe). Use to verify field API names, types, properties (createable/updateable/filterable/sortable/groupable/nillable), picklist values and relationship names for Account, Contact, Opportunity, Lead, Case, ApexClass, ApexCodeCoverage, TraceFlag, custom __c objects and more. Load this alongside a SOQL/query/Apex skill when the field names, types, or Filter/Sort/Group capabilities are unverified, not when the fields are already known and only query syntax or optimization is needed. TRIGGER when verifying, validating, or debugging fields in a SOQL/SOSL query or DML (capabilities, relationship/subquery paths, or what fields an object has) so the query runs instead of guessing. DO NOT TRIGGER for authoring/deploying *-meta.xml or sfdx source (use the Metadata API skill)."
metadata:
  version: "1.1-qm"
  domains: ["Platform"]
  minApiVersion: "67.0"
  relatedSkills:
    - "platform-metadata-api-context-get"
  cliTools:
    - tool: ["sf"]
      semver: ">=2.0.0"
    - tool: ["jq"]
      semver: ">=1.6"
---

# Salesforce Data + Tooling API Skill (live describe)

Use this skill to get authoritative field names, types and properties **before**
writing SOQL/SOSL, building DML, or reading records at runtime, so queries and
writes don't fail with `INVALID_FIELD` / "No such column" errors.

It covers two runtime API surfaces:

- **Enterprise/Data API**: standard and custom sObjects you query with SOQL and
  modify with DML (Account, Contact, Opportunity, Lead, Case, `My_Object__c`, ...).
- **Tooling API**: developer/metadata-adjacent records (`ApexClass`,
  `ApexCodeCoverageAggregate`, `TraceFlag`, `EntityDefinition`,
  `MetadataComponentDependency`, `SymbolTable`, ...).

> **QM note:** this slim copy no longer ships the offline per-object JSON corpus
> (about 17 MB, 2,130 files). Field details come from describing the target org
> with the Salesforce CLI, which is also more accurate: it reflects the org's API
> version, installed packages, custom fields and the running user's access.
> [`references/data_and_tooling_index_table.md`](references/data_and_tooling_index_table.md)
> is kept only as a catalogue of standard object names per API surface.

> **This skill is for runtime data, not deployment.** For authoring `*-meta.xml`
> source files (CustomObject, Flow, Profile, ...) use the **Metadata API** skill
> (`platform-metadata-api-context-get`). The two are companions, not substitutes.

## How to Use This Skill

### CRITICAL: Field-Existence Gate (do this BEFORE answering)

**NEVER answer a field question ("does field X exist?", "is X filterable?", "what's
X's API name/type?") from memory or training data.** This includes obvious system
fields like `Id`, `Name`, `CreatedDate`, `OwnerId`. Describe the object in the target
org first. Confidence is not verification.

Pick the org: use the alias the user or project names (`--target-org <alias>`), or
the project's default org (`sf config get target-org`). If no org is authorised,
say so and ask, rather than guessing. Never authorise against a production org just
to run a describe unless the user asked for that org.

**Data API object, one field (atomic):**

```bash
sf sobject describe --sobject <Object> --target-org <alias> --json \
  | jq '.result.fields[] | select(.name == "<FieldName>")
        | {name, type, label, createable, updateable, filterable, sortable,
           groupable, nillable, defaultedOnCreate, externalId, calculated,
           relationshipName, referenceTo, length, picklistValues: [.picklistValues[]?.value]}'
```

**Tooling API object:** add `--use-tooling-api` (short form `-t`):

```bash
sf sobject describe --sobject ApexCodeCoverageAggregate --use-tooling-api --target-org <alias> --json \
  | jq '[.result.fields[] | {name, type, filterable}]'
```

Interpret the result: a field object back means it exists for that org and user,
and its booleans answer the capability question. Empty output means the field is
not on that object for this org/user (check spelling and exact casing, then the
object name, then field-level security: describe only returns fields the running
user can see).

**MANDATORY VERIFICATION GATE.** Before you state any field fact, print this line
verbatim in your reply to the user:

```text
field_lookup: object=<Object> field=<FieldName> api=<data|tooling> org=<alias> result=<found|not_found>
```

If you cannot print this line truthfully, you have not done the lookup; stop and run
the describe. Keep the gate line out of files you generate for the user (`.soql`,
`.md`, `.json`, query comment headers, etc.).

### Keep describe output small

Describe JSON for large objects (Account, Opportunity, User) is hundreds of KB.
**Always pipe through `jq` and select only what you need**; never print or load the
whole response. Useful filters:

```bash
# all field names + types
... --json | jq -r '.result.fields[] | "\(.name)\t\(.type)"'
# filterable fields only
... --json | jq -r '.result.fields[] | select(.filterable) | .name'
# writable on insert / update
... --json | jq -r '.result.fields[] | select(.createable) | .name'
... --json | jq -r '.result.fields[] | select(.updateable) | .name'
# reference fields with relationship name and targets
... --json | jq -r '.result.fields[] | select(.type == "reference") | "\(.name)\t\(.relationshipName)\t\(.referenceTo | join(","))"'
# child relationships (for parent-to-child subqueries)
... --json | jq -r '.result.childRelationships[] | select(.relationshipName) | "\(.relationshipName)\t\(.childSObject)"'
# object-level flags
... --json | jq '.result | {name, queryable, createable, updateable, deletable, searchable, custom}'
```

If you need several lookups on one object, save the describe once to a temp file
(`> /tmp/<Object>.describe.json`) and run `jq` against it.

### Which API?

- **Standard and custom sObjects** you query and modify at runtime: plain
  `sf sobject describe --sobject <Name>`.
- **Developer / diagnostics records** (ApexClass, ApexCodeCoverageAggregate,
  TraceFlag, EntityDefinition, MetadataComponentDependency, SymbolTable): add
  `--use-tooling-api`. Some names exist on both surfaces with different fields
  (e.g. ApexClass); describe the surface you will query.
- **Does the object exist in this org?** `sf sobject list --sobject all --target-org <alias>`
  (Data API) and grep the output. For a standard-name sanity check without an org,
  `grep -i "<ObjectName>" references/data_and_tooling_index_table.md`.

### No org available?

If no org can be described, say that the field facts are unverified, and either ask
for an org alias or give the answer clearly labelled as unverified. Do not present
remembered field properties as checked.

> **More detail:** worked query/DML examples, relationship-traversal patterns and a
> property cheat sheet live in [`references/usage_guide.md`](references/usage_guide.md).
> Load it only when needed.

## Query & DML Generation Requirements

### Verify the field exists and its API name

1. **Describe first and print the `field_lookup:` gate line**, even for system fields.
   Field API names are case-insensitive to Salesforce but must resolve to a real field.
   Custom fields end in `__c`; custom relationships traverse with `__r`.
2. **Do not invent fields.** A guessed column produces
   `INVALID_FIELD: No such column 'X' on entity 'Y'`.
3. **Match exact casing from describe output.** A few objects (e.g. `LoginEventLog`)
   have two distinct fields whose names differ only by case (`UserName`, `Username`).
   Treat them as different columns.

### Respect field properties

Describe booleans control what you can do with a field:

- `filterable` → usable in `WHERE`.
- `sortable` → usable in `ORDER BY`.
- `groupable` → usable in `GROUP BY`.
- `createable` / `updateable` → settable via `insert` / `update`. Formula
  (`calculated: true`) and system fields are read-only.
- `nillable: false` and `defaultedOnCreate: false` → required on insert.
- `externalId: true` → usable as the match field for `upsert`.
- `picklistValues` → active and inactive values for the org (check `.active`).

### Relationships

For `reference` fields, `relationshipName` gives the parent relationship for SOQL
traversal and `referenceTo` lists the target object(s). Parent-to-child subqueries
use `childRelationships[].relationshipName`.

```sql
-- OwnerId (reference, relationshipName = Owner, referenceTo = [User])
SELECT Id, Owner.Name FROM Account
-- Custom lookup Foo__c traverses as Foo__r
SELECT Id, Foo__r.Name FROM My_Object__c
-- Child relationship from childRelationships
SELECT Id, (SELECT Id FROM Contacts) FROM Account
```

Polymorphic fields (`WhoId`, `WhatId`, some `OwnerId`) list several `referenceTo`
targets; use `TYPEOF` for target-specific fields.

### Tooling API vs Data API

Tooling records are queried through the **Tooling API** endpoint
(`/services/data/vXX.0/tooling/query`, or `sf data query --use-tooling-api`), not the
regular Data API. Many Tooling objects are read-only, and some (for example
`MetadataComponentDependency`) impose record caps and do not support `ORDER BY`,
`OFFSET` or `queryMore()`; check the Salesforce Tooling API reference when a query
fails on clauses rather than fields.

> **Not for deployment.** To author or edit `*-meta.xml` source use the Metadata API
> skill. The objects here are the runtime/queryable representation.

## Duplicate and Ambiguous Object Names

Several names exist in BOTH the Metadata API and here (ApexClass, ApexTrigger,
CustomField, CustomObject, EmailTemplate, Layout, Profile, PermissionSet,
RecordType, ValidationRule, Flow, ...). They mean different things:

- **This skill** = the runtime/queryable record: fields you `SELECT`, filter, and
  (sometimes) write via the Data or Tooling API.
- **Metadata API skill** = the `*-meta.xml` source form you author and deploy.

Signals: "query", "SOQL", "SOSL", "DML", "insert/update/upsert", "what
fields/columns", "filterable", "record", "runtime", "REST/SOAP" → **this skill**.
"authoring", "deploy", "retrieve", `package.xml`, `force-app/`, `.meta.xml` →
**Metadata API skill**. "Tooling API", `ApexCodeCoverage`, `EntityDefinition`,
`TraceFlag`, "code coverage", "debug log" → Tooling half of **this skill**.

If invoked directly by name with no other signal, default to the runtime data
interpretation and disclose the assumption.

## Troubleshooting

### `NOT_FOUND` / "The requested resource does not exist" on describe

- Object names are case-sensitive PascalCase API names (`Account`, `ApexClass`);
  custom objects need the `__c` suffix (and namespace prefix for packaged objects).
- Try the other surface (`--use-tooling-api` on or off).
- The object may need a feature or licence the org doesn't have, or the running user
  lacks access. Check with `sf sobject list --sobject all`.

### INVALID_FIELD / No such column

- Wrong API name, or the field is hidden from the running user by field-level
  security. Re-run the describe and confirm the exact name.
- The field exists but lacks the needed property (filtering a non-filterable field,
  sorting a non-sortable one, writing a read-only one).

### Relationship query fails

- Traverse with `relationshipName` (`Owner.Name`, not `OwnerId.Name`). Custom
  lookups traverse with `__r`.
- Polymorphic fields need `TYPEOF` or the correct relationship.

### Tooling query returns nothing / errors

- Query the Tooling endpoint (`sf data query --use-tooling-api`), not the Data API.

## Common Objects

### Enterprise / Data API (SOQL + DML)

- **Account**, **Contact**, **Opportunity**, **Lead**, **Case**, **User**, **Task**, **Event**

### Tooling API (developer records)

- **ApexClass**, **ApexTrigger**, **ApexCodeCoverageAggregate**, **TraceFlag**, **EntityDefinition**
