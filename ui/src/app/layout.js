import "./globals.css";

export const metadata = {
  title: "Scrollhouse Onboarding",
  description: "PS-01 Multi-Agent Client Onboarding Workflow",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
