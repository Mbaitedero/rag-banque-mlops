import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Assistant documentaire | MBAITEDERO BANK",
  description:
    "Assistant documentaire de démonstration de MBAITEDERO BANK, banque fictive.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
