import { ChatIcon, SearchIcon } from '../Icons';
import { Sidebar } from '../Sidebar';
import { SidebarContainer } from '../containers/SidebarContainer';
import { ChatBubble } from './ChatBubble';
import { ChatCard } from './ChatCard';
import { ChatNavbar } from './ChatNavbar';
import { ChatSendMessage } from './ChatSendMessage';

function ChatPage() {
  return (
    <div className="h-screen bg-white flex sm:flex-row flex-col">
      <SidebarContainer>
        <Sidebar />
      </SidebarContainer>
      <div className="flex flex-1 pt-12 px-6">
        <div className="h-[745px] flex flex-1 border border-[#E5E8EE] rounded-3xl">
          <div className="w-[220px] lg:w-[333px] flex flex-col shrink-0 border-r border-[#E5E8EE]">
            <div className="pt-3.5 pb-4 px-2.5 flex flex-col gap-6 border-b border-[#E5E8EE]">
              <div className="flex items-center justify-between px-1">
                <h1 className="text-passiveLinkColor font-medium text-2xl leading-7">
                  Chat
                </h1>
                <button className="p-2 border rounded-md border-[#E5E8EE]">
                  <ChatIcon />
                </button>
              </div>
              <div className="relative px-2.5">
                <input
                  type="text"
                  className="border border-[#E5E8EE] rounded-md w-full h-[38px] pl-[9px]"
                />
                <span className="absolute top-1/2 -translate-y-1/2 right-5">
                  <SearchIcon />
                </span>
              </div>
            </div>
            <div className="flex flex-col flex-1 overflow-y-auto">
              <ChatCard />
            </div>
          </div>
          <div className="w-full flex flex-col">
            <ChatNavbar />
            <div className="flex flex-col justify-end flex-1 px-4 gap-10 pb-4">
              <ChatBubble
                message="Do you think AI is a paradigm shift, or just a fad?"
                name="You"
                date="12:32am"
                index={0}
              />
              <ChatBubble
                message="I believe AI will be a game changer."
                name="Peter Thiel"
                date="12:32am"
                index={1}
              />
            </div>
            <div className="py-3 px-2.5 border-t border-[#E5E8EE]">
              <ChatSendMessage />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export { ChatPage };
