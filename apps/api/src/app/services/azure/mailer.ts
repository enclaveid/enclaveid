import { EmailClient } from '@azure/communication-email';

const emailClient = new EmailClient(process.env.AZURE_EMAIL_CONNECTION_STRING);
const senderAddress =
  'DoNotReply@9996352e-b5cf-4ac3-9058-5a8adb2c225e.azurecomm.net';

export async function sendEmail(to: string, subject: string, body: string) {
  const emailMessage = {
    sender: `EnclaveID <${senderAddress}>`,
    senderAddress,
    content: {
      subject,
      html: body,
    },
    recipients: {
      to: [{ address: to }],
    },
  };

  const poller = await emailClient.beginSend(emailMessage);

  await poller.pollUntilDone();
}
