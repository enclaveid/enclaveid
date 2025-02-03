import { readZip } from '../readZip';

// Message media type mapping
const MESSAGE_MEDIA_TYPES: { [key: number]: string | null } = {
  1: 'IMAGE',
  38: 'SEE_ONCE_IMAGE',
  6: 'SEE_ONCE_IMAGE',
  2: 'VIDEO',
  39: 'SEE_ONCE_VIDEO',
  13: 'SEE_ONCE_VIDEO',
  3: 'AUDIO',
  4: 'CONTACT',
  5: 'LOCATION',
  7: 'URL',
  8: 'FILE',
  11: 'GIF',
  14: 'DELETED_MESSAGE',
  15: 'STICKER',
  46: 'POLL',
  54: 'VIDEO_NOTE',
};

function processMessageStruct(
  content: string | null,
  message_type: number | null,
  media_title: string | null
): string {
  let text = content;
  const messageType = message_type;
  const mediaTitle = media_title;

  // If text is empty, try to get the media type
  if (!text) {
    if (messageType) {
      text = `MEDIA: ${MESSAGE_MEDIA_TYPES[messageType] || 'UNKNOWN'}`;
    } else {
      text = '';
    }
  }

  // If the text contains a link and media_title is not empty, replace the full URL with the media title
  if (text.includes('https://') && mediaTitle) {
    const urlStart = text.indexOf('https://');
    const urlEnd =
      text.indexOf(' ', urlStart) === -1
        ? text.length
        : text.indexOf(' ', urlStart);
    text =
      text.substring(0, urlStart) +
      'Sent a link: ' +
      mediaTitle +
      text.substring(urlEnd);
  }

  return text;
}

const EXPECTED_FILE = 'messages.json';

interface InputRecord {
  from: string;
  from_phone_number: string | null;
  to: string;
  to_phone_number: string | null;
  datetime: string;
  content: string;
  message_type: number;
  media_title: string | null;
}

interface OutputRecord {
  from: string;
  from_phone_number: string | null;
  to: string;
  to_phone_number: string | null;
  datetime: Date;
  content: string;
  count: number;
}

export async function parseWhatsappDesktopArchive(
  fileData: ArrayBuffer,
  userPhoneNumber: string
) {
  const buffer = Buffer.from(fileData);
  const rawData = await readZip(buffer, EXPECTED_FILE);

  // Parse JSON directly
  const messages = JSON.parse(
    new TextDecoder().decode(rawData)
  ) as InputRecord[];

  if (!messages || !messages.length) {
    throw new Error('Expected non-empty messages but got empty data.');
  }

  // Process and sort messages
  const processedMessages = messages
    .map((row) => ({
      from: row.from,
      from_phone_number:
        row.from == 'me' ? userPhoneNumber : row.from_phone_number,
      to: row.to,
      to_phone_number: row.to == 'me' ? userPhoneNumber : row.to_phone_number,
      datetime: new Date(row.datetime),
      content: processMessageStruct(
        row.content,
        row.message_type,
        row.media_title
      ),
    }))
    .sort((a, b) => a.datetime.getTime() - b.datetime.getTime());

  // Squash consecutive identical messages
  const squashedMessages = processedMessages.reduce<OutputRecord[]>(
    (acc, curr, idx, arr) => {
      const prev = arr[idx - 1];

      if (
        !prev ||
        prev.from !== curr.from ||
        prev.to !== curr.to ||
        prev.content !== curr.content
      ) {
        // Start new group
        acc.push({
          from: curr.from,
          from_phone_number: curr.from_phone_number,
          to: curr.to,
          to_phone_number: curr.to_phone_number,
          datetime: curr.datetime,
          content: curr.content,
          count: 1,
        });
      } else {
        // Add to existing group
        const lastGroup = acc[acc.length - 1];
        lastGroup.count++;
        lastGroup.content =
          lastGroup.count > 1
            ? `Sent ${lastGroup.count} of ${curr.content}`
            : curr.content;
      }

      return acc;
    },
    []
  );

  return Buffer.from(JSON.stringify(squashedMessages));
}
