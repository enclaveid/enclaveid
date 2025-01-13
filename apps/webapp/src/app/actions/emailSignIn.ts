'use server';

import { signIn } from '../services/auth';

export async function emailSignIn(email: string) {
  await signIn('email', { email });
}
