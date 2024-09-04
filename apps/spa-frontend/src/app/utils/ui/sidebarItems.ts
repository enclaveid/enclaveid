import {
  ChatBubbleLeftRightIcon,
  PuzzlePieceIcon,
  UserCircleIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';

export const sidebarItems = {
  'Social Discovery': [
    {
      icon: UsersIcon,
      text: 'Find similar users',
      href: '/dashboard/socials',
    },
    {
      icon: ChatBubbleLeftRightIcon,
      text: 'Messages',
      href: '/dashboard/chat',
    },
  ],
  'Your profile': [
    {
      icon: UserCircleIcon,
      text: 'Traits Dashboard',
      href: '/dashboard/traits',
    },
    {
      icon: PuzzlePieceIcon,
      text: 'Interests',
      href: '/dashboard/interests',
    },
  ],
};
