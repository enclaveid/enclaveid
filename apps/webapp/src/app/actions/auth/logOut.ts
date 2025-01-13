'use server';

import { signOut } from '../../services/auth';

export async function logOut() {
  await signOut();
}
