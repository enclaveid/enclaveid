import { AiChat } from '../../../components/ai-chat/ai-chat';

export default async function Home() {
  return (
    <div className="flex flex-row gap-4 h-full">
      <AiChat />
    </div>
  );
}
