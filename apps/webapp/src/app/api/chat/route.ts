import { streamText } from 'ai';
import { genAiModel } from '../../services/azure/genAiModel';

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: genAiModel('gpt-4o'),
    messages,
    tools: {
      // TODO: server-side tool with execute function:
      // getWeatherInformation: {
      //   description: 'show the weather in a given city to the user',
      //   parameters: z.object({ city: z.string() }),
      //   execute: async ({}: { city: string }) => {
      //     const weatherOptions = ['sunny', 'cloudy', 'rainy', 'snowy', 'windy'];
      //     return weatherOptions[
      //       Math.floor(Math.random() * weatherOptions.length)
      //     ];
      //   },
      // },
    },
  });

  return result.toDataStreamResponse();
}
