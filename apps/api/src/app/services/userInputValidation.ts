import {
  RegExpMatcher,
  englishDataset,
  englishRecommendedTransformers,
} from 'obscenity';
import { isDisposableEmail } from 'disposable-email-domains-js';
import { validate } from 'email-validator';

const matcher = new RegExpMatcher({
  ...englishDataset.build(),
  ...englishRecommendedTransformers,
});

export function checkProfanity(text: string) {
  return matcher.hasMatch(text);
}

export function checkEmail(email: string) {
  return validate(email) && !isDisposableEmail(email);
}
