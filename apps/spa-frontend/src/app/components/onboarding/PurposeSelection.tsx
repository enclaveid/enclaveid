import { useEffect, useState } from 'react';
import { Button } from '../Button';

import RiOpenaiFill from '~icons/ri/openai-fill';
import LogosGoogleMaps from '~icons/logos/google-maps';
import LogosGoogleIcon from '~icons/logos/google-icon';
import SkillIconsInstagram from '~icons/skill-icons/instagram';
import LogosWhatsappIcon from '~icons/logos/whatsapp-icon';
import LogosMessenger from '~icons/logos/messenger';
import LogosFacebook from '~icons/logos/facebook';
import LogosYoutubeIcon from '~icons/logos/youtube-icon';
import SkillIconsGithubDark from '~icons/skill-icons/github-dark';
import LogosSpotifyIcon from '~icons/logos/spotify-icon';
import LogosGoogleCalendar from '~icons/logos/google-calendar';
import SkillIconsLinkedin from '~icons/skill-icons/linkedin';
import { backgroundPattern } from '../../utils/backgroundPattern';
import { useNavigate } from 'react-router-dom';
import { WarningModal } from '../WarningModal';

import { Purpose } from '@prisma/client';
import { fromCamelCase } from '../../utils/ui/fromCamelCase';

const iconsMap = {
  messaging: [LogosWhatsappIcon, LogosMessenger, LogosFacebook],
  social: [SkillIconsInstagram, LogosFacebook],
  search: [LogosGoogleIcon, RiOpenaiFill, LogosYoutubeIcon],
  calendar: [LogosGoogleCalendar],
  location: [LogosGoogleMaps],
  enterteinment: [LogosYoutubeIcon, LogosSpotifyIcon],
  productivity: [
    SkillIconsLinkedin,
    LogosGoogleCalendar,
    SkillIconsGithubDark,
    RiOpenaiFill,
  ],
};

const options = {
  [Purpose.AnalyzingMyself]: [
    ...iconsMap['messaging'],
    ...iconsMap['social'],
    ...iconsMap['search'],
  ],
  [Purpose.Dating]: [...iconsMap['messaging'], ...iconsMap['social']],
  [Purpose.FindingTravelBuddies]: [
    ...iconsMap['location'],
    ...iconsMap['social'],
  ],
  [Purpose.FindingRoomates]: [
    ...iconsMap['location'],
    ...iconsMap['enterteinment'],
  ],
  [Purpose.FindingProjectCollaborators]: [...iconsMap['productivity']],
  [Purpose.FormingAStudyGroup]: [
    ...iconsMap['productivity'],
    ...iconsMap['search'],
  ],
  [Purpose.MakingFriendsInANewCity]: [
    ...iconsMap['location'],
    ...iconsMap['social'],
    ...iconsMap['enterteinment'],
  ],
  [Purpose.FindingGymBuddies]: [
    ...iconsMap['location'],
    ...iconsMap['enterteinment'],
  ],
  [Purpose.FindingALanguageTeacher]: [...iconsMap['search']],
};

export function PurposeSelection() {
  const [selectedOptions, setSelectedOptions] = useState<Purpose[]>([
    Purpose.AnalyzingMyself,
    Purpose.Dating,
  ]);

  const [noSocial, setNoSocial] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if "Analyzing myself" is the only selected option
    setNoSocial(
      selectedOptions.length === 1 &&
        selectedOptions[0] === Purpose.AnalyzingMyself,
    );
  }, [selectedOptions]);

  return (
    <section
      className="min-h-screen onboarding-gradient flex items-center justify-center"
      style={{ ...backgroundPattern }}
    >
      <div className="flex flex-col gap-6 items-center">
        <h1 className="text-passiveLinkColor tracking-[0.02em] leading-[42px] font-medium text-4xl">
          How do you want to use EnclaveID?
        </h1>
        <div className="bg-white px-9 pt-8 pb-5 border border-[#E5E8EE] rounded-xl max-w-[597px] w-full flex flex-col gap-3">
          <h1 className="leading-[22px] text-passiveLinkColor">
            EnclaveID analyzes your data to give you personal insights as well
            as find similar people [...]
          </h1>

          <div className="h-72 overflow-y-auto border border-[#E5E8EE] rounded-xl p-3 bg-slate-100">
            <div className="grid grid-cols-3 gap-2">
              {Object.keys(options).map((option, index) => (
                <Button
                  label={fromCamelCase(option)}
                  variant={
                    selectedOptions.includes(option as Purpose)
                      ? 'primary'
                      : 'tertiary'
                  }
                  key={index}
                  size="small"
                  onClick={() =>
                    setSelectedOptions((prev) =>
                      prev.includes(option as Purpose)
                        ? prev.filter((item) => item !== (option as Purpose))
                        : [...prev, option as Purpose],
                    )
                  }
                />
              ))}
            </div>
          </div>
          <Button
            label={
              selectedOptions.length === Object.keys(options).length
                ? 'Deselect all'
                : 'Select all'
            }
            variant="secondary"
            onClick={() => {
              if (selectedOptions.length < Object.keys(options).length) {
                setSelectedOptions(
                  Object.keys(options).map((option) => option as Purpose),
                );
              } else {
                setSelectedOptions([]);
              }
            }}
            className="mb-5"
          />

          <div className="flex flex-row justify-between items-center px-5">
            <span className="text-passiveLinkColor text-md leading-5">
              Suggested data sources:
            </span>
            <div className="flex justify-end w-7/12">
              <div className="grid grid-cols-9 gap-2">
                {selectedOptions
                  .reduce((prev, option) => {
                    return Array.from(new Set([...prev, ...options[option]]));
                  }, [])
                  .map((Icon, index) => (
                    <Icon key={index} />
                  ))}
              </div>
            </div>
          </div>
          <WarningModal
            isOpen={isModalOpen}
            closeModal={() => setIsModalOpen(false)}
            title="Are you sure?"
            description="The best part of EnclaveID is discovering new people. You can also familiarize yourself with the solo features and revise this decision in your account settings at any other time."
            onConfirm={() => {
              // TODO: mutation
              navigate('/onboarding/questionnaire');
            }}
          />

          {selectedOptions.length > 0 &&
            (noSocial ? (
              <Button
                label="I do not want to connect anonymously with other similar users"
                variant="secondary"
                fullWidth
                className="mt-10 mb-10"
                onClick={() => setIsModalOpen(true)}
              />
            ) : (
              <Button
                label="Next"
                variant="primary"
                fullWidth
                className="mt-10 mb-10"
                onClick={() => {
                  navigate('/onboarding/questionnaire');
                }}
              />
            ))}
        </div>
      </div>
    </section>
  );
}
