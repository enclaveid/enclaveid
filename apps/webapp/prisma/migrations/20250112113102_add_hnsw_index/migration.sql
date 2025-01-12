-- This is added manually since it's not supported by Prisma
-- Drop existing indexes if they exist
DROP INDEX IF EXISTS user_claims_embedding_idx;

-- Create HNSW vector index
CREATE INDEX user_claims_embedding_idx
ON "UserClaim"
USING hnsw (embedding halfvec_cosine_ops);
