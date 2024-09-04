import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Button } from '../atoms/Button';
import { Logo } from '../atoms/Logo';
import { CheckmarkIcon } from '../atoms/Icons';
import { Questionnaire } from '@enclaveid/shared';
import { useTypewriterEffect } from '../../hooks/useTypewriterEffect';

type Steps = 'onboarding' | 'steps' | 'final';

export interface StepFormProps {
  onSkip?: () => void;
  onFinished?: (answers: StepFormAnswers) => void;
  questionnaire?: Questionnaire;
}

type StepFormAnswers = Record<string, string>;

export function StepForm(props: StepFormProps) {
  const { onSkip, onFinished, questionnaire } = props;

  const { title, parts } = questionnaire;

  const [currentPart, setCurrentPart] = useState(0);
  const { questions, options, headline } = parts[currentPart];
  const totalQuestions = parts.reduce(
    (acc, part) => acc + part.questions.length,
    0,
  );
  const [progress, setProgress] = useState(1);

  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<StepFormAnswers>({});
  const [steps, setSteps] = useState<Steps>('onboarding');

  const handleSelectOption = (option: string, statement: string) => {
    setAnswers((prev) => ({ ...prev, [statement]: option }));
    setProgress((prev) => prev + 1);

    if (currentStep < questions.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else if (currentPart < parts.length - 1) {
      setCurrentPart((prev) => prev + 1);
      setCurrentStep(0);
    } else {
      setSteps('final');
    }
  };

  useEffect(() => {
    if (steps === 'final' && onFinished) {
      setSteps('onboarding');
      onFinished(answers);
    }
  }, [steps, answers, onFinished]);

  const currentQuestion = questions[currentStep];

  const typewriterText = useTypewriterEffect(currentQuestion);

  useEffect(() => {
    // Reset the state when the questionnaire changes
    setCurrentPart(0);
    setCurrentStep(0);
    setProgress(1);
    setAnswers({});
    setSteps('onboarding');
  }, [questionnaire]);

  if (steps === 'onboarding') {
    return (
      <div className="flex flex-col gap-9 max-w-[478px]">
        <h2 className="text-passiveLinkColor font-medium text-4xl leading-[42px] -tracking-[0.02em] text-center">
          {title}
        </h2>
        <div className="bg-white border border-[#E5E8EE] px-[29px] pt-[42px] pb-5 rounded-xl">
          <p className="text-passiveLinkColor leading-[22px]">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce eget
            condimentum augue. Aenean elementum commodo varius.
            <br />
            <br />
            It takes <span className="font-bold">around 3 minutes</span> and
            will{' '}
            <span className="font-bold">
              make your results much more interesting.
            </span>
          </p>
          <div className="mt-8 flex flex-col gap-4 items-center">
            <Button
              label="Take the test"
              onClick={() => setSteps('steps')}
              fullWidth
            />
            <Button
              variant="secondary"
              label="I'll do it later"
              onClick={() => {
                console.log('skipping');
                onSkip();
              }}
              fullWidth
            />
          </div>
        </div>
      </div>
    );
  }

  if (steps === 'final') {
    return (
      <div className="flex flex-col gap-14 items-center max-w-[478px] w-full mx-auto">
        <Logo />
        <div className="bg-white border border-[#E5E8EE] py-10 rounded-xl flex flex-col items-center gap-6 w-full">
          <div
            className="w-[90px] h-[90px] rounded-full bg-[#EAF9F6] flex items-center justify-center"
            style={{
              boxShadow:
                '0px 0.717742px 1.43548px rgba(0, 0, 0, 0.06), 0px 0.717742px 2.15323px rgba(0, 0, 0, 0.1)',
            }}
          >
            <CheckmarkIcon />
          </div>
          <h3 className="text-center text-passiveLinkColor text-2xl leading-[34px] -tracking-[0.02em] font-medium">
            Thanks for taking the test!
          </h3>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[567px] w-full mx-auto">
      <AnimatePresence mode="wait">
        <div className="flex flex-col gap-2.5">
          <div className="flex flex-col gap-[21px]">
            <h2 className="text-passiveLinkColor font-medium text-2xl leading-7 -tracking-[0.02em] text-center">
              {title}
            </h2>
            <p className="text-passiveLinkColor leading-[22px] text-center whitespace-pre-wrap">
              {`${headline}\n(${progress} out of ${totalQuestions})`}
            </p>
          </div>

          {currentQuestion && (
            <div className="bg-white border border-[#E5E8EE] py-10 rounded-xl">
              <div className="flex flex-col gap-10 max-w-[406px] w-full mx-auto">
                <h4 className="text-center text-passiveLinkColor text-lg leading-[25px min-h-10">
                  {typewriterText}
                </h4>
                <motion.div
                  key={questions.indexOf(currentQuestion)}
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                  transition={{
                    type: 'spring',
                    stiffness: 100,
                    damping: 30,
                    duration: 3,
                  }}
                >
                  <div className="flex flex-col gap-3 max-w-[406px] w-full mx-auto">
                    {options.map((option, index) => (
                      <button
                        key={index}
                        style={{
                          boxShadow:
                            '0px 1px 2px rgba(0, 0, 0, 0.06), 0px 1px 3px rgba(0, 0, 0, 0.1)',
                        }}
                        className={`bg-white pt-[13px] pb-3 text-passiveLinkColor leading-5 text-center hover:bg-[#EAF9F6] transition-colors rounded-md focus:outline focus:outline-greenBg`}
                        onClick={() =>
                          handleSelectOption(option, currentQuestion)
                        }
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </motion.div>
              </div>
            </div>
          )}
        </div>
      </AnimatePresence>
    </div>
  );
}
