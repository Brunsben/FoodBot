import { db } from "./db";
import { users } from "./db/schema";
import { eq } from "drizzle-orm";
import { SignJWT } from "jose";

const POSTGREST_URL = process.env.POSTGREST_URL || "http://postgrest:3000";
const JWT_SECRET = process.env.JWT_SECRET || "";

/**
 * Sync users from Portal (PostgREST) → fw_food.users.
 * Creates new users and updates existing ones. Does not delete.
 */
export async function syncFromPortal(): Promise<{
  created: number;
  updated: number;
  errors: string[];
}> {
  const errors: string[] = [];
  let created = 0;
  let updated = 0;

  // Generate short-lived service JWT
  const secret = new TextEncoder().encode(JWT_SECRET);
  const serviceToken = await new SignJWT({
    role: "psa_user",
    app_role: "Admin",
  })
    .setProtectedHeader({ alg: "HS256" })
    .setExpirationTime("5m")
    .sign(secret);

  // Fetch active members from Portal
  const response = await fetch(
    `${POSTGREST_URL}/Kameraden?Aktiv=eq.true&Personalnummer=not.is.null`,
    {
      headers: {
        Authorization: `Bearer ${serviceToken}`,
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Portal-Sync fehlgeschlagen: ${response.status} ${response.statusText}`,
    );
  }

  const kameraden = (await response.json()) as Array<{
    Id?: number;
    id?: number;
    Vorname: string;
    Name: string;
    Personalnummer: string;
    KartenID?: string;
  }>;

  for (const k of kameraden) {
    const rawMemberId = k.Id ?? k.id;
    if (rawMemberId === null || rawMemberId === undefined) {
      errors.push(
        `${k.Personalnummer}: Portal-Mitglied ohne ID wurde übersprungen`,
      );
      continue;
    }

    const portalMemberId = String(rawMemberId);
    const name = `${k.Vorname} ${k.Name}`.trim();
    const personalNumber = k.Personalnummer;
    const cardId = k.KartenID || null;

    try {
      const [existingByPortalId] = await db
        .select()
        .from(users)
        .where(eq(users.portalMemberId, portalMemberId))
        .limit(1);

      const [existingByPersonalNumber] = await db
        .select()
        .from(users)
        .where(eq(users.personalNumber, personalNumber))
        .limit(1);

      const existing = existingByPortalId || existingByPersonalNumber;

      if (existing) {
        await db
          .update(users)
          .set({
            name,
            personalNumber,
            cardId,
            portalMemberId,
          })
          .where(eq(users.id, existing.id));
        updated++;
      } else {
        await db.insert(users).values({
          name,
          personalNumber,
          cardId,
          portalMemberId,
        });
        created++;
      }
    } catch (err) {
      errors.push(
        `${portalMemberId}/${personalNumber}: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  }

  return { created, updated, errors };
}
