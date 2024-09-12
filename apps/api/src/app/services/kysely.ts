import { Kysely, PostgresDialect } from 'kysely';
import { kyselyTypes } from '@enclaveid/backend';
import { Pool } from 'pg';

export const kyselyConn = new Kysely<kyselyTypes.DB>({
  dialect: new PostgresDialect({
    pool: new Pool({
      connectionString: process.env.API_DATABASE_URL,
      max: 10,
    }),
  }),
});
