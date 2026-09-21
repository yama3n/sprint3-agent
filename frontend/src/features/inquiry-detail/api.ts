export {
  useGetInquiryDetailApiV1InquiriesInquiryIdGet as useInquiryDetail,
  getGetInquiryDetailApiV1InquiriesInquiryIdGetQueryKey as getInquiryDetailQueryKey,
  useUpdateCaseFieldApiV1InquiriesInquiryIdFieldsFieldIdPatch as useUpdateCaseField,
  useUpdateItemFieldApiV1InquiriesInquiryIdItemsItemIdFieldsFieldIdPatch as useUpdateItemField,
  useConfirmApiV1InquiriesInquiryIdConfirmPost as useConfirmInquiry,
  useCreateInquiryExportApiV1InquiriesInquiryIdExportsPost as useCreateExport,
  getDownloadInquiryExportApiV1InquiriesInquiryIdExportsExportIdDownloadGetUrl as getExportDownloadUrl,
} from "@/shared/api/generated/inquiries";
export type {
  InquiryDetailResponse,
  FieldRead,
  CandidateRead,
  ItemRead,
  NoteRead,
} from "@/shared/api/generated/model";
