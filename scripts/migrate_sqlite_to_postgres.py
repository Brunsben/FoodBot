#!/usr/bin/env python3
"""
SQLite → PostgreSQL Migrationsskript für FoodBot
=================================================

Überträgt alle Daten aus der alten SQLite-Datenbank (foodbot.db) in das
neue fw_food Schema in PostgreSQL.

Transformationen:
  - Integer-IDs → UUIDs
  - User.personal_number → fw_common.members.id Mapping
  - User.card_id → fw_food.rfid_cards (eigene Tabelle)
  - User.mobile_token → fw_food.mobile_tokens (eigene Tabelle)
  - Spalten-Umbenennung: date→datum, description→beschreibung, count→anzahl,
    menu_choice→menu_wahl, registration_deadline→anmeldefrist,
    deadline_enabled→frist_aktiv, timestamp→zeitpunkt, action→aktion

Voraussetzungen:
  - PostgreSQL mit fw_common und fw_food Schemas (postgres-init.sql + postgres-food.sql)
  - fw_common.members bereits befüllt (aus NocoDB / PSA-Verwaltung)
  - SQLite-Datei foodbot.db im FoodBot-Root oder als Argument

Verwendung:
  python scripts/migrate_sqlite_to_postgres.py [pfad/zu/foodbot.db]

Umgebungsvariablen:
  DATABASE_URL  - PostgreSQL Connection-String (default: postgresql://nocodb:nocodb@localhost:5432/nocodb)
"""

import sqlite3
import os
import sys
import uuid
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("❌ psycopg2 nicht installiert. Bitte: pip install psycopg2-binary")
    sys.exit(1)


# ─── Konfiguration ──────────────────────────────────────────────────────────

SQLITE_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "foodbot.db"
)

POSTGRES_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://nocodb:nocodb@localhost:5432/nocodb"
)

# Trockenlauf: nur anzeigen, nichts schreiben
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")


# ─── Hilfsfunktionen ────────────────────────────────────────────────────────

def connect_sqlite(path: str) -> sqlite3.Connection:
    """SQLite-DB öffnen (read-only)."""
    if not os.path.exists(path):
        print(f"❌ SQLite-Datei nicht gefunden: {path}")
        sys.exit(1)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def connect_postgres(url: str):
    """PostgreSQL-Verbindung herstellen."""
    conn = psycopg2.connect(url)
    conn.autocommit = False
    return conn


def new_uuid() -> str:
    return str(uuid.uuid4())


def load_member_map(pg_cur) -> dict:
    """
    Lädt alle Mitglieder aus fw_common.members und erstellt ein Mapping
    Personalnummer → UUID.
    """
    pg_cur.execute("""
        SELECT id, "Personalnummer", "Vorname", "Name"
        FROM fw_common.members
        WHERE "Aktiv" = true OR "Aktiv" IS NULL
    """)
    member_map = {}
    for row in pg_cur.fetchall():
        if row[1]:  # Personalnummer vorhanden
            member_map[str(row[1])] = str(row[0])
    return member_map


def load_user_map(sqlite_cur) -> dict:
    """Lädt alle User aus SQLite: id → {name, personal_number, card_id, mobile_token}."""
    sqlite_cur.execute("SELECT id, name, personal_number, card_id, mobile_token FROM user")
    users = {}
    for row in sqlite_cur.fetchall():
        users[row["id"]] = {
            "name": row["name"],
            "personal_number": row["personal_number"],
            "card_id": row["card_id"],
            "mobile_token": row["mobile_token"],
        }
    return users


# ─── Migrations-Funktionen ──────────────────────────────────────────────────

