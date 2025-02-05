import { parquetRead } from 'hyparquet';
import { compressors } from 'hyparquet-compressors';
import { useGraphVizFileData } from './graph-viz-file-context';
import { useForm, FormProvider } from 'react-hook-form';
import { Card } from '@enclaveid/ui/card';
import { CardContent } from '@enclaveid/ui/card';
import { Input } from '@enclaveid/ui/input';
import { Button } from '@enclaveid/ui/button';
import { FormField } from '@enclaveid/ui/form';
import { FormItem } from '@enclaveid/ui/form';
import { FormLabel } from '@enclaveid/ui/form';
import { FormControl } from '@enclaveid/ui/form';
import { useCallback } from 'react';

export function GraphVizFileLoader() {
  const { setChunkData, setNodeData } = useGraphVizFileData();
  const form = useForm();

  const handleParquetFile = useCallback(
    async (file: File, setData: (data: any) => void) => {
      try {
        // Create a new Blob from the file and then get its ArrayBuffer
        const blob = new Blob([file], { type: file.type });
        const arrayBuffer = await blob.arrayBuffer();
        await parquetRead({
          file: arrayBuffer,
          compressors,
          rowFormat: 'object',
          onComplete: (data) => {
            console.log('File data:', data);
            setData(data);
          },
        });
      } catch (error) {
        console.error('Error processing parquet file:', error);
      }
    },
    []
  );

  const onSubmit = useCallback(
    async (data: any) => {
      try {
        const chunkFile = data.chunkFile?.[0];
        const nodeFile = data.nodeFile?.[0];

        if (chunkFile) {
          await handleParquetFile(chunkFile, setChunkData);
        }
        if (nodeFile) {
          await handleParquetFile(nodeFile, setNodeData);
        }
      } catch (error) {
        console.error('Error loading parquet files:', error);
      }
    },
    [handleParquetFile, setChunkData, setNodeData]
  );

  return (
    <div className="flex flex-col items-center min-h-screen p-8">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormProvider {...form}>
              <FormField
                control={form.control}
                name="chunkFile"
                render={({ field: { onChange, ...field } }) => (
                  <FormItem>
                    <FormLabel>Chunk Data File</FormLabel>
                    <FormControl>
                      <Input
                        type="file"
                        accept=".parquet,.snappy"
                        onChange={(e) => {
                          onChange(e.target.files);
                        }}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="nodeFile"
                render={({ field: { onChange, ...field } }) => (
                  <FormItem>
                    <FormLabel>Node Data File</FormLabel>
                    <FormControl>
                      <Input
                        type="file"
                        accept=".parquet,.snappy"
                        onChange={(e) => {
                          onChange(e.target.files);
                        }}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <Button type="submit" className="w-full">
                Load Files
              </Button>
            </FormProvider>
          </form>
        </CardContent>
      </Card>
      <div className="mt-4 text-muted-foreground">
        Check browser console for data after submitting
      </div>
    </div>
  );
}
