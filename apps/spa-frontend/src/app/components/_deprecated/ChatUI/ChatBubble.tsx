import classNames from 'classnames';

interface ChatBubbleProps {
  message: string;
  name: string;
  date: string; // Change later with Date
  index: number;
}

function ChatBubble({ name, message, date, index }: ChatBubbleProps) {
  return (
    <article className="flex flex-col gap-3 odd:items-end">
      <div
        className={classNames(
          'rounded-lg max-w-[430px] w-full p-3',
          index % 2 === 0
            ? 'rounded-tr-none bg-[#E9F3EC]'
            : 'rounded-bl-none bg-[#DAE3EC]',
        )}
      >
        <p className="text-passiveLinkColor">{message}</p>
      </div>
      <p className="text-passiveLinkColor text-sm">
        {name} - <span>{date}</span>
      </p>
    </article>
  );
}

export { ChatBubble };
