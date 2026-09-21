"""AGENT-01ツールのJSON Schema（tools.py の @tool input_schema 用）。

agent-plan.md「2. エージェント間データフロー」の ExtractionCandidate 形状に対応する。
"""

CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "field_id": {"type": "string"},
        "value": {"type": ["string", "null"]},
        "source_type": {"type": "string", "enum": ["pdf", "excel", "eml"]},
        "source_file": {"type": "string"},
        "source_location": {"type": "string"},
        "quoted_text": {"type": "string"},
        "correction_hint": {
            "type": "object",
            "properties": {
                "is_explicit_correction": {"type": "boolean"},
                "superseded_value": {"type": "string"},
            },
            "required": ["is_explicit_correction"],
        },
    },
    "required": [
        "field_id",
        "value",
        "source_type",
        "source_file",
        "source_location",
        "quoted_text",
    ],
}

NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string"},
        "source_type": {"type": "string", "enum": ["pdf", "excel", "eml"]},
        "source_file": {"type": "string"},
        "source_location": {"type": "string"},
    },
    "required": ["content"],
}

PARSE_FILE_SCHEMA = {
    "type": "object",
    "properties": {"file_id": {"type": "integer"}},
    "required": ["file_id"],
}

EXTRACT_CASE_FIELDS_SCHEMA = {
    "type": "object",
    "properties": {
        "inquiry_id": {"type": "integer"},
        "candidates": {"type": "array", "items": CANDIDATE_SCHEMA},
    },
    "required": ["inquiry_id", "candidates"],
}

EXTRACT_ITEM_FIELDS_SCHEMA = {
    "type": "object",
    "properties": {
        "inquiry_id": {"type": "integer"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_no": {"type": "integer"},
                    "candidates": {"type": "array", "items": CANDIDATE_SCHEMA},
                },
                "required": ["item_no", "candidates"],
            },
        },
    },
    "required": ["inquiry_id", "items"],
}

EXTRACT_SUPPLEMENTARY_NOTES_SCHEMA = {
    "type": "object",
    "properties": {
        "inquiry_id": {"type": "integer"},
        "case_notes": {"type": "array", "items": NOTE_SCHEMA},
        "item_notes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_no": {"type": "integer"},
                    "notes": {"type": "array", "items": NOTE_SCHEMA},
                },
                "required": ["item_no", "notes"],
            },
        },
    },
    "required": ["inquiry_id", "case_notes", "item_notes"],
}

EMIT_EXTRACTION_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "inquiry_id": {"type": "integer"},
        "agent_run_id": {"type": "integer"},
        "source_files": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["inquiry_id", "agent_run_id", "source_files"],
}
