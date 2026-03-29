import type { Metadata } from "next";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import "./globals.css";
import { Providers } from "./providers";
import { Navbar } from "@/components/navbar";

export const metadata: Metadata = {
  title: "ClipCognition",
  description: "Video analysis and semantic search powered by Azure AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-bs-theme="light" data-scroll-behavior="smooth" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Providers>
          <Navbar />
          <main className="container-xl py-4 px-4">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
