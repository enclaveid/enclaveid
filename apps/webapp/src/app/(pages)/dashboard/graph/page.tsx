'use client';

import { Card, CardContent } from '@enclaveid/ui/card';
import { useState } from 'react';
import { Button } from '@enclaveid/ui/button';
import { Textarea } from '@enclaveid/ui/textarea';

export default function Graph() {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');

  const testEndpoints = async () => {
    try {
      // Example: Test similar_nodes endpoint
      const response = await fetch('http://127.0.0.1:8000/similar_nodes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input }),
      });

      const data = await response.json();
      setOutput(JSON.stringify(data, null, 2));
    } catch (error: any) {
      setOutput(`Error: ${error.message}`);
    }
  };

  return (
    <Card className="flex flex-col w-full">
      <CardContent className="flex flex-1 flex-col gap-4 p-4">
        <Textarea
          placeholder="Enter your query here..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="min-h-[100px]"
        />
        <Button onClick={testEndpoints}>Test Endpoint</Button>
        <Textarea
          placeholder="Output will appear here..."
          value={output}
          readOnly
          className="min-h-[200px]"
        />
      </CardContent>
    </Card>
  );
}
