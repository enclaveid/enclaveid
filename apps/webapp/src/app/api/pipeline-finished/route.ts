import { NextRequest, NextResponse } from 'next/server';
import { loadPipelineResults } from '../../services/azure/loadPipelineResult';
import { readParquet } from '../../services/readParquet';
import { saveDataframes } from '../../services/db/saveDataframes';

export async function POST(request: NextRequest) {
  try {
    const { initiatorPhoneNumber, partnerPhoneNumber } = await request.json();

    if (!initiatorPhoneNumber || !partnerPhoneNumber) {
      return NextResponse.json(
        { error: 'initiatorPhoneNumber and partnerPhoneNumber are required' },
        { status: 400 }
      );
    }

    const blobNames = [
      `/dagster/whatsapp_out_chunks/${initiatorPhoneNumber}/${partnerPhoneNumber}.snappy`,
      `/dagster/whatsapp_out_nodes/${initiatorPhoneNumber}/${partnerPhoneNumber}.snappy`,
    ];

    const [outChunks, outNodes] = await Promise.all(
      blobNames.map(async (blobName) => {
        const data = await loadPipelineResults(blobName);
        return await readParquet(data);
      })
    );

    await saveDataframes(
      [initiatorPhoneNumber, partnerPhoneNumber],
      outChunks,
      outNodes
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error: ' + error },
      { status: 500 }
    );
  }
}
