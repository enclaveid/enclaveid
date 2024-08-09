export function LoadingCard() {
  return (
    <div className="flex relative flex-col w-full items-center justify-center rounded-3xl overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-gray-200 before:to-transparent">
      <div className="p-6 w-full flex items-center gap-4 border border-[#E5E8EE] rounded-3xl h-[151px]">
        <div className="w-[101px] h-[101px] rounded-full bg-gray-200/50"></div>
        <div className="flex flex-col">
          <div className="w-[180px] bg-gray-200/50 h-7 rounded"></div>
          <div className="w-[80px] bg-gray-200/50 h-[18px] rounded mt-[9px]"></div>
          <div className="w-[100px] bg-gray-200/50 h-5 rounded mt-3"></div>
        </div>
      </div>
    </div>
  );
}