def migrate_menus(sqlite_cur, pg_cur) -> dict:
    """Migriert Menu-Tabelle. Gibt Mapping alte_id → neue_uuid zurück."""
    sqlite_cur.execute("""
        SELECT id, date, description, zwei_menues_aktiv, menu1_name, menu2_name,
               registration_deadline, deadline_enabled
        FROM menu
    """)
    menu_map = {}
    rows = sqlite_cur.fetchall()
    
    for row in rows:
        new_id = new_uuid()
        menu_map[row["id"]] = new_id
        
        pg_cur.execute("""
            INSERT INTO fw_food.menus (id, datum, beschreibung, zwei_menues_aktiv,
                                       menu1_name, menu2_name, anmeldefrist, frist_aktiv)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (datum) DO NOTHING
        """, (
            new_id,
            row["date"],
            row["description"],
            bool(row["zwei_menues_aktiv"]) if row["zwei_menues_aktiv"] is not None else False,
            row["menu1_name"] or "Menü 1",
            row["menu2_name"] or "Menü 2",
            row["registration_deadline"],
            bool(row["deadline_enabled"]) if row["deadline_enabled"] is not None else False,
        ))
    
    print(f"  ✅ {len(rows)} Menüs migriert")
    return menu_map


def migrate_registrations(sqlite_cur, pg_cur, user_to_member: dict) -> int:
    """Migriert Registration-Tabelle. Gibt Anzahl migrierten Zeilen zurück."""
    sqlite_cur.execute("SELECT id, user_id, date, menu_choice FROM registration")
    rows = sqlite_cur.fetchall()
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        member_id = user_to_member.get(row["user_id"])
        if not member_id:
            skipped += 1
            continue
        
        pg_cur.execute("""
            INSERT INTO fw_food.registrations (id, member_id, datum, menu_wahl)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (member_id, datum) DO NOTHING
        """, (
            new_uuid(),
            member_id,
            row["date"],
            row["menu_choice"] or 1,
        ))
        migrated += 1
    
    print(f"  ✅ {migrated} Anmeldungen migriert ({skipped} übersprungen — User nicht gefunden)")
    return migrated


def migrate_guests(sqlite_cur, pg_cur) -> int:
    """Migriert Guest-Tabelle."""
    sqlite_cur.execute("SELECT id, date, menu_choice, count FROM guest")
    rows = sqlite_cur.fetchall()
    
    for row in rows:
        pg_cur.execute("""
            INSERT INTO fw_food.guests (id, datum, menu_wahl, anzahl)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (datum, menu_wahl) DO NOTHING
        """, (
            new_uuid(),
            row["date"],
            row["menu_choice"] or 1,
            row["count"] or 0,
        ))
    
    print(f"  ✅ {len(rows)} Gäste-Einträge migriert")
    return len(rows)


def migrate_rfid_cards(pg_cur, users: dict, user_to_member: dict) -> int:
    """Extrahiert card_id aus alten Users in rfid_cards-Tabelle."""
    migrated = 0
    
    for old_id, user in users.items():
        if user["card_id"] and old_id in user_to_member:
            member_id = user_to_member[old_id]
            pg_cur.execute("""
                INSERT INTO fw_food.rfid_cards (id, card_id, member_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (card_id) DO NOTHING
            """, (
                new_uuid(),
                user["card_id"],
                member_id,
            ))
            migrated += 1
    
    print(f"  ✅ {migrated} RFID-Karten migriert")
    return migrated


def migrate_mobile_tokens(pg_cur, users: dict, user_to_member: dict) -> int:
    """Extrahiert mobile_token aus alten Users in mobile_tokens-Tabelle."""
    migrated = 0
    
    for old_id, user in users.items():
        if user["mobile_token"] and old_id in user_to_member:
            member_id = user_to_member[old_id]
            pg_cur.execute("""
                INSERT INTO fw_food.mobile_tokens (id, member_id, token)
                VALUES (%s, %s, %s)
                ON CONFLICT (member_id) DO NOTHING
            """, (
                new_uuid(),
                member_id,
                user["mobile_token"],
            ))
            migrated += 1
    
    print(f"  ✅ {migrated} Mobile-Tokens migriert")
    return migrated


