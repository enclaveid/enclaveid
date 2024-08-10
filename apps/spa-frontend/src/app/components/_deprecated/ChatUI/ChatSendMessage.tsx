import { ChatSendIcon } from '../Icons';

function ChatSendMessage() {
  return (
    <div className="relative">
      <input
        type="text"
        className="w-full h-9 outline outline-1 outline-[#E5E8EE] rounded-lg pl-3"
      />
      <button className="bg-greenBg w-7 h-7 flex items-center justify-center rounded-md absolute right-3 top-1/2 -translate-y-1/2">
        <ChatSendIcon />
      </button>
    </div>
  );
}

export { ChatSendMessage };
