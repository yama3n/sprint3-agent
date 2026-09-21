export {
  useGetInquiryDetailApiV1InquiriesInquiryIdGet as useInquiryDetail,
  getGetInquiryDetailApiV1InquiriesInquiryIdGetQueryKey as getInquiryDetailQueryKey,
  useUpdateCaseFieldApiV1InquiriesInquiryIdFieldsFieldIdPatch as useUpdateCaseField,
  useUpdateItemFieldApiV1InquiriesInquiryIdItemsItemIdFieldsFieldIdPatch as useUpdateItemField,
} from "@/shared/api/generated/inquiries";
export type {
  InquiryDetailResponse,
  FieldRead,
  CandidateRead,
  ItemRead,
  NoteRead,
} from "@/shared/api/generated/model";
