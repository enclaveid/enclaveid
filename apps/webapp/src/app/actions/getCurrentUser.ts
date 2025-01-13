'use server';

import { auth } from '../services/auth';
import { cache } from 'react';

// Cache the getCurrentUser function to avoid multiple DB hits
export const getCurrentUser = cache(async () => {
  try {
    const session = await auth();

    if (!session?.user) {
      return null;
    }

    return {
      id: session.user.id!,
      email: session.user.email!,
      name: session.user.name!,
    };
  } catch (error) {
    console.error('Error getting current user:', error);
    return null;
  }
});
