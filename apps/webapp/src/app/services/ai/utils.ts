import { Tool, ToolSet } from 'ai';
import { causalInferenceActions } from './causalInferenceAgent/actions';
import { quantitativeActions } from './quantitativeAgent/actions';
import { jsonrepair } from 'jsonrepair';

export async function makeApiRequest(
  endpoint: string,
  data: Record<string, any>
) {
  const response = await fetch(`http://127.0.0.1:8000/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) throw new Error(`Failed to fetch ${endpoint}`);
  return response.json();
}

export function serializeActions(actions: ToolSet): string {
  return Object.entries(actions)
    .map(([name, action]) => {
      const params = Object.keys(action.parameters.shape);
      const functionSignature = `${name}(${params.join(', ')})`;
      return `- ${functionSignature}: ${(action as Tool).description}`;
    })
    .join('\n');
}

export async function parseAndExecuteActions(
  rawAssistantMessage: string
): Promise<{
  actionsResults: string | null;
  finalResult: string | null;
}> {
  // Extract JSON object using regex
  const jsonMatch = rawAssistantMessage.match(/\{[\s\S]*\}/);

  if (!jsonMatch) {
    // If there are no actions to execute, it's the final result
    return {
      actionsResults: null,
      finalResult: rawAssistantMessage,
    };
  }

  const actionsArray = JSON.parse(jsonrepair(jsonMatch[0])).actions;

  const allActions = {
    ...causalInferenceActions,
    ...quantitativeActions,
  };

  const results = await Promise.all(
    actionsArray.map(
      async (action: { name: string; args: Record<string, any> }) => {
        const { name, args } = action;
        const actionFunction = allActions[name as keyof typeof allActions];

        if (!actionFunction) {
          throw new Error(`Unknown action: ${name}`);
        }

        const result = await actionFunction.execute?.(args as any);
        return { name, args, result };
      }
    )
  );

  // Transform array of results into a record
  const resultsRecord = results.reduce(
    (acc, { name, args, result }) => ({
      ...acc,
      [name]: { args, result },
    }),
    {} as Record<string, { args: Record<string, any>; result: any }>
  );

  return {
    actionsResults: JSON.stringify(resultsRecord, null, 2),
    finalResult: null,
  };
}
