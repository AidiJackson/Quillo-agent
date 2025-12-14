import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export function GlassCard({ children, className = '', onClick }: GlassCardProps) {
  return (
    <div
      onClick={onClick}
      className={`bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl border border-border rounded-[20px] shadow-lg shadow-primary/5 ${className}`}
    >
      {children}
    </div>
  );
}
