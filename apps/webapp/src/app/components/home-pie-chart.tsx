'use client';

import * as React from 'react';
import { Label, Pie, PieChart, Cell } from 'recharts';

import { Card, CardContent } from '@enclaveid/ui/card';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '@enclaveid/ui/chart';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@enclaveid/ui/table';

interface ChartData {
  id: string;
  name: string;
  count: number;
}

function getDynamicColors(length: number): string[] {
  return Array.from({ length }, (_, i) => {
    const saturation = 40 + (30 * i) / (length - 1);
    const lightness = 25 + (10 * i) / (length - 1);
    return `hsl(120, ${saturation}%, ${lightness}%)`;
  });
}

export async function HomePieChart({ data }: { data: ChartData[] }) {
  // Sort data by count in descending order
  const sortedData = React.useMemo(() => {
    return [...data].sort((a, b) => b.count - a.count);
  }, [data]);

  const totalUserClaims = React.useMemo(() => {
    return sortedData.reduce((acc, curr) => acc + curr.count, 0);
  }, [sortedData]);

  // Generate color palette based on the data length
  const dynamicColors = React.useMemo(() => {
    return getDynamicColors(sortedData.length);
  }, [sortedData.length]);

  return (
    <Card className="flex flex-col">
      <CardContent className="flex-1 pb-0">
        <Table className="mb-4">
          <TableHeader>
            <TableRow>
              <TableHead className="text-center"></TableHead>
              <TableHead className="text-left">Name</TableHead>
              <TableHead className="text-left">Count</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedData.map((item, index) => (
              <TableRow key={item.id}>
                <TableCell>
                  <div
                    className="h-4 w-4 rounded"
                    style={{ backgroundColor: dynamicColors[index] }}
                  />
                </TableCell>
                <TableCell>{item.name.replace(/\s*\([^)]*\)/g, '')}</TableCell>
                <TableCell className="text-right">
                  {item.count.toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <ChartContainer
          config={{}}
          className="mx-auto aspect-square max-h-[250px]"
        >
          <PieChart>
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent hideLabel />}
            />
            <Pie
              data={sortedData}
              dataKey="count"
              nameKey="name"
              innerRadius={60}
              strokeWidth={5}
            >
              {sortedData.map((entry, index) => (
                <Cell key={`cell-${entry.id}`} fill={dynamicColors[index]} />
              ))}
              <Label
                content={({ viewBox }) => {
                  if (viewBox && 'cx' in viewBox && 'cy' in viewBox) {
                    return (
                      <text
                        x={viewBox.cx}
                        y={viewBox.cy}
                        textAnchor="middle"
                        dominantBaseline="middle"
                      >
                        <tspan
                          x={viewBox.cx}
                          y={viewBox.cy}
                          className="fill-foreground text-3xl font-bold"
                        >
                          {totalUserClaims.toLocaleString()}
                        </tspan>
                        <tspan
                          x={viewBox.cx}
                          y={(viewBox.cy || 0) + 24}
                          className="fill-muted-foreground"
                        >
                          Datapoints
                        </tspan>
                      </text>
                    );
                  }
                }}
              />
            </Pie>
          </PieChart>
        </ChartContainer>
      </CardContent>
      {/* <CardFooter className="flex-col gap-2 text-sm">
        <div className="flex items-center gap-2 font-medium leading-none">
          Trending up by 5.2% this month <TrendingUp className="h-4 w-4" />
        </div>
        <div className="leading-none text-muted-foreground">
          Showing total visitors for the last 6 months
        </div>
      </CardFooter> */}
    </Card>
  );
}
