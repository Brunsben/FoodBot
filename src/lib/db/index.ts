import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

const client = postgres(
  process.env.DATABASE_URL || "postgresql://localhost:5432/feuerwehr",
  {
    max: 10,
  },
);

export const db = drizzle(client, { schema });

let schemaInitPromise: Promise<void> | null = null;

function ensureFoodSchema() {
  if (schemaInitPromise) return schemaInitPromise;

  schemaInitPromise = (async () => {
    await client.unsafe(`
      ALTER TABLE IF EXISTS "fw_food"."users"
      ADD COLUMN IF NOT EXISTS "portal_member_id" text;
    `);

    await client.unsafe(`
      CREATE UNIQUE INDEX IF NOT EXISTS "users_portal_member_id_idx"
      ON "fw_food"."users" ("portal_member_id");
    `);
  })().catch((err) => {
    console.error("FoodBot schema bootstrap failed:", err);
  });

  return schemaInitPromise;
}

void ensureFoodSchema();
