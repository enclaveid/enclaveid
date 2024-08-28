export function DynamicAreaLoading() {
  // Function to generate a random width class
  const randomWidth = () => {
    const widths = ['w-1/4', 'w-1/3', 'w-1/2', 'w-2/3', 'w-3/4', 'w-full'];
    return widths[Math.floor(Math.random() * widths.length)];
  };

  // Function to generate a random height class
  const randomHeight = () => {
    const heights = ['h-4', 'h-5', 'h-6', 'h-8'];
    return heights[Math.floor(Math.random() * heights.length)];
  };

  // Generate an array of loading bars
  const loadingBars = Array.from({ length: 5 }, (_, index) => (
    <div
      key={index}
      className={`${randomWidth()} bg-gray-200/50 ${randomHeight()} rounded mb-4`}
    ></div>
  ));

  return (
    <div className="rounded-3xl relative w-full h-full flex flex-col items-start justify-center overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-gray-200 before:to-transparent">
      <div className="p-6 w-full h-full flex flex-col justify-start gap-4">
        {loadingBars}
      </div>
    </div>
  );
}
