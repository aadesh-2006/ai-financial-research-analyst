import React from "react";

export const LoadingSkeleton: React.FC<{ count?: number; height?: string }> = ({
  count = 1,
  height = "h-24",
}) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full animate-pulse">
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className={`${height} bg-slate-800/40 border border-slate-800 rounded-xl`}
        />
      ))}
    </div>
  );
};

export const ChartSkeleton: React.FC = () => {
  return (
    <div className="h-72 w-full bg-slate-800/30 border border-slate-800 rounded-xl p-6 flex flex-col justify-between animate-pulse">
      <div className="w-1/3 h-5 bg-slate-800 rounded" />
      <div className="h-44 w-full bg-slate-800/40 rounded flex items-end gap-3 px-6 py-3">
        <div className="w-1/6 h-2/3 bg-slate-700/40 rounded" />
        <div className="w-1/6 h-full bg-slate-700/50 rounded" />
        <div className="w-1/6 h-4/5 bg-slate-700/40 rounded" />
        <div className="w-1/6 h-1/2 bg-slate-700/30 rounded" />
        <div className="w-1/6 h-3/4 bg-slate-700/40 rounded" />
        <div className="w-1/6 h-5/6 bg-slate-700/50 rounded" />
      </div>
      <div className="w-1/4 h-3 bg-slate-800 rounded self-center" />
    </div>
  );
};