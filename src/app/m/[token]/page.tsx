import { db } from "@/lib/db";
import { users, menus, registrations } from "@/lib/db/schema";
import { eq, and } from "drizzle-orm";
import MobileRegistration from "./mobile-registration";

function todayString() {
  return new Date().toISOString().slice(0, 10);
}

export default async function MobilePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;

  const user = await db.query.users.findFirst({
    where: eq(users.mobileToken, token),
  });

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-8 text-center max-w-sm">
          <p className="text-4xl mb-4">❌</p>
          <h1 className="text-xl font-bold dark:text-white">Ungültiger Link</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            Dieser Link ist nicht gültig oder abgelaufen.
          </p>
        </div>
      </div>
    );
  }

  const today = todayString();

  const [menu, registration] = await Promise.all([
    db.query.menus.findFirst({ where: eq(menus.date, today) }),
    db.query.registrations.findFirst({
      where: and(eq(registrations.userId, user.id), eq(registrations.date, today)),
    }),
  ]);

  return (
    <MobileRegistration
      user={{ id: user.id, name: user.name, personalNumber: user.personalNumber }}
      menu={menu || null}
      initialRegistration={registration ? { menuChoice: registration.menuChoice } : null}
    />
  );
}
