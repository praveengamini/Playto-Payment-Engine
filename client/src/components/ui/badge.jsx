import { cn } from "@/lib/utils";

const statusClasses = {
  pending: "bg-amber-100 text-amber-800 border-amber-200",
  processing: "bg-blue-100 text-blue-800 border-blue-200",
  completed: "bg-emerald-100 text-emerald-800 border-emerald-200",
  failed: "bg-rose-100 text-rose-800 border-rose-200",
};

function Badge({ className, variant = "default", ...props }) {
  const statusClass = statusClasses[variant] ?? "bg-slate-100 text-slate-800 border-slate-200";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        statusClass,
        className
      )}
      {...props}
    />
  );
}

export { Badge };
