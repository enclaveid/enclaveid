import { NextRequest, NextResponse } from 'next/server';
import { azureContainerClient } from '../../../services/azure/storage';
import { apiAuth } from '../../../actions/auth/apiAuth';

export async function POST(req: NextRequest) {
  try {
    const user = await apiAuth(req);

    // Check if request contains a file
    if (!req.body) {
      return NextResponse.json(
        { error: 'No file provided in request' },
        { status: 400 }
      );
    }

    // Get the file data as ArrayBuffer
    const fileData = await req.arrayBuffer();

    // Create blob name using user ID
    const blobName = `/api/${user.id}/whatsapp_desktop/latest.zip`;

    // Get blob client and upload file
    const blockBlobClient = azureContainerClient.getBlockBlobClient(blobName);

    await blockBlobClient.upload(fileData, fileData.byteLength, {
      blobHTTPHeaders: {
        blobContentType: 'application/zip',
      },
    });

    return NextResponse.json({
      message: 'File uploaded successfully',
      path: blobName,
    });
  } catch (error) {
    console.error('Error uploading file:', error);
    return NextResponse.json(
      { error: 'Internal server error: ' + error },
      { status: 500 }
    );
  }
}

// Increase payload size limit for file uploads
export const config = {
  api: {
    bodyParser: false,
    responseLimit: '50mb',
  },
};
