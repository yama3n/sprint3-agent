"""FastAPI OpenAPI スキーマをエクスポート"""

import argparse
import json
import sys
from pathlib import Path

# backend/ をルートとして扱う（`python scripts/export_openapi.py` 実行時、既定では
# scripts/ しか sys.path に乗らないため、親ディレクトリを明示的に追加する）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Export OpenAPI schema")
    parser.add_argument("-o", "--output", default="openapi.json", help="Output file path")
    args = parser.parse_args()

    openapi_schema = app.openapi()

    with open(args.output, "w") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI schema exported to: {args.output}")


if __name__ == "__main__":
    main()
