import React from "react";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "emerald" | "rose" | "amber" | "sky" | "slate" | "purple";
  size?: "sm" | "md";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "slate",
  size = "sm",
  className = "",
}) => {
  const variantStyles = {
    emerald: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    rose: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    amber: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    sky: "bg-sky-500/10 text-sky-400 border-sky-500/30",
    slate: "bg-slate-800 text-slate-300 border-slate-700",
    purple: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  }[variant];

  const sizeStyles = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
  }[size];

  return (
    <span
      className={`inline-flex items-center font-mono font-medium rounded-full border ${variantStyles} ${sizeStyles} ${className}`}
    >
      {children}
    </span>
  );
};