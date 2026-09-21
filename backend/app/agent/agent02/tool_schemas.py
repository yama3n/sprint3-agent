"""AGENT-02ツールのJSON Schema（tools.py の @tool input_schema 用）。"""

CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "value": {"type": "string"},
        "source_type": {"type": "string", "enum": ["pdf", "excel", "eml", "web"]},
        "source_file": {"type": "string"},
        "source_location": {"type": "string"},
        "quoted_text": {"type": "string"},
        "web_url": {"type": "string"},
        "web_source_name": {"type": "string"},
        "web_referenced_at": {"type": "string"},
        "is_explicit_correction": {"type": "boolean"},
        "superseded_value": {"type": "string"},
        "is_selected": {"type": "boolean"},
    },
    "required": ["value", "source_type"],
}

LOAD_EXISTING_INQUIRY_SCHEMA = {
    "type": "object",
    "properties": {"inquiry_id": {"type": "integer"}},
    "required": ["inquiry_id"],
}

_FIELD_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "field_id": {"type": "string"},
        "item_no": {"type": ["integer", "null"]},
        "value": {"type": ["string", "null"]},
        "candidates": {"type": "array", "items": CANDIDATE_SCHEMA},
    },
    "required": ["field_id", "candidates"],
}

COMPARE_AND_MERGE_CANDIDATES_SCHEMA = {
    "type": "object",
    "properties": {
        "inquiry_id": {"type": "integer"},
        "fields": {"type": "array", "items": _FIELD_RESULT_SCHEMA},
    },
    "required": ["inquiry_id", "fields"],
}

EVALUATE_EXPLICIT_CORRECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "inquiry_id": {"type": "integer"},
        "corrections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field_id": {"type": "string"},
                    "item_no": {"type": ["integer", "null"]},
                    "adopted_value": {"type": "string"},
                    "superseded_value": {"type": "string"},
                },
                "required": ["field_id", "adopted_value"],
            },
        },
    },
    "required": ["inquiry_id", "corrections"],
}

CLASSIFY_STATUS_SCHEMA = {
    "type": "object",
    "properties": {
        "inquiry_id": {"type": "integer"},
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field_id": {"type": "string"},
                    "item_no": {"type": ["integer", "null"]},
                    "status": {"type": "string", "enum": ["ok", "review"]},
                    "reason_type": {
                        "type": ["string", "null"],
                        "enum": [
                            "missing",
                            "conflict",
                            "ambiguous",
                            "multiple_candidates",
                            "parse_error",
                            None,
                        ],
                    },
                },
                "required": ["field_id", "status"],
            },
        },
    },
    "required": ["inquiry_id", "decisions"],
}

WEB_SEARCH_COMPANY_INFO_SCHEMA = {
    "type": "object",
    "properties": {
        "inquiry_id": {"type": "integer"},
        "field_id": {"type": "string"},
        "item_no": {"type": ["integer", "null"]},
        "value": {"type": "string"},
        "url": {"type": "string"},
        "source_name": {"type": "string"},
        "referenced_at": {"type": "string"},
    },
    "required": ["inquiry_id", "field_id", "value", "url", "source_name"],
}

SAVE_STRUCTURED_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "inquiry_id": {"type": "integer"},
        "agent_run_id": {"type": "integer"},
    },
    "required": ["inquiry_id", "agent_run_id"],
}
