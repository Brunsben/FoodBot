import { db } from "./db";
import { adminLog } from "./db/schema";

/**
 * Log an admin action.
 */
export async function logAdmin(adminUser: string, action: string, details?: string) {
  await db.insert(adminLog).values({ adminUser, action, details });
}
