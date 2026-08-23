import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FoodBot — Essensanmeldung",
  description: "Feuerwehr Essensanmeldung",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de" suppressHydrationWarning>
      <head>
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"
        />
        <link rel="manifest" href="/food/manifest.json" />
        <meta name="theme-color" content="#1e293b" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                var theme = document.cookie.match(/fw_theme=([^;]+)/)?.[1] || 'dark';
                document.documentElement.classList.toggle('dark', theme === 'dark');
              })();
            `,
          }}
        />
      </head>
      <body className="bg-gray-50 text-gray-900 dark:bg-slate-900 dark:text-gray-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
