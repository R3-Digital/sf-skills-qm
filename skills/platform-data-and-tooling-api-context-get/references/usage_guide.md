# Data + Tooling API Skill: Usage Guide

Supplementary reference for `platform-data-and-tooling-api-context-get`. Load only when
needed; the core rules live in `SKILL.md`. All field facts come from a live
`sf sobject describe` of the target org (QM slim copy: the offline JSON corpus was removed).

## Worked Examples

### Example 1: Build a filtered SOQL query

**User**: "Query open high-value opportunities with their account name."

1. `sf sobject describe --sobject Opportunity --target-org <alias> --json > /tmp/Opportunity.describe.json`
2. Confirm the fields you need:
   ```bash
   jq '.result.fields[] | select(.name | IN("Amount","IsClosed","AccountId"))
       | {name, type, filterable, sortable, relationshipName, referenceTo}' /tmp/Opportunity.describe.json
   ```
   `Amount` (filterable, sortable), `IsClosed` (filterable), `AccountId`
   (reference, relationshipName = `Account`).
3. Generate:
   ```sql
   SELECT Id, Name, Amount, Account.Name
   FROM Opportunity
   WHERE IsClosed = false AND Amount > 100000
   ORDER BY Amount DESC
   ```

### Example 2: Safe DML (respect read-only fields)

**User**: "Update the account rating and its formula health score."

1. Describe Account and check `updateable` / `calculated` for both fields.
2. `Rating` is updateable. A formula field has `calculated: true` and
   `updateable: false`, so setting it fails. Only include writable fields in the
   `update` payload.

### Example 3: Tooling API code coverage

**User**: "What fields give per-class Apex code coverage?"

1. `sf sobject describe --sobject ApexCodeCoverageAggregate --use-tooling-api --target-org <alias> --json | jq -r '.result.fields[] | "\(.name)\t\(.type)"'`
2. Note `NumLinesCovered`, `NumLinesUncovered`, `ApexClassOrTriggerId` (use the exact
   casing the describe returns).
3. Query via the Tooling endpoint: `sf data query --use-tooling-api --query "SELECT ..." --target-org <alias>`.

## Relationship Traversal

- Parent (child to parent): use `relationshipName`: `Owner.Name`, `Account.Industry`.
- Custom lookups: `__c` id field, traverse with `__r` (`Foo__r.Name`).
- Child (parent to children): use `childRelationships[].relationshipName` in a subquery,
  e.g. `SELECT Id, (SELECT Id FROM Contacts) FROM Account`.
- Polymorphic (`WhoId`, `WhatId`, `OwnerId` on some objects): `referenceTo` lists
  several targets; use `TYPEOF` for target-specific fields.

## Describe Field Properties Cheat Sheet

| Describe key | Enables |
|---|---|
| `createable` | set on `insert` |
| `updateable` | set on `update` |
| `filterable` | use in `WHERE` |
| `sortable` | use in `ORDER BY` |
| `groupable` | use in `GROUP BY` |
| `nillable` | may be null (non-nillable and not `defaultedOnCreate` = required on insert) |
| `externalId` | can be the `upsert` match field |
| `calculated` | formula or roll-up field, read-only |
| `picklistValues` | allowed values for this org (check `.active`) |

## Object catalogue

`references/data_and_tooling_index_table.md` lists the standard object names known
at API 67.0 per surface. Grep it for a name sanity check; it carries no field data.
