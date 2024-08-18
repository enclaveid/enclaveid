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
      href: '/socials',
    },
    {
      icon: ChatBubbleLeftRightIcon,
      text: 'Messages',
      href: '/chat',
    },
  ],
  'Your profile': [
    {
      icon: UserCircleIcon,
      text: 'Traits Dashboard',
      href: '/dashboard',
    },
    {
      icon: PuzzlePieceIcon,
      text: 'Interests',
      href: '/interests',
      chip: 'soon',
    },
  ],
};
