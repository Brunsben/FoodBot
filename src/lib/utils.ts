import { randomBytes } from "crypto";
import { db } from "./db";
import { menus, registrations, guests, users } from "./db/schema";
import { eq, and, sql } from "drizzle-orm";

/**
 * Generate a random token for mobile links.
 */
export function generateToken(): string {
  return randomBytes(24).toString("hex");
}

/**
 * Get today's date as YYYY-MM-DD string.
 */
export function today(): string {
  return new Date().toISOString().split("T")[0];
}

/**
 * Get the menu for a specific date.
 */
export async function getMenuForDate(date: string) {
  const [menu] = await db.select().from(menus).where(eq(menus.date, date)).limit(1);
  return menu || null;
}

/**
 * Get guests for a specific date, structured by menu choice.
 */
export async function getGuestsForDate(date: string) {
  const rows = await db.select().from(guests).where(eq(guests.date, date));
  return {
    menu1: rows.find((g) => g.menuChoice === 1)?.count || 0,
    menu2: rows.find((g) => g.menuChoice === 2)?.count || 0,
  };
}

/**
 * Get registrations for a date with user info.
 */
export async function getRegistrationsForDate(date: string) {
  return db
    .select({
      id: registrations.id,
      userId: registrations.userId,
      menuChoice: registrations.menuChoice,
      userName: users.name,
      personalNumber: users.personalNumber,
    })
    .from(registrations)
    .innerJoin(users, eq(registrations.userId, users.id))
    .where(eq(registrations.date, date))
    .orderBy(users.name);
}

/**
 * Check if registration is still open for a menu.
 */
export function isRegistrationOpen(menu: { registrationDeadline: string; deadlineEnabled: boolean }) {
  if (!menu.deadlineEnabled) return true;
  const now = new Date();
  const [hours, minutes] = menu.registrationDeadline.split(":").map(Number);
  const deadline = new Date();
  deadline.setHours(hours, minutes, 0, 0);
  return now < deadline;
}

/**
 * Toggle registration for a user on today.
 * Returns { registered: boolean, menuChoice: number }.
 */
export async function toggleRegistration(userId: number, menuChoice: number = 1) {
  const dateStr = today();

  // Check if already registered
  const [existing] = await db
    .select()
    .from(registrations)
    .where(and(eq(registrations.userId, userId), eq(registrations.date, dateStr)))
    .limit(1);

  if (existing) {
    // Unregister
    await db.delete(registrations).where(eq(registrations.id, existing.id));
    return { registered: false, menuChoice: existing.menuChoice };
  } else {
    // Register
    await db.insert(registrations).values({ userId, date: dateStr, menuChoice });
    return { registered: true, menuChoice };
  }
}

/**
 * Save menu for a date.
 */
export async function saveMenu(
  date: string,
  data: {
    description: string;
    zweiMenuesAktiv?: boolean;
    menu1Name?: string;
    menu2Name?: string;
    registrationDeadline?: string;
    deadlineEnabled?: boolean;
  },
) {
  const existing = await getMenuForDate(date);

  const values = {
    date,
    description: data.description,
    zweiMenuesAktiv: data.zweiMenuesAktiv || false,
    menu1Name: data.menu1Name || null,
    menu2Name: data.menu2Name || null,
    registrationDeadline: data.registrationDeadline || "19:45",
    deadlineEnabled: data.deadlineEnabled !== false,
  };

  if (existing) {
    await db.update(menus).set(values).where(eq(menus.id, existing.id));
  } else {
    await db.insert(menus).values(values);
  }
}

/**
 * Set guest count for a date and menu choice.
 */
export async function setGuestCount(date: string, menuChoice: number, count: number) {
  const [existing] = await db
    .select()
    .from(guests)
    .where(and(eq(guests.date, date), eq(guests.menuChoice, menuChoice)))
    .limit(1);

  if (existing) {
    await db
      .update(guests)
      .set({ count: Math.max(0, count) })
      .where(eq(guests.id, existing.id));
  } else if (count > 0) {
    await db.insert(guests).values({ date, menuChoice, count: Math.max(0, count) });
  }
}

/**
 * Get registration count for a date.
 */
export async function getRegistrationCount(date: string) {
  const [result] = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(registrations)
    .where(eq(registrations.date, date));
  return result?.count || 0;
}

/**
 * Get total count (registrations + guests) for a date.
 */
export async function getTotalCount(date: string) {
  const regCount = await getRegistrationCount(date);
  const guestData = await getGuestsForDate(date);
  return regCount + guestData.menu1 + guestData.menu2;
}
