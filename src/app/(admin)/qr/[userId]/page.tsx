import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import { notFound } from "next/navigation";
import { generateToken } from "@/lib/utils";
import { generateQRCode } from "@/lib/qr";
import QRPrintButton from "./qr-print-button";

export default async function QRCodePage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId: userIdStr } = await params;
  const userId = parseInt(userIdStr, 10);
  if (isNaN(userId)) notFound();

  let user = await db.query.users.findFirst({ where: eq(users.id, userId) });
  if (!user) notFound();

  // Generate token if user doesn't have one
  if (!user.mobileToken) {
    const token = generateToken();
    await db
      .update(users)
      .set({ mobileToken: token })
      .where(eq(users.id, userId));
    user = { ...user, mobileToken: token };
  }

  const baseUrl = process.env.BASE_URL || "https://fw.example.com";
  const mobileUrl = `${baseUrl}/food/m/${user.mobileToken}`;
  const qrDataUrl = await generateQRCode(mobileUrl);

  return (
    <div className="max-w-md mx-auto py-8">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-8 text-center">
        <h1 className="text-xl font-bold mb-1 dark:text-white">{user.name}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Personal-Nr: {user.personalNumber}
        </p>

        {/* QR Code */}
        <div className="bg-white p-4 rounded-xl inline-block mb-6">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={qrDataUrl} alt="QR Code" className="w-64 h-64" />
        </div>

        <p className="text-xs text-gray-500 dark:text-gray-400 break-all mb-6">
          {mobileUrl}
        </p>

        <QRPrintButton />
      </div>
    </div>
  );
}
