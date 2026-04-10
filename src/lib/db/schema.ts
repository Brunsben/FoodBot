import {
  pgSchema,
  serial,
  text,
  integer,
  boolean,
  date,
  timestamp,
  uniqueIndex,
  index,
} from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";

const food = pgSchema("fw_food");

// ─── Users ────────────────────────────────────────────────────
export const users = food.table(
  "users",
  {
    id: serial("id").primaryKey(),
    name: text("name").notNull(),
    personalNumber: text("personal_number").notNull(),
    cardId: text("card_id"),
    mobileToken: text("mobile_token"),
  },
  (t) => [
    uniqueIndex("users_personal_number_idx").on(t.personalNumber),
    uniqueIndex("users_card_id_idx").on(t.cardId),
    uniqueIndex("users_mobile_token_idx").on(t.mobileToken),
    index("users_name_idx").on(t.name),
  ],
);

export const usersRelations = relations(users, ({ many }) => ({
  registrations: many(registrations),
}));

// ─── Menus ────────────────────────────────────────────────────
export const menus = food.table(
  "menus",
  {
    id: serial("id").primaryKey(),
    date: date("date", { mode: "string" }).notNull().defaultNow(),
    description: text("description").notNull(),
    zweiMenuesAktiv: boolean("zwei_menues_aktiv").notNull().default(false),
    menu1Name: text("menu1_name"),
    menu2Name: text("menu2_name"),
    registrationDeadline: text("registration_deadline").notNull().default("19:45"),
    deadlineEnabled: boolean("deadline_enabled").notNull().default(true),
  },
  (t) => [uniqueIndex("menus_date_idx").on(t.date)],
);

// ─── Registrations ────────────────────────────────────────────
export const registrations = food.table(
  "registrations",
  {
    id: serial("id").primaryKey(),
    userId: integer("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    date: date("date", { mode: "string" }).notNull().defaultNow(),
    menuChoice: integer("menu_choice").notNull().default(1),
  },
  (t) => [
    uniqueIndex("registrations_user_date_idx").on(t.userId, t.date),
    index("registrations_date_user_idx").on(t.date, t.userId),
  ],
);

export const registrationsRelations = relations(registrations, ({ one }) => ({
  user: one(users, { fields: [registrations.userId], references: [users.id] }),
}));

// ─── Guests ───────────────────────────────────────────────────
export const guests = food.table(
  "guests",
  {
    id: serial("id").primaryKey(),
    date: date("date", { mode: "string" }).notNull().defaultNow(),
    menuChoice: integer("menu_choice").notNull().default(1),
    count: integer("count").notNull().default(0),
  },
  (t) => [
    uniqueIndex("guests_date_menu_idx").on(t.date, t.menuChoice),
    index("guests_date_idx").on(t.date),
  ],
);

// ─── Admin Log ────────────────────────────────────────────────
export const adminLog = food.table(
  "admin_log",
  {
    id: serial("id").primaryKey(),
    timestamp: timestamp("timestamp", { mode: "string" }).notNull().defaultNow(),
    adminUser: text("admin_user").notNull(),
    action: text("action").notNull(),
    details: text("details"),
  },
  (t) => [
    index("admin_log_timestamp_idx").on(t.timestamp),
    index("admin_log_admin_user_idx").on(t.adminUser),
  ],
);

// ─── Preset Menus ─────────────────────────────────────────────
export const presetMenus = food.table(
  "preset_menus",
  {
    id: serial("id").primaryKey(),
    name: text("name").notNull().unique(),
    sortOrder: integer("sort_order").notNull().default(0),
  },
);

// ─── Type Exports ─────────────────────────────────────────────
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type Menu = typeof menus.$inferSelect;
export type NewMenu = typeof menus.$inferInsert;
export type Registration = typeof registrations.$inferSelect;
export type Guest = typeof guests.$inferSelect;
export type AdminLogEntry = typeof adminLog.$inferSelect;
export type PresetMenu = typeof presetMenus.$inferSelect;
