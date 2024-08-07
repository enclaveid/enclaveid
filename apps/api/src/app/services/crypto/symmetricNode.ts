import { prisma } from '@enclaveid/backend';
import crypto from 'crypto';

export async function encryptResponsePayload(
  userId: string,
  payload: unknown,
): Promise<{
  encryptedPayload: string;
  nonce: string;
}> {
  const sessionKey = await prisma.user
    .findUnique({
      where: { id: userId },
      select: { session: { select: { sessionSecret: true } } },
    })
    .then((user) => user?.session?.sessionSecret);

  const nonce = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-ctr', sessionKey, nonce);
  const encryptedPayload =
    cipher.update(JSON.stringify(payload), 'utf8', 'base64') +
    cipher.final('base64');

  return {
    encryptedPayload,
    nonce: nonce.toString('base64'),
  };
}

export async function decryptRequestPayload(
  userId: string,
  encryptedPayload: string,
  nonce: string,
): Promise<string> {
  const sessionKey = await prisma.user
    .findUnique({
      where: { id: userId },
      select: { session: { select: { sessionSecret: true } } },
    })
    .then((user) => user?.session?.sessionSecret);

  const decipher = crypto.createDecipheriv(
    'aes-256-ctr',
    sessionKey,
    Buffer.from(nonce, 'base64'),
  );
  return (
    decipher.update(encryptedPayload, 'base64', 'utf8') + decipher.final('utf8')
  );
}
