import React from 'react';
import { BRAND_CONFIG } from '../config/brand';

interface BrandLogoProps {
  size?: 'sm' | 'md' | 'lg';
  showBadge?: boolean;
  showTagline?: boolean;
  className?: string;
}

export const BrandSymbol: React.FC<{ size?: 'sm' | 'md' | 'lg'; className?: string }> = ({
  size = 'md',
  className = '',
}) => {
  const sizeMap = {
    sm: { box: 'w-7 h-7', px: 28 },
    md: { box: 'w-9 h-9', px: 36 },
    lg: { box: 'w-11 h-11', px: 44 },
  };

  const current = sizeMap[size];

  return (
    <div
      className={`relative flex items-center justify-center rounded-xl bg-slate-900 border border-indigo-500/30 shadow-md shadow-indigo-950/40 shrink-0 ${current.box} ${className}`}
    >
      <svg
        viewBox="0 0 32 32"
        width={current.px * 0.75}
        height={current.px * 0.75}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="transform transition-transform group-hover:scale-105"
      >
        {/* Outer coordinated agent perimeter */}
        <path
          d="M16 4.5L25.5 10V22L16 27.5L6.5 22V10L16 4.5Z"
          stroke="#4F46E5"
          strokeWidth="1.5"
          strokeLinejoin="round"
          strokeDasharray="2 1.5"
          opacity="0.6"
        />
        {/* Inner resolution prism */}
        <path
          d="M16 8L22.5 11.75V20.25L16 24L9.5 20.25V11.75L16 8Z"
          fill="#1E1B4B"
          stroke="#6366F1"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        {/* Central convergence node */}
        <circle cx="16" cy="16" r="2.75" fill="#818CF8" />
        {/* Agent coordination pathways */}
        <path
          d="M16 8V13.25M22.5 20.25L18.2 17.5M9.5 20.25L13.8 17.5"
          stroke="#C7D2FE"
          strokeWidth="1.25"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
};

export const BrandLogo: React.FC<BrandLogoProps> = ({
  size = 'md',
  showBadge = true,
  showTagline = false,
  className = '',
}) => {
  const textSizes = {
    sm: 'text-base',
    md: 'text-lg',
    lg: 'text-xl',
  };

  return (
    <div className={`flex items-center space-x-3 group ${className}`}>
      <BrandSymbol size={size} />
      <div className="flex flex-col">
        <div className="flex items-center space-x-2">
          <span
            className={`font-bold tracking-tight text-slate-900 dark:text-white font-sans ${textSizes[size]}`}
          >
            {BRAND_CONFIG.name}
          </span>
          {showBadge && (
            <span className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/20 font-mono">
              Enterprise
            </span>
          )}
        </div>
        {showTagline && (
          <span className="text-[11px] text-slate-500 dark:text-slate-400 font-sans tracking-normal hidden md:inline-block">
            {BRAND_CONFIG.primaryTagline}
          </span>
        )}
      </div>
    </div>
  );
};
