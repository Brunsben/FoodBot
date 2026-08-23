import { z } from "zod";

export const personalNumberSchema = z
  .string()
  .min(1)
  .max(20)
  .regex(/^[a-zA-Z0-9\-]+$/, "Nur alphanumerische Zeichen und Bindestriche");

export const cardIdSchema = z
  .string()
  .max(50)
  .regex(/^[0-9a-fA-F]+$/, "Nur Hexadezimalzeichen")
  .transform((v) => v.toUpperCase());

export const nameSchema = z
  .string()
  .min(2, "Mindestens 2 Zeichen")
  .max(100, "Maximal 100 Zeichen");

export const menuChoiceSchema = z.coerce
  .number()
  .int()
  .min(1)
  .max(2)
  .default(1);

export const dateSchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Format: YYYY-MM-DD");

export const timeSchema = z.string().regex(/^\d{2}:\d{2}$/, "Format: HH:MM");

export const tokenSchema = z
  .string()
  .min(32)
  .max(64)
  .regex(/^[A-Za-z0-9_\-]+$/);

export function sanitizeString(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;")
    .trim();
}
