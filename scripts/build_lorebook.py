import os
import json
import re

ENTRY_DIR = "lorebook_entries"
OUTPUT_FILE = "lorebook.json"

# Default values taken from your example JSON
DEFAULT_FIELDS = {
    "keysecondary": [],
    "comment": "",
    "constant": False,
    "vectorized": False,
    "selective": True,
    "selectiveLogic": 0,
    "addMemo": True,
    "order": 100,
    "position": 0,
    "disable": False,
    "ignoreBudget": False,
    "excludeRecursion": False,
    "preventRecursion": False,
    "matchPersonaDescription": False,
    "matchCharacterDescription": False,
    "matchCharacterPersonality": False,
    "matchCharacterDepthPrompt": False,
    "matchScenario": False,
    "matchCreatorNotes": False,
    "delayUntilRecursion": False,
    "probability": 100,
    "useProbability": True,
    "depth": 4,
    "outletName": "",
    "group": "",
    "groupOverride": False,
    "groupWeight": 100,
    "scanDepth": None,
    "caseSensitive": None,
    "matchWholeWords": None,
    "useGroupScoring": None,
    "automationId": "",
    "role": None,
    "sticky": 0,
    "cooldown": 0,
    "delay": 0,
    "triggers": [],
    "characterFilter": {
        "isExclude": False,
        "names": [],
        "tags": []
    }
}

# Fields that can be overridden by text entries
OPTIONAL_FIELDS = {
    "KeySecondary": "keysecondary",
    "Comment": "comment",
    "Constant": "constant",
    "Vectorized": "vectorized",
    "Selective": "selective",
    "SelectiveLogic": "selectiveLogic",
    "AddMemo": "addMemo",
    "Order": "order",
    "Position": "position",
    "Disable": "disable",
    "IgnoreBudget": "ignoreBudget",
    "ExcludeRecursion": "excludeRecursion",
    "PreventRecursion": "preventRecursion",
    "MatchPersonaDescription": "matchPersonaDescription",
    "MatchCharacterDescription": "matchCharacterDescription",
    "MatchCharacterPersonality": "matchCharacterPersonality",
    "MatchCharacterDepthPrompt": "matchCharacterDepthPrompt",
    "MatchScenario": "matchScenario",
    "MatchCreatorNotes": "matchCreatorNotes",
    "DelayUntilRecursion": "delayUntilRecursion",
    "Probability": "probability",
    "UseProbability": "useProbability",
    "Depth": "depth",
    "OutletName": "outletName",
    "Group": "group",
    "GroupOverride": "groupOverride",
    "GroupWeight": "groupWeight",
    "ScanDepth": "scanDepth",
    "CaseSensitive": "caseSensitive",
    "MatchWholeWords": "matchWholeWords",
    "UseGroupScoring": "useGroupScoring",
    "AutomationId": "automationId",
    "Role": "role",
    "Sticky": "sticky",
    "Cooldown": "cooldown",
    "Delay": "delay",
    "Triggers": "triggers",
    "CharacterFilterIsExclude": ("characterFilter", "isExclude"),
    "CharacterFilterNames": ("characterFilter", "names"),
    "CharacterFilterTags": ("characterFilter", "tags")
}


def parse_entry(text):
    """Parses a single entry .txt file into structured data."""

    data = {}
    lines = text.splitlines()

    name = None
    keys = None
    i = 0
    content_lines = []

    # First pass: gather header sections until Content:
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("Content:"):
            # Start of content block — all remaining lines are content
            content_lines = lines[i + 1 :]
            break

        if line.startswith("Name:"):
            name = line[len("Name:"):].strip()

        elif line.startswith("Keys:"):
            keys = [k.strip() for k in line[len("Keys:"):].split(",") if k.strip()]

        else:
            # Optional fields
            for field in OPTIONAL_FIELDS:
                if line.startswith(field + ":"):
                    value = line.split(":", 1)[1].strip()

                    dest = OPTIONAL_FIELDS[field]

                    # Convert types automatically
                    if isinstance(dest, tuple):
                        # nested field (characterFilter)
                        parent, child = dest
                        if parent not in data:
                            data[parent] = DEFAULT_FIELDS[parent].copy()

                        # list fields
                        if child in ["names", "tags"]:
                            data[parent][child] = [v.strip() for v in value.split(",") if v.strip()]
                        else:
                            data[parent][child] = parse_typed_value(value)

                    else:
                        # normal flat field
                        data[dest] = parse_typed_value(value)

        i += 1

    # Ensure required fields are present
    if not name:
        raise ValueError("Missing required field: Name")
    if not keys:
        raise ValueError("Missing required field: Keys")
    if not content_lines:
        raise ValueError("Missing required field: Content")

    data["name"] = name
    data["key"] = keys
    data["content"] = "\n".join(content_lines).strip()

    return data


def parse_typed_value(value: str):
    """Helper to convert string field values into correct Python types."""
    if value.lower() in ["true", "false"]:
        return value.lower() == "true"
    if value.isdigit():
        return int(value)
    # list-like values must be handled earlier
    return value


def merge_defaults(entry_data: dict, uid: int):
    """Fill missing fields using DEFAULT_FIELDS and add uid/displayIndex."""

    merged = {}

    # Add required fields from parsed entry
    merged["uid"] = uid
    merged["key"] = entry_data["key"]
    merged["content"] = entry_data["content"]
    merged["comment"] = entry_data.get("comment", "")

    # Now apply defaults for all others
    for field, default_value in DEFAULT_FIELDS.items():
        if field not in entry_data:
            merged[field] = default_value
        else:
            merged[field] = entry_data[field]

    # Special case: nested characterFilter defaults
    if "characterFilter" not in entry_data:
        merged["characterFilter"] = DEFAULT_FIELDS["characterFilter"].copy()

    merged["displayIndex"] = uid
    return merged


def main():
    entries = []
    uid = 0

    for filename in sorted(os.listdir(ENTRY_DIR)):
        if not filename.endswith(".txt"):
            continue

        path = os.path.join(ENTRY_DIR, filename)
        with open(path, encoding="utf-8") as f:
            text = f.read()

        parsed = parse_entry(text)
        full_entry = merge_defaults(parsed, uid)
        entries.append(full_entry)
        uid += 1

    final_json = {"entries": entries}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)

    print(f"✓ Lorebook generated: {OUTPUT_FILE}")
    print(f"✓ {len(entries)} entries included")


if __name__ == "__main__":
    main()
