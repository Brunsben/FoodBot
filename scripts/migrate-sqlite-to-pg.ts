/**
 * Migration: FoodBot SQLite → PostgreSQL
 *
 * Liest die bestehende SQLite-DB und schreibt alle Daten nach PostgreSQL.
 *
 * Voraussetzungen:
 *   1. PostgreSQL-Schema `fw_food` existiert:
 *      CREATE SCHEMA IF NOT EXISTS fw_food;
 *   2. Drizzle-Tabellen sind erstellt:
 *      DATABASE_URL=... npx drizzle-kit push
 *   3. DATABASE_URL und SQLITE_PATH sind gesetzt.
 *
 * Ausführen:
 *   DATABASE_URL=postgresql://... SQLITE_PATH=./foodbot.db npx tsx scripts/migrate-sqlite-to-pg.ts
 */

import Database from "better-sqlite3";
import postgres from "postgres";

const SQLITE_PATH = process.env.SQLITE_PATH || "./foodbot.db";
const PG_URL = process.env.DATABASE_URL;

if (!PG_URL) {
  console.error("❌ DATABASE_URL nicht gesetzt");
  process.exit(1);
}

const sqlite = new Database(SQLITE_PATH, { readonly: true });
const pg = postgres(PG_URL);

const SCHEMA = "fw_food";

async function migrate() {
  console.log(`📀 SQLite: ${SQLITE_PATH}`);
  console.log(`🐘 PostgreSQL: ${PG_URL?.replace(/:[^@]+@/, ":***@")}`);
  console.log();

  // Tables in order (FK dependencies)
  const tables = [
    { name: "user", pgName: "users", boolCols: [] as string[] },
    {
      name: "menu",
      pgName: "menus",
      boolCols: ["zwei_menues_aktiv", "deadline_enabled"],
    },
    { name: "registration", pgName: "registrations", boolCols: [] as string[] },
    { name: "guest", pgName: "guests", boolCols: [] as string[] },
    { name: "admin_log", pgName: "admin_log", boolCols: [] as string[] },
    { name: "preset_menu", pgName: "preset_menus", boolCols: [] as string[] },
  ];

  for (const table of tables) {
    let rows: Record<string, unknown>[];
    try {
      rows = sqlite.prepare(`SELECT * FROM ${table.name}`).all() as Record<
        string,
        unknown
      >[];
    } catch {
      console.log(`  ⏭️  ${table.name}: Tabelle nicht vorhanden`);
      continue;
    }

    if (rows.length === 0) {
      console.log(`  ⏭️  ${table.name}: leer`);
      continue;
    }

    // Convert booleans (SQLite 0/1 → PG true/false)
    for (const row of rows) {
      for (const col of table.boolCols) {
        if (col in row) {
          row[col] = row[col] === 1 || row[col] === true;
        }
      }
    }

    const cols = Object.keys(rows[0]);
    const colList = cols.map((c) => `"${c}"`).join(", ");
    const placeholders = cols.map((_, i) => `$${i + 1}`).join(", ");

    // Reset sequence after insert
    let inserted = 0;
    let maxId = 0;
    for (const row of rows) {
      const values = cols.map((c) => row[c] ?? null);
      try {
        await pg.unsafe(
          `INSERT INTO "${SCHEMA}"."${table.pgName}" (${colList}) VALUES (${placeholders}) ON CONFLICT DO NOTHING`,
          values as any[],
        );
        inserted++;
        if (typeof row.id === "number" && row.id > maxId) maxId = row.id;
      } catch (err: unknown) {
        console.error(`  ❌ ${table.name}: Fehler bei Zeile`, row, err);
      }
    }

    // Reset serial sequence if table has integer id
    if (maxId > 0) {
      await pg.unsafe(
        `SELECT setval(pg_get_serial_sequence('"${SCHEMA}"."${table.pgName}"', 'id'), $1)`,
        [maxId],
      );
    }

    console.log(
      `  ✅ ${table.name} → ${table.pgName}: ${inserted}/${rows.length} Zeilen migriert`,
    );
  }

  console.log("\n🎉 Migration abgeschlossen!");
  await pg.end();
  sqlite.close();
}

migrate().catch((err) => {
  console.error("❌ Migration fehlgeschlagen:", err);
  process.exit(1);
});
