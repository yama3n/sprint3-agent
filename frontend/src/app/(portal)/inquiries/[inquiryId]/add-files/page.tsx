import { AddFilesPage } from "@/features/inquiries";

export default async function AddFilesRoute({
  params,
}: {
  params: Promise<{ inquiryId: string }>;
}) {
  const { inquiryId } = await params;
  return <AddFilesPage inquiryId={Number(inquiryId)} />;
}
