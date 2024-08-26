import { Pin } from './atoms/Pin';

enum Label {
  VeryLow = 'Very Low',
  Low = 'Low',
  Average = 'Average',
  High = 'High',
  VeryHigh = 'Very High',
}

interface GradientLineProps {
  value: number;
  title: string;
  variant?: 'primary' | 'secondary';
  index: number;
  isDrawer?: boolean;
}

function GradientLine({
  value,
  title,
  variant = 'primary',
  index,
  isDrawer = false,
}: GradientLineProps) {
  const getLabel = (value: number): Label => {
    if (value <= 20) return Label.VeryLow;
    else if (value <= 40) return Label.Low;
    else if (value <= 60) return Label.Average;
    else if (value <= 80) return Label.High;
    else return Label.VeryHigh;
  };

  const label = getLabel(value);

  const pinStyle = {
    left: `${value}%`,
    transform: 'translateX(-50%)',
  };

  const barColors = {
    primary: 'from-primary-gradient-start to-primary-gradient-stop',
    secondary: 'from-secondary-gradient-start to-secondary-gradient-stop',
  };

  const barColor = barColors[variant];
  if (variant === 'secondary') {
    return (
      <div className="flex gap-[18px] items-center">
        {!isDrawer && (
          <span className="text-[#6C7A8A] font-medium leading-4 text-sm max-w-[142px] w-full text-right">
            {title}
          </span>
        )}
        <div
          className={`h-2.5 rounded-full w-full bg-gradient-to-r ${barColor} relative`}
        >
          <Pin style={pinStyle} variant={variant} />
          {(isDrawer || index === 0) && (
            <div className="flex items-center justify-between absolute -top-8 w-full ">
              <span className="text-[#5799E6] text-sm font-medium leading-4">
                Low
              </span>
              <span className="text-[#30A78A] text-sm font-medium leading-4">
                High
              </span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full gap-6">
      <div className="flex items-center justify-between">
        <span className="text-[#6C7A8A] font-medium leading-[19px]">
          {title}
        </span>
        <span className="text-greenBg font-medium leading-[19px]">{label}</span>
      </div>
      <div className="flex gap-[18px] items-center">
        <div
          className={`h-2.5 rounded-full w-full bg-gradient-to-r ${barColor} relative`}
        >
          <Pin style={pinStyle} variant={variant} />
        </div>
      </div>
    </div>
  );
}

export { GradientLine };
