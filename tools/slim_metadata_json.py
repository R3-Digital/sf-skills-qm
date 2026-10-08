#!/usr/bin/env python3
"""Slim platform-metadata-api-context-get per-type JSON for QM.

Replaces the verbose raw `wsdl_segment` XSD text with a compact structured digest and
writes compact JSON. Idempotent: files without `wsdl_segment` are only re-serialised.

Kept as-is: title, description, fields (incl. required flags), sub_types,
declarative_metadata_sample_definition, file_information, directory_location and any
other section.
Added from the WSDL before dropping it:
  wsdl_enums: {SimpleTypeName: [allowed values]}   every xsd:simpleType enumeration
  wsdl_types: {ComplexTypeName: {"extends": base?, "fields": {element: "type[] (required)"}}}
              only complex types whose fields are not already in this file (`fields` for
              the type itself, `sub_types`) or in another type's own file / sub_types,
              so nested types such as CustomField -> ValueSet stay resolvable.

usage: slim_metadata_json.py <assets/metadata_api dir> [--check]
"""
import glob, json, os, re, sys

CT = re.compile(r'<xsd:complexType name="([^"]+)">(.*?)</xsd:complexType>', re.S)
ST = re.compile(r'<xsd:simpleType name="([^"]+)">(.*?)</xsd:simpleType>', re.S)
EL = re.compile(r'<xsd:element\s+([^>]*?)/?>')
AT = re.compile(r'(\w+)="([^"]*)"')
EN = re.compile(r'<xsd:enumeration value="([^"]*)"')
EXT = re.compile(r'<xsd:extension base="([^"]+)"')


def strip_ns(t):
    return t.split(":", 1)[1] if ":" in t else t


def digest_type(body):
    out = {}
    m = EXT.search(body)
    if m:
        out["extends"] = strip_ns(m.group(1))
    fields = {}
    for em in EL.finditer(body):
        a = dict(AT.findall(em.group(1)))
        if "name" not in a:
            continue
        t = strip_ns(a.get("type", "?"))
        if a.get("maxOccurs") == "unbounded":
            t += "[]"
        if a.get("minOccurs", "1") != "0":
            t += " (required)"
        fields[a["name"]] = t
    out["fields"] = fields
    return out


def main():
    d = sys.argv[1]
    check = "--check" in sys.argv
    paths = sorted(glob.glob(os.path.join(d, "*.json")))
    docs = {p: json.load(open(p, encoding="utf-8")) for p in paths}
    own = {os.path.basename(p)[:-5] for p in paths}
    covered = set(own)
    for doc in docs.values():
        covered.update((doc.get("sub_types") or {}).keys())
    before = after = 0
    for p, doc in docs.items():
        before += os.path.getsize(p)
        w = doc.pop("wsdl_segment", None)
        if w:
            enums = {n: EN.findall(b) for n, b in ST.findall(w)}
            enums = {k: v for k, v in enums.items() if v}
            types = {}
            me = os.path.basename(p)[:-5]
            for n, b in CT.findall(w):
                if n == me and doc.get("fields"):
                    continue
                if n in covered and n != me:
                    continue
                types[n] = digest_type(b)
            if enums:
                doc["wsdl_enums"] = enums
            if types:
                doc["wsdl_types"] = types
            secs = [s for s in doc.get("sections", []) if s != "wsdl_segment"]
            for k in ("wsdl_types", "wsdl_enums"):
                if k in doc and k not in secs:
                    secs.append(k)
            if "sections" in doc:
                doc["sections"] = secs
        s = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
        after += len(s.encode())
        if not check:
            open(p, "w", encoding="utf-8").write(s + "\n")
    print(f"files={len(paths)} before={before} after={after}")


if __name__ == "__main__":
    main()
