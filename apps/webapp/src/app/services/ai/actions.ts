import { causalInferenceActions } from './causalInferenceAgent/actions';
import { quantitativeActions } from './quantitativeAgent/actions';

export const allActions = {
  ...causalInferenceActions,
  ...quantitativeActions,
};
