#!/usr/bin/env python3
# clean_json.py
# Usage: python clean_json.py input.jsonl cleaned.jsonl

import sys, json

REQUIRED_RESPONSE_KEYS = {
    "situation_assessment",
    "immediate_actions",
    "evacuation_and_shelter",
    "medical_and_critical_infra",
    "long_term_strategies",
}

def validate_record(obj):
    """Strict Phase-3 schema validation."""
    if not isinstance(obj, dict):
        return False, "not a JSON object"
    if "instruction" not in obj or "context" not in obj or "response" not in obj:
        return False, "missing top-level keys"
    resp = obj["response"]
    if not isinstance(resp, dict):
        return False, "response is not an object"
    missing = REQUIRED_RESPONSE_KEYS - set(resp.keys())
    if missing:
        return False, f"response missing keys: {', '.join(sorted(missing))}"
    return True, None

def clean_jsonl(in_path, out_path, err_path="clean_errors.txt"):
    valid_count, invalid_count = 0, 0
    errors = []

    with open(in_path, "r", encoding="utf-8", errors="replace") as f, \
         open(out_path, "w", encoding="utf-8") as fo:
        for i, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except Exception as e:
                errors.append((i, "JSON parse error", str(e), s[:200]))
                continue

            ok, reason = validate_record(obj)
            if ok:
                fo.write(json.dumps(obj, ensure_ascii=False) + "\n")
                valid_count += 1
            else:
                errors.append((i, "Schema validation error", reason, s[:200]))
                invalid_count += 1

    with open(err_path, "w", encoding="utf-8") as fe:
        for e in errors[:1000]:  # keep log manageable
            fe.write(f"Line {e[0]} | {e[1]} | {e[2]} | {e[3]}\n")

    print(f"✅ Saved {valid_count} valid records to {out_path}")
    print(f"❌ {invalid_count} invalid records (see {err_path})")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python clean_json.py <input.jsonl> <output.jsonl>")
        sys.exit(1)
    in_file = sys.argv[1]
    out_file = sys.argv[2]
    clean_jsonl(in_file, out_file)
