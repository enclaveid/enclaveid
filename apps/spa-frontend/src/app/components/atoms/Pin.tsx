import React from 'react';

interface PinProps {
  variant?: 'primary' | 'secondary';
  style: React.CSSProperties;
}

function Pin({ variant, style }: PinProps) {
  const combinedStyle =
    variant === 'secondary'
      ? {
          ...style,
          transform: `${style.transform} translateY(-50%)`,
        }
      : style;

  if (variant === 'primary') {
    return (
      <div
        className="flex flex-col items-center justify-center absolute bottom-0"
        style={combinedStyle}
      >
        <div className="w-2.5 h-2.5 rounded-full bg-[#6C7A8A]" />
        <div className="w-[2px] h-4 bg-[#6C7A8A]" />
      </div>
    );
  }
  return (
    <div
      className="w-4 h-4 bg-[#6C7A8A] rounded-full absolute top-1/2"
      style={combinedStyle}
    />
  );
}

export { Pin };
