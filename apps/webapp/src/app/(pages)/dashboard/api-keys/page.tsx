import { getApiKeys } from '../../../actions/api-keys/getApiKeys';
import ApiKeysTable from '../../../components/api-keys-table';

export default async function ApiKeysPage() {
  // Fetch data server-side
  const apiKeys = await getApiKeys();

  return <ApiKeysTable initialApiKeys={apiKeys} />;
}
