export function getSentimentColor(sentiment: number): string {
  // Ensure sentiment is between -1 and 1
  const normalizedSentiment = Math.max(-1, Math.min(1, sentiment));

  // Convert to a 0-1 scale for interpolation
  const t = (normalizedSentiment + 1) / 2;

  const red = Math.round(255 - 175 * t);
  const green = Math.round(80 + 175 * t);
  const blue = 0;

  return `rgb(${red}, ${green}, ${blue})`;
}
