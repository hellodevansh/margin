import { Badge } from "@/components/badge";
export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <header className="border-b border-white/[0.07]"><div className="mx-auto flex max-w-[1280px] flex-col gap-5 px-6 py-7 md:flex-row md:items-end md:justify-between md:px-10"><div><div className="mb-3"><Badge tone="accent">{eyebrow}</Badge></div><h1 className="text-3xl font-semibold tracking-[-0.045em] md:text-[34px]">{title}</h1><p className="mt-2 max-w-2xl text-xs leading-6 text-[#858b96]">{description}</p></div>{action}</div></header>;
}
