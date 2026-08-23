import QRCode from "qrcode";

/**
 * Generate a QR code as a base64-encoded data URL.
 */
export async function generateQRCode(data: string): Promise<string> {
  return QRCode.toDataURL(data, {
    type: "image/png",
    width: 300,
    margin: 2,
    color: { dark: "#000000", light: "#ffffff" },
  });
}
