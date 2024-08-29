import Redis from 'ioredis';

export const redis =
  process.env.ENABLE_FAKE_OAUTH === 'true'
    ? process.env.NODE_ENV === 'development'
      ? new Redis({
          port: 6379,
          host: 'localhost',
        })
      : new Redis.Cluster([
          {
            port: parseInt(process.env.REDIS_PORT || '6379'),
            host:
              process.env.REDIS_HOST ||
              'enclaveid-redis-master.default.svc.cluster.local',
          },
        ])
    : null;
