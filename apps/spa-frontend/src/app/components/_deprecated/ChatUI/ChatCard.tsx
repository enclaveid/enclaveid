function ChatCard() {
  return (
    <div className="pl-2.5 pr-5 py-[26px] border-b border-[#E5E8EE] flex items-center gap-2.5">
      <img
        src="https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?q=80&w=2662&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
        alt="PP"
        className="w-11 h-11 rounded-full object-cover"
      />
      <div className="flex flex-col gap-[7px] flex-1">
        <div className="flex items-center justify-between">
          <h1 className="text-passiveLinkColor font-medium leading-[19x]">
            Peter Thiel
          </h1>
          <h6 className="text-passiveLinkColor text-sm leading-4">12:32am</h6>
        </div>
        <p className="line-clamp-1 text-passiveLinkColor text-sm leading-4">
          I believe AI will be a game changer Lorem ipsum dolor sit amet
          consectetur adipisicing elit. Perspiciatis aspernatur quasi eligendi
          sint sit. Numquam eaque nobis rerum iusto incidunt.
        </p>
      </div>
    </div>
  );
}

export { ChatCard };
