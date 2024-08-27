import { StepForm } from '../../components/onboarding/StepForm';
import { QuestionnaireContainer } from '../../components/containers/QuestionnaireContainer';
import { backgroundPattern } from '../../utils/backgroundPattern';

export function QuestionnairePage() {
  return (
    <div
      className="h-screen flex items-center justify-center"
      style={backgroundPattern}
    >
      <QuestionnaireContainer>
        <StepForm />
      </QuestionnaireContainer>
    </div>
  );
}
