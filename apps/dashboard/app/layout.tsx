import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Public Opinin Analytics",
  description: "Public opinion analytics dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
