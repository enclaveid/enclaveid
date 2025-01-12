import { Pool } from 'pg';
import { Kysely, PostgresDialect } from 'kysely';
import { DB } from './kyselyTypes';

export const db = new Kysely<DB>({
  dialect: new PostgresDialect({
    pool: new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 10,
    }),
  }),
});