def migrate_preset_menus(sqlite_cur, pg_cur) -> int:
    """Migriert PresetMenu-Tabelle."""
    sqlite_cur.execute("SELECT id, name, sort_order FROM preset_menu")
    rows = sqlite_cur.fetchall()
    
    for row in rows:
        pg_cur.execute("""
            INSERT INTO fw_food.preset_menus (id, name, sort_order)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (
            new_uuid(),
            row["name"],
            row["sort_order"] or 0,
        ))
    
    print(f"  ✅ {len(rows)} Vorlagen-Menüs migriert")
    return len(rows)


def migrate_admin_log(sqlite_cur, pg_cur) -> int:
    """Migriert AdminLog-Tabelle."""
    sqlite_cur.execute("SELECT id, timestamp, admin_user, action, details FROM admin_log")
    rows = sqlite_cur.fetchall()
    
    for row in rows:
        pg_cur.execute("""
            INSERT INTO fw_food.admin_log (id, zeitpunkt, admin_user, aktion, details)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            new_uuid(),
            row["timestamp"] or datetime.now().isoformat(),
            row["admin_user"],
            row["action"],
            row["details"],
        ))
    
    print(f"  ✅ {len(rows)} Admin-Log-Einträge migriert")
    return len(rows)


# ─── Hauptprogramm ──────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("FoodBot Migration: SQLite → PostgreSQL (fw_food)")
    print("=" * 60)
    print()
    
    if DRY_RUN:
        print("⚠️  TROCKENLAUF — keine Daten werden geschrieben")
        print()
    
    # Verbindungen herstellen
    print(f"📂 SQLite: {SQLITE_PATH}")
    print(f"🐘 PostgreSQL: {POSTGRES_URL.split('@')[1] if '@' in POSTGRES_URL else POSTGRES_URL}")
    print()
    
    sqlite_conn = connect_sqlite(SQLITE_PATH)
    sqlite_cur = sqlite_conn.cursor()
    
    pg_conn = connect_postgres(POSTGRES_URL)
    pg_cur = pg_conn.cursor()
    
    try:
        # 1. Mappings laden
        print("🔗 Lade Mitglieder-Mapping...")
        member_map = load_member_map(pg_cur)  # Personalnummer → UUID
        print(f"   {len(member_map)} Mitglieder in fw_common.members gefunden")
        
        users = load_user_map(sqlite_cur)  # old_id → {name, personal_number, ...}
        print(f"   {len(users)} User in SQLite gefunden")
        
        # User → Member Mapping erstellen (old_int_id → UUID)
        user_to_member = {}
        unmatched = []
        
        for old_id, user in users.items():
            pn = str(user["personal_number"]) if user["personal_number"] else None
            if pn and pn in member_map:
                user_to_member[old_id] = member_map[pn]
            else:
                unmatched.append(f"  ⚠️  User #{old_id} '{user['name']}' (PN: {pn}) — kein Mitglied gefunden")
        
        print(f"   {len(user_to_member)} User ↔ Mitglieder gemappt")
        
        if unmatched:
            print(f"\n⚠️  {len(unmatched)} User konnten nicht zugeordnet werden:")
            for msg in unmatched[:20]:
                print(msg)
            if len(unmatched) > 20:
                print(f"   ... und {len(unmatched) - 20} weitere")
        print()
        
        # 2. Daten migrieren
        print("📦 Starte Migration...")
        
        migrate_menus(sqlite_cur, pg_cur)
        migrate_registrations(sqlite_cur, pg_cur, user_to_member)
        migrate_guests(sqlite_cur, pg_cur)
        migrate_rfid_cards(pg_cur, users, user_to_member)
        migrate_mobile_tokens(pg_cur, users, user_to_member)
        migrate_preset_menus(sqlite_cur, pg_cur)
        migrate_admin_log(sqlite_cur, pg_cur)
        
        # 3. Commit oder Rollback
        if DRY_RUN:
            print("\n🔄 Trockenlauf — Rollback")
            pg_conn.rollback()
        else:
            print("\n💾 Commit...")
            pg_conn.commit()
            print("✅ Migration erfolgreich abgeschlossen!")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"\n❌ Fehler bei der Migration: {e}")
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()
    
    print()
    print("=" * 60)
    print("Nächste Schritte:")
    print("  1. FoodBot mit PostgreSQL starten und testen")
    print("  2. SQLite-Datei archivieren (nicht löschen!)")
    print("  3. RFID-Reader / Touch-Interface testen")
    print("=" * 60)


if __name__ == "__main__":
    main()
