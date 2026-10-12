import type { Metadata } from "next";
import { IBM_Plex_Mono, Lexend, Source_Sans_3 } from "next/font/google";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

const lexend = Lexend({ variable: "--font-lexend", subsets: ["latin"], weight: ["500", "600"] });
const sourceSans = Source_Sans_3({ variable: "--font-source-sans", subsets: ["latin"], weight: ["400", "500", "600"] });
const plexMono = IBM_Plex_Mono({ variable: "--font-plex-mono", subsets: ["latin"], weight: ["500"] });

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://suppliertrail.com"),
  title: "SupplierTrail — FDA records for food and supplement suppliers",
  description:
    "Look up FDA import alerts, import refusals, inspections, recalls and warning letters for food and dietary-supplement suppliers.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${lexend.variable} ${sourceSans.variable} ${plexMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:rounded-md focus:bg-surface focus:px-4 focus:py-2"
        >
          Skip to main content
        </a>
        <SiteHeader />
        <main id="main" className="mx-auto flex w-full max-w-[1200px] flex-1 flex-col gap-6 px-4 pb-16 pt-6 sm:px-6">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}
