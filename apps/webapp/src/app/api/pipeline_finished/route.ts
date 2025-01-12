import { NextRequest, NextResponse } from 'next/server';
import { loadPipelineResults } from '../../services/azure/loadPipelineResult';
import { readParquet } from '../../services/readParquet';
import { DataframeRow, saveDataframe } from '../../services/db/saveDataframe';

export async function POST(request: NextRequest) {
  try {
    const { userId } = await request.json();

    if (!userId) {
      return NextResponse.json(
        { error: 'userId is required' },
        { status: 400 }
      );
    }

    const blobName = `${userId}.snappy`;
    const parquetData = await loadPipelineResults(blobName).then((data) => {
      return readParquet(data);
    });

    await saveDataframe(userId, parquetData as DataframeRow[]);

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error: ' + error },
      { status: 500 }
    );
  }
}
