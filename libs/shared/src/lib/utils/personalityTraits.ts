import {
  MbtiPartial,
  PoliticalCompassPartial,
} from '../constants/partialTypes';

export function mbtiToString(mbti: MbtiPartial): string {
  const e = mbti.extraversion ? 'E' : 'I';
  const s = mbti.sensing ? 'S' : 'N';
  const t = mbti.thinking ? 'T' : 'F';
  const j = mbti.judging ? 'J' : 'P';

  return `${e}${s}${t}${j}`;
}

export function politicalCompassToString(
  politicalCompass: PoliticalCompassPartial,
): string {
  const { economic, social } = politicalCompass;

  const socialLabel = social > 0 ? 'Authoritarian' : 'Libertarian';
  const economicLabel =
    economic == 0 ? 'Center' : economic > 0 ? 'Right' : 'Left';

  return `${socialLabel} ${economicLabel}`;
}
