import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '../../../services/db/prisma';
import { z } from 'zod';
import { apiAuth } from '../../../actions/auth/apiAuth';

// Update input validation schema
const MessageCountDataSchema = z.object({
  phone_number: z.string(),
  message_count: z.number(),
});

const InputSchema = z.record(z.string(), MessageCountDataSchema);

export async function POST(req: NextRequest) {
  try {
    const user = await apiAuth(req);
    // Parse and validate request body
    const body = await req.json();
    const validatedData = InputSchema.parse(body);

    // Transform the data structure for database insertion
    const messagingPartners = Object.entries(validatedData).map(
      ([name, data]) => ({
        name,
        phoneNumber: data.phone_number,
        numberOfMessages: data.message_count,
        userId: user.id,
      })
    );

    // Create messaging partners
    const createdPartners = await prisma.messagingPartner.createMany({
      data: messagingPartners,
      skipDuplicates: true,
    });

    return NextResponse.json({
      message: 'Messaging partners created successfully',
      count: createdPartners.count,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid input data', details: error.errors },
        { status: 400 }
      );
    }
    console.error('Error creating messaging partners:', error);
    return NextResponse.json(
      { error: 'Internal server error: ' + error },
      { status: 500 }
    );
  }
}
