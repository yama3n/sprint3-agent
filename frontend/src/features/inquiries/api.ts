export {
  useListInquiriesApiV1InquiriesGet as useListInquiries,
  useCreateInquiryApiV1InquiriesPost as useCreateInquiry,
  useAddFilesApiV1InquiriesInquiryIdFilesPost as useAddFiles,
  useGetAgentStatusApiV1InquiriesInquiryIdAgentStatusGet as useAgentStatusQuery,
} from "@/shared/api/generated/inquiries";
export type {
  InquiryListItem,
  AgentStatusResponse,
  UploadResponse,
} from "@/shared/api/generated/model";
