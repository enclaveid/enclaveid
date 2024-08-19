const baseClasses =
  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium uppercase w-fit';

const variants = {
  reactive_needs: {
    classes: 'bg-orange-100 text-orange-800',
    text: 'reactive',
  },
  knowledge_progression: {
    classes: 'bg-green-100 text-green-800',
    text: 'proactive',
  },
  sensitive: {
    classes: 'bg-red-100 text-red-800',
    text: 'sensitive',
  },
};

export function SmallBadge({ variant }: { variant: keyof typeof variants }) {
  return (
    <span className={`${baseClasses} ${variants[variant].classes}`}>
      {variants[variant].text}
    </span>
  );
}
