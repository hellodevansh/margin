export function LoadingState({ label = "Loading audit intelligence" }: { label?: string }) {
  return <div className="flex min-h-[70vh] items-center justify-center"><div className="text-center"><div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border border-white/10 border-t-[#5eead4]" /><p className="text-xs text-[#858b96]">{label}</p></div></div>;
}

