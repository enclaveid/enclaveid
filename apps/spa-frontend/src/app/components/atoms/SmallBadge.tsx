import { ActivityType } from '@prisma/client';

const baseClasses =
  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium uppercase w-fit';

const variants: Record<
  ActivityType & 'sensitive',
  { classes: string; text: string }
> = {
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
  unknown: {
    classes: 'bg-gray-100 text-gray-800',
    text: 'unknown',
  },
};

export function SmallBadge({
  variant,
}: {
  variant: ActivityType | 'sensitive';
}) {
  return (
    <span className={`${baseClasses} ${variants[variant].classes}`}>
      {variants[variant].text}
    </span>
  );
}
