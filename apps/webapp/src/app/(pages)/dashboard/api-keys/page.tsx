'use client';

import { useEffect, useState } from 'react';
import { Button } from '@enclaveid/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@enclaveid/ui/table';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { CopyIcon, TrashIcon } from 'lucide-react';
import { Alert, AlertDescription } from '@enclaveid/ui/alert';
import { toast } from '@enclaveid/ui/hooks/use-toast';
import { createApiKey } from '../../../actions/api-keys/createApiKey';
import { ApiKey } from '@prisma/client';
import { deleteApiKey } from '../../../actions/api-keys/deleteApiKey';
import { getApiKeys } from '../../../actions/api-keys/getApiKeys';

const columnHelper = createColumnHelper<ApiKey>();

export default function ApiKeysPage({
  initialApiKeys = [],
}: {
  initialApiKeys: ApiKey[];
}) {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>(initialApiKeys);

  const handleDeleteKey = async (apiKeyId: string) => {
    const deletedKey = await deleteApiKey(apiKeyId);
    setApiKeys(apiKeys.filter((key) => key.id !== deletedKey.id));
  };

  const handleGenerateNewKey = async () => {
    const newKey = await createApiKey();
    setApiKeys([...apiKeys, newKey]);
  };

  const handleRefreshKeys = async () => {
    const keys = await getApiKeys();
    setApiKeys(keys);
  };

  useEffect(() => {
    handleRefreshKeys();
  }, []);

  const columns = [
    columnHelper.accessor('key', {
      header: 'Key',
      cell: (info) => {
        const key = info.getValue();
        const visiblePart = key.slice(-8); // Show last 8 characters
        const hiddenPart = '•'.repeat(key.length - 8);

        return (
          <div className="flex items-center gap-2">
            <code className="bg-muted px-2 py-1 rounded font-mono">
              {hiddenPart + visiblePart}
            </code>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                navigator.clipboard.writeText(key);
                toast({
                  title: 'Copied!',
                  description: 'API key copied to clipboard',
                });
              }}
            >
              <CopyIcon className="h-4 w-4" />
            </Button>
          </div>
        );
      },
    }),
    columnHelper.accessor('createdAt', {
      header: 'Created',
      cell: (info) => new Date(info.getValue()).toLocaleDateString(),
    }),
    columnHelper.display({
      id: 'actions',
      cell: (info) => (
        <div className="flex gap-2">
          <Button
            variant="destructive"
            size="sm"
            onClick={() => handleDeleteKey(info.row.original.id)}
          >
            <TrashIcon className="h-4 w-4" />
          </Button>
        </div>
      ),
    }),
  ];

  const table = useReactTable({
    data: apiKeys,
    columns,
    getCoreRowModel: getCoreRowModel(),
    defaultColumn: {},
    state: {},
  });

  return (
    <div className="container mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">API Keys</h1>
        <p className="text-muted-foreground">
          Manage your API keys for accessing the platform programmatically.
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <Button onClick={handleGenerateNewKey}>Generate New API Key</Button>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id}>
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="text-center h-24"
                  >
                    No API keys found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        <Alert>
          <AlertDescription>
            Keep your API keys secure and never share them publicly. If a key is
            compromised, revoke it immediately and generate a new one.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
}
