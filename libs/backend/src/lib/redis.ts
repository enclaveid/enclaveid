import Redis from 'ioredis';

export const redis = new Redis.Cluster([
  {
    port: parseInt(process.env.REDIS_PORT || '6379'),
    host:
      process.env.REDIS_HOST ||
      'enclaveid-redis-master.default.svc.cluster.local',
  },
]);
