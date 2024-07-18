import { toSvg } from 'jdenticon';

export function getIdenticon(uniqueId: string): string {
  const svgString = toSvg(uniqueId, 200);

  return (
    'data:image/svg+xml,' +
    encodeURIComponent(svgString).replace(/'/g, '%27').replace(/"/g, '%22')
  );
}
