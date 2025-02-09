import { prisma } from './prisma';

export interface OutChunksRow {
  chunk_id: bigint;
  sentiment: bigint;
  start_dt: Date;
  end_dt: Date;
  messages_str: string;
  reduced_embedding: bigint[];
}

export interface OutNodesRow {
  id: string; // label of the node
  user: string; // can be "both" or a user name
  proposition: string;
  chunk_ids: bigint[];
  datetimes: string[];
  frequency: bigint;
  edges: string[];
  sentiment: bigint;
  reduced_embedding: bigint[];
}

export async function saveDataframes(
  phoneNumbers: string[],
  outChunks: OutChunksRow[],
  outNodes: OutNodesRow[]
): Promise<void> {
  try {
    await prisma.$transaction(async (tx) => {
      //
      // 1) Find all phoneNumber records (and their Users) for the incoming phoneNumbers
      //
      const phoneNumberRecords = await tx.phoneNumber.findMany({
        where: {
          phoneNumber: { in: phoneNumbers },
        },
        include: {
          user: true,
        },
      });
      // Collect all associated userIds (from the found phoneNumbers)
      const phoneNumberUserIds = [
        ...new Set(phoneNumberRecords.map((pn) => pn.user.id)),
      ];

      //
      // 2) Upsert RawDataChunk records for each row in outChunks
      //    and connect them to the phoneNumbers.
      //
      for (const row of outChunks) {
        // Convert the embedding if necessary (bigint -> number)
        const embedding = row.reduced_embedding.map((val) => Number(val));

        // chunk_id is bigint, so convert to number where needed
        const chunkNumber = Number(row.chunk_id);

        await tx.rawDataChunk.upsert({
          where: { chunkNumber }, // chunkNumber is unique in your schema
          update: {
            // Potentially update any fields that might change
            sentiment: Number(row.sentiment),
            fromDatetime: row.start_dt,
            toDatetime: row.end_dt,
            rawData: row.messages_str,
            embedding,
          },
          create: {
            chunkNumber,
            sentiment: Number(row.sentiment),
            fromDatetime: row.start_dt,
            toDatetime: row.end_dt,
            rawData: row.messages_str,
            embedding,
            // Connect to all phoneNumbers specified in the phoneNumbers argument
            phoneNumbers: {
              connect: phoneNumbers.map((p) => ({ phoneNumber: p })),
            },
          },
        });
      }

      //
      // 3) Upsert CausalGraphNode records for each row in outNodes,
      //    connect them to the relevant RawDataChunks (by chunkNumber),
      //    and also to the appropriate Users.
      //
      for (const row of outNodes) {
        const nodeLabel = row.id;
        const edges = row.edges; // string[]
        const proposition = row.proposition;
        const sentiment = Number(row.sentiment);
        const embedding = row.reduced_embedding.map((val) => Number(val));
        // Convert string array to Date[]
        const datetimes = row.datetimes.map((dt) => new Date(dt));

        // Connect to rawDataChunks by their unique chunkNumber
        const connectChunks = row.chunk_ids.map((cid) => ({
          chunkNumber: Number(cid),
        }));

        // Decide which users to connect:
        // if row.user === "both", connect all userIds from phoneNumbers
        // otherwise, find/create a single user by name = row.user
        let connectUsers: { id: string }[] = [];

        if (row.user === 'both') {
          connectUsers = phoneNumberUserIds.map((id) => ({ id }));
        } else {
          // If row.user is a specific name, find or create that user
          const userName = row.user.trim();

          // Attempt to find a user with this name
          const existingUser = await tx.user.findFirst({
            where: { name: userName },
            select: { id: true },
          });

          if (existingUser) {
            connectUsers = [{ id: existingUser.id }];
          } else {
            // If no user found, create a new one
            // TODO: (If you do NOT want to allow creation here, you can throw instead)
            // const newUser = await tx.user.create({
            //   data: {
            //     name: userName,
            //   },
            //   select: { id: true },
            // });
            // connectUsers = [{ id: newUser.id }];
            throw new Error(
              `User '${userName}' with any of the phone numbers '${phoneNumbers}' not found!`
            );
          }
        }

        await tx.causalGraphNode.upsert({
          where: { nodeLabel }, // nodeLabel is unique
          update: {
            proposition,
            edges,
            sentiment,
            datetimes,
            embedding,
            // Reconnect the chunks if needed
            rawDataChunks: {
              set: [], // Clear existing connections (optional, if you want a "replace" approach)
              connect: connectChunks,
            },
            // Reconnect propositionSubjects as well (optional "replace" approach)
            propositionSubjects: {
              set: [],
              connect: connectUsers,
            },
          },
          create: {
            nodeLabel,
            proposition,
            edges,
            sentiment,
            datetimes,
            embedding,
            rawDataChunks: {
              connect: connectChunks,
            },
            propositionSubjects: {
              connect: connectUsers,
            },
          },
        });
      }
    });

    console.log('Dataframes saved successfully.');
  } catch (error) {
    if (error instanceof Error) {
      console.error('Error saving dataframes:', {
        message: error.message,
        stack: error.stack,
      });
    }
    throw error;
  }
}
