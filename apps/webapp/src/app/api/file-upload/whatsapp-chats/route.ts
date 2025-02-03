import { NextRequest, NextResponse } from 'next/server';
import { azureContainerClient } from '../../../services/azure/storage';
import { apiAuth } from '../../../actions/auth/apiAuth';
import { parseWhatsappDesktopArchive } from '../../../services/parsing/parseWhatsappDesktopArchive';
import { prisma } from '../../../services/db/prisma';

export async function POST(req: NextRequest) {
  try {
    const user = await apiAuth(req);
    const phoneNumber = req.headers.get('X-Phone-Number');

    if (!phoneNumber || !req.body) {
      return NextResponse.json(
        { error: 'Phone number or file not provided' },
        { status: 400 }
      );
    }

    // Check if phone number belongs to user
    const userPhoneNumber = await prisma.phoneNumber.findFirst({
      where: {
        userId: user.id,
        number: phoneNumber,
        verifiedAt: { not: null },
      },
    });

    if (!userPhoneNumber) {
      return NextResponse.json(
        { error: 'Phone number does not belong to user or is not verified' },
        { status: 400 }
      );
    }

    const parsedBuffer = await req
      .arrayBuffer()
      .then((fileData) => parseWhatsappDesktopArchive(fileData, phoneNumber));

    // Create blob name using user ID
    const blobName = `/api/${user.id}/whatsapp_desktop/latest.json`;

    // Get blob client and upload file
    const blockBlobClient = azureContainerClient.getBlockBlobClient(blobName);

    await blockBlobClient.upload(parsedBuffer, parsedBuffer.byteLength, {
      blobHTTPHeaders: {
        blobContentType: 'application/json',
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
