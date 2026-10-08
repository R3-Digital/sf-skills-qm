#!/bin/sh
# Re-apply the QM size trims after refreshing skills/ from upstream forcedotcom/sf-skills.
# Run from the repo root. Idempotent. See README.md "QM size trims".
set -eu
D=skills/platform-data-and-tooling-api-context-get
# 1. data/tooling skill: drop the offline per-object JSON corpus (agents use `sf sobject describe`)
rm -rf "$D/assets" "$D/examples"
# 2. metadata skill: replace raw wsdl_segment with compact wsdl_enums / wsdl_types, write compact JSON
python3 tools/slim_metadata_json.py skills/platform-metadata-api-context-get/assets/metadata_api
# 3. keep the QM-edited docs (upstream versions describe the removed files)
for f in "$D/SKILL.md" "$D/references/usage_guide.md" "$D/references/data_and_tooling_index_table.md" \
         skills/platform-metadata-api-context-get/SKILL.md skills/platform-metadata-api-context-get/README.md \
         skills/platform-metadata-api-context-get/references/usage_guide.md \
         skills/platform-metadata-api-context-get/references/metadata_index_table.md \
         skills/platform-metadata-api-context-get/examples/README.md; do
  git checkout HEAD -- "$f" 2>/dev/null || echo "warn: could not restore QM version of $f (review upstream changes by hand)"
done
du -sh "$D" skills/platform-metadata-api-context-get
