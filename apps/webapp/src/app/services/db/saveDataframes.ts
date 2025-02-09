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
  id: string; // nodeLabel
  user: string; // propositionSubject (e.g. "Alice", "Bob", or "both")
  proposition: string;
  chunk_ids: bigint[];
  datetimes: string[];
  frequency: bigint;
  edges: string[];
  sentiment: bigint;
  reduced_embedding: bigint[];
}

// TODO: slow as shit. find a proper ORM that supports pgvector + bulk upserts.
export async function saveDataframes(
  phoneNumbers: string[],
  outChunks: OutChunksRow[],
  outNodes: OutNodesRow[]
): Promise<void> {
  try {
    await prisma.$transaction(async (tx) => {
      // 1) Gather phoneNumber records (and their user) so we know which Users to link later
      const phoneNumberRecords = await tx.phoneNumber.findMany({
        where: { phoneNumber: { in: phoneNumbers } },
        include: { user: true },
      });

      // Collect unique userIds from these phone records
      const userIds = Array.from(
        new Set(phoneNumberRecords.map((rec) => rec.userId))
      );

      // 2) CREATE MANY RawDataChunk for all outChunks (skip duplicates based on unique chunkNumber)
      await tx.rawDataChunk.createMany({
        data: outChunks.map((chunk) => ({
          chunkNumber: Number(chunk.chunk_id),
          fromDatetime: chunk.start_dt,
          toDatetime: chunk.end_dt,
          sentiment: Number(chunk.sentiment),
          rawData: chunk.messages_str,
          // We can't set embedding here (vector type); will set it via $executeRaw below
        })),
        skipDuplicates: true,
      });

      // 3) For each OutChunksRow, UPDATE (a) any changed scalar fields,
      //    (b) connect phoneNumbers, (c) set the embedding via raw SQL.
      for (const chunk of outChunks) {
        // (a) Update scalar fields (in case they changed) and connect phoneNumbers
        await tx.rawDataChunk.update({
          where: { chunkNumber: Number(chunk.chunk_id) }, // chunkNumber is unique
          data: {
            fromDatetime: chunk.start_dt,
            toDatetime: chunk.end_dt,
            sentiment: Number(chunk.sentiment),
            rawData: chunk.messages_str,
            phoneNumbers: {
              connect: phoneNumbers.map((ph) => ({ phoneNumber: ph })),
            },
          },
        });

        // (b) Update the vector/embedding field via raw SQL
        const embeddingArrayLiteral = `ARRAY[${chunk.reduced_embedding.join(
          ','
        )}]`;
        await tx.$executeRawUnsafe(`
          UPDATE "RawDataChunk"
          SET "embedding" = (${embeddingArrayLiteral})::vector
          WHERE "chunkNumber" = ${Number(chunk.chunk_id)}
        `);
      }

      // 4) CREATE MANY CausalGraphNode for outNodes (skip duplicates on nodeLabel)
      await tx.causalGraphNode.createMany({
        data: outNodes.map((node) => ({
          nodeLabel: node.id,
          proposition: node.proposition,
          edges: node.edges,
          sentiment: Number(node.sentiment),
          datetimes: node.datetimes.map((dt) => new Date(dt)),
          frequency: Number(node.frequency),
          // embedding set via raw SQL later
        })),
        skipDuplicates: true,
      });

      // 5) For each OutNodesRow (with sanitized ID), UPDATE scalars, connect to rawDataChunks,
      //    connect to user(s), and set the embedding via raw SQL.
      for (const node of outNodes) {
        // Decide which users to connect to.
        // If `node.user` is "both", connect all userIds from phoneNumbers.
        // Otherwise, attempt to match by user.name for a single user, or skip if not found.
        let userIdsToConnect: string[] = [];

        if (node.user === 'both') {
          userIdsToConnect = userIds;
        } else {
          // Attempt to find a single user among phoneNumberRecords whose user.name === node.user
          const match = phoneNumberRecords.find(
            (rec) => rec.user?.name === node.user
          );
          if (match?.userId) {
            userIdsToConnect.push(match.userId);
          }
        }

        // (a) Update the node to set scalars & connect relevant rawDataChunks + users
        await tx.causalGraphNode.update({
          where: { nodeLabel: node.id },
          data: {
            proposition: node.proposition,
            edges: node.edges,
            sentiment: Number(node.sentiment),
            frequency: Number(node.frequency),
            datetimes: node.datetimes.map((dt) => new Date(dt)),
            rawDataChunks: {
              connect: node.chunk_ids.map((cid) => ({
                chunkNumber: Number(cid),
              })),
            },
            propositionSubjects: {
              connect: userIdsToConnect.map((uid) => ({ id: uid })),
            },
          },
        });

        // (b) Update the vector/embedding field for the node via raw SQL
        const nodeEmbedding = `ARRAY[${node.reduced_embedding.join(',')}]`;
        await tx.$executeRawUnsafe(`
          UPDATE "CausalGraphNode"
          SET "embedding" = (${nodeEmbedding})::vector
          WHERE "nodeLabel" = '${node.id}'
        `);
      }
    });
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
