/**
 * Converts a camelCase string to a human readable string, keeping the case of the first letter.
 * @param str
 * @returns
 */
export function fromCamelCase(str: string) {
  if (!str) return str;

  return str
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .toLowerCase()
    .replace(/^./, (firstChar) => firstChar.toUpperCase());
}
