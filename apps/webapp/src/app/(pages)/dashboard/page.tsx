import { AiChat } from '../../components/ai-chat/ai-chat';

export default function Page() {
  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="flex-1 rounded-xl bg-muted/50 ">
        <AiChat />
      </div>
    </div>
  );
}
