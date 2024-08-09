const sizeMap = {
  xs: 'w-5', // 1.25rem, 20px
  sm: 'w-6', // 1.5rem, 24px
  md: 'w-8', // 2rem, 32px
  lg: 'w-10', // 2.5rem, 40px
  xl: 'w-12', // 3rem, 48px
  '2xl': 'w-16', // 4rem, 64px
};

function getFontSize(sizeClass) {
  return (
    {
      'w-5': 'text-[0.4rem]',
      'w-6': 'text-[0.5rem]',
      'w-8': 'text-xs',
      'w-10': 'text-sm',
      'w-12': 'text-base',
      'w-16': 'text-lg',
    }[sizeClass] || 'text-base'
  );
}

export function PercentageCircle({
  percentage,
  size = 'md',
  label,
}: {
  percentage: number;
  size: keyof typeof sizeMap;
  label?: string;
}) {
  const sizeClass = sizeMap[size] || sizeMap.md;
  const viewBoxSize = 100;
  const strokeWidth = 10;
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const getColor = (percent) => {
    if (percent < 33) return '#FF6B6B';
    if (percent < 66) return '#FFD93D';
    return '#6BCB77';
  };

  return (
    <div className="flex items-center justify-between">
      <div className={`relative ${sizeClass} aspect-square`}>
        <svg
          className="w-full h-full -rotate-90"
          viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
        >
          <circle
            className="text-gray-200"
            strokeWidth={strokeWidth}
            stroke="currentColor"
            fill="transparent"
            r={radius}
            cx={viewBoxSize / 2}
            cy={viewBoxSize / 2}
          />
          <circle
            className="transition-all duration-500 ease-out"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            stroke={getColor(percentage)}
            fill="transparent"
            r={radius}
            cx={viewBoxSize / 2}
            cy={viewBoxSize / 2}
            style={{
              strokeDasharray: circumference,
              strokeDashoffset: strokeDashoffset,
            }}
          />
        </svg>
        <div
          className={`text-passiveLinkColor text-sm absolute inset-0 flex items-center justify-center text-center font-bold ${getFontSize(sizeClass)}`}
        >
          {percentage.toFixed(0)}
        </div>
      </div>
      <h1 className="text-passiveLinkColor text-sm font-medium ml-2">
        {label}
      </h1>
    </div>
  );
}
