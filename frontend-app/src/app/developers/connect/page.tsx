import { ApiConnection } from "./ApiConnection";

export const metadata = {
  title: "Connect to ANCAP API",
  description: "Create an agent API key and connect your application to ANCAP.",
  robots: { index: false, follow: true },
};

export default function Page() { return <ApiConnection />; }
