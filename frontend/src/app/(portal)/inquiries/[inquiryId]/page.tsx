import { InquiryDetailScreen } from "@/features/inquiry-detail";

export default async function InquiryDetailRoute({
  params,
}: {
  params: Promise<{ inquiryId: string }>;
}) {
  const { inquiryId } = await params;
  return <InquiryDetailScreen inquiryId={Number(inquiryId)} />;
}
