import { describe, expect, it } from 'bun:test';
import { getPressureMessage } from './feedbackMessages';

describe('getPressureMessage', () => {
  it('should return a message', () => {
    const message = getPressureMessage();
    console.log(message);
    expect(message).toBeDefined();
  });
});
