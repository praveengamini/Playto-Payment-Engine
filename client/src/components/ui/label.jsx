import { cn } from "@/lib/utils";

function Label({ className, ...props }) {
  return (
    <label
      className={cn("text-sm font-medium leading-none text-slate-700 dark:text-slate-300", className)}
      {...props}
    />
  );
}

export { Label };
