import { useNavigate } from 'react-router-dom';
import { StepForm } from '../../components/onboarding/StepForm';
import { QuestionnaireContainer } from '../../components/containers/QuestionnaireContainer';
import { RequireAuth } from '../../providers/AuthProvider';

export function QuestionnairePage() {
  const navigate = useNavigate();

  return (
    <RequireAuth>
      <div className="h-screen flex items-center justify-center bg-[#F3F5F7]">
        <QuestionnaireContainer
          onSkipAll={() => {
            navigate('/dashboard/personality');
          }}
        >
          <StepForm />
        </QuestionnaireContainer>
      </div>
    </RequireAuth>
  );
}
