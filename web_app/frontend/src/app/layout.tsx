import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RAG Web Console",
  description: "RAG-powered Q&A system with admin panel",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
