import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ card_id: null });
}
