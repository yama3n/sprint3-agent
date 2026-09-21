import pytest

from app.services.inquiry_upload_service import (
    UnsupportedFileTypeError,
    validate_file_names,
)

SUPPORTED = ("order.xlsx", "quote.pdf", "inquiry.eml")


def test_validate_file_names_accepts_supported_extensions() -> None:
    validate_file_names(list(SUPPORTED))  # no exception


def test_validate_file_names_rejects_unsupported_extension() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_file_names(["contract.docx"])


def test_validate_file_names_rejects_empty_list() -> None:
    from app.services.inquiry_upload_service import NoFilesError

    with pytest.raises(NoFilesError):
        validate_file_names([])


def test_validate_file_names_is_case_insensitive() -> None:
    validate_file_names(["ORDER.XLSX"])
