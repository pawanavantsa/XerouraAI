import Link from "next/link";

const SIZES = {
  sm: { box: "w-7 h-7", icon: "w-3.5 h-3.5", text: "text-sm font-semibold" },
  md: { box: "w-9 h-9", icon: "w-4 h-4", text: "text-lg font-semibold" },
  lg: { box: "w-10 h-10", icon: "w-5 h-5", text: "text-xl font-bold" },
} as const;

type Size = keyof typeof SIZES;

type BrandMarkProps = {
  size?: Size;
  /** On purple gradient panels (login/signup left column) */
  variant?: "default" | "onDark";
  className?: string;
};

export function BrandMark({ size = "md", variant = "default", className = "" }: BrandMarkProps) {
  const s = SIZES[size];
  const isDark = variant === "onDark";

  return (
    <Link
      href="/"
      className={`flex items-center gap-2.5 rounded-xl outline-none hover:opacity-95 transition-opacity focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900 ${className}`}
    >
      <div
        className={
          isDark
            ? `${s.box} rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center ring-1 ring-white/15`
            : `${s.box} rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/25 ring-1 ring-white/15`
        }
      >
        <svg className={`${s.icon} text-white`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
      <span className={`${s.text} tracking-tight ${isDark ? "text-white" : "text-slate-900 dark:text-white"}`}>
        Xeroura AI
      </span>
    </Link>
  );
}
