import { authenticatedProcedure, publicProcedure, router } from '../trpc';
import { observable } from '@trpc/server/observable';
import { z } from 'zod';
import { AppContext } from '../context';
import { TRPCError } from '@trpc/server';
import {
  ChromeUserEventEnum,
  ParsedPayload,
  fromEventPayload,
} from '@enclaveid/shared';
import { connectFreePod } from '../services/fakeOauth/kubernetes';
import { redis } from '@enclaveid/backend';

export const fakeOauth = router({
  startSession: authenticatedProcedure
    .input(
      z.object({
        isMobile: z.boolean(),
        viewport: z.object({
          vh: z.number(),
          vw: z.number(),
        }),
      }),
    )
    .mutation(async ({ ctx, input }) => {
      const {
        isMobile,
        viewport: { vh, vw },
      } = input;

      const {
        user: { id: userId },
      } = ctx as AppContext;

      return await connectFreePod(userId, isMobile, { vh, vw });
    }),
  podEvents: publicProcedure
    .input(z.object({ podName: z.string() }))
    .subscription(async ({ input }) => {
      const podName = input.podName;
      const streamKey = podName;
      const groupName = 'podEventGroup';
      const consumerName = `consumer-${podName}`;

      if (!podName) {
        throw new TRPCError({
          code: 'NOT_FOUND',
          message: 'Pod does not exist.',
        });
      }

      // Ensure the stream and group exist
      await redis
        .xgroup('CREATE', streamKey, groupName, '$', 'MKSTREAM')
        .catch((error) => {
          if (!error.message.includes('BUSYGROUP')) {
            throw new TRPCError({
              code: 'INTERNAL_SERVER_ERROR',
              message: 'Failed to create stream group: ' + error.message,
            });
          }
        });

      return observable<ParsedPayload<ChromeUserEventEnum>>((emit) => {
        const listenToStream = async () => {
          while (true) {
            try {
              const results = await redis.xreadgroup(
                'GROUP',
                groupName,
                consumerName,
                'BLOCK',
                0,
                'STREAMS',
                streamKey,
                '>',
              );
              if (results) {
                results[0][1].forEach(([id, message]) => {
                  const [key, data] = message;
                  const eventPayload = fromEventPayload(data);
                  emit.next({
                    event: eventPayload.event,
                    data: eventPayload.data,
                  });

                  if (
                    eventPayload.event === ChromeUserEventEnum.LOGIN_SUCCESS
                  ) {
                    emit.complete();
                  }

                  // Acknowledge the message
                  redis.xack(streamKey, groupName, id);
                });
              }
            } catch (error) {
              console.error('Error reading from stream:', error);
              await new Promise((resolve) => setTimeout(resolve, 1000)); // Pause before retrying
            }
          }
        };

        // Start listening to the stream
        listenToStream().catch((error) => {
          emit.error(
            new TRPCError({
              code: 'INTERNAL_SERVER_ERROR',
              message: 'Stream read error: ' + error.message,
            }),
          );
        });

        // Cleanup function when unsubscribed
        return () => {
          redis
            .xgroup('DELCONSUMER', streamKey, groupName, consumerName)
            .catch(console.error);
        };
      });
    }),
});
