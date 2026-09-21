"""AGENT-01のファイル解析（決定論的処理）。

parse_excel/parse_pdf/parse_eml ツールの中身。openpyxl/pypdf/email標準ライブラリによる
汎用的なテキスト化のみを行い、意味理解（値の候補抽出・出典判断）は行わない
（それはAGENT-01の実行ループ=Claude自身の役割。agent-development.md追加要件）。
固定セル位置・固定文言・ファイル名に依存したsample-data専用ロジックは持たない。
"""

import email
from email import policy
from email.message import Message
from pathlib import Path

import openpyxl
from pypdf import PdfReader


def parse_excel_file(path: str | Path) -> list[dict]:
    """シートごとの非空セルをセル座標付きでテキスト化する（04-db.md parsed_documents.content相当）。"""
    workbook = openpyxl.load_workbook(path, data_only=True)
    rows: list[dict] = []
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                rows.append(
                    {
                        "sheet": sheet.title,
                        "cell": cell.coordinate,
                        "text": str(cell.value),
                    }
                )
    return rows


def parse_pdf_file(path: str | Path) -> list[dict]:
    """ページ単位でテキスト化する。"""
    reader = PdfReader(str(path))
    return [
        {"page": index, "text": page.extract_text() or ""}
        for index, page in enumerate(reader.pages, start=1)
    ]


def _extract_body_text(msg: Message) -> str:
    body = msg.get_body(preferencelist=("plain", "html"))
    if body is None:
        return ""
    return body.get_content()


def parse_eml_file(path: str | Path) -> list[dict]:
    """件名＋本文を段落単位のセクションに分解する（訂正表現等の位置追跡用）。"""
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    sections: list[dict] = [
        {"section": "subject", "text": msg.get("Subject", "") or ""}
    ]
    body_text = _extract_body_text(msg)
    paragraphs = [p.strip() for p in body_text.split("\n\n") if p.strip()]
    sections.extend(
        {"section": f"body-{index}", "text": paragraph}
        for index, paragraph in enumerate(paragraphs, start=1)
    )
    return sections
