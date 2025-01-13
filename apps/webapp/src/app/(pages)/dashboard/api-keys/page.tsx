import { Card, CardHeader, CardTitle, CardContent } from '@enclaveid/ui/card';
import { Input } from '@enclaveid/ui/input';
import { Button } from '@enclaveid/ui/button';
import { CopyIcon } from 'lucide-react';
import { getApiKey } from '../../../actions/getApiKey';

export default async function ApiKeysPage() {
  const apiKey = await getApiKey();

  return (
    <div className="container mx-auto py-8">
      <Card>
        <CardHeader>
          <CardTitle>API Key</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Input
            readOnly
            value={apiKey || ''}
            type="text"
            className="font-mono"
          />
          <Button
            // onClick={() => {
            //   navigator.clipboard.writeText(apiKey || '');
            // }}
            variant="outline"
          >
            <CopyIcon className="h-4 w-4" />
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
