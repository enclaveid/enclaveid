'use server';

import { signIn } from '../../services/auth';

export async function githubSignIn() {
  await signIn('github');
}
