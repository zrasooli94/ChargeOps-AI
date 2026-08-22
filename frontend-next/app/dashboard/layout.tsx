import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import DashboardShell from "@/components/dashboard/shell";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const cookieStore = await cookies();
  if (!cookieStore.has("chargeops_token")) redirect("/");
  return <DashboardShell>{children}</DashboardShell>;
}
