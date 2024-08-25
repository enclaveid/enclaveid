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
  'Analyzing myself': [
    ...iconsMap['messaging'],
    ...iconsMap['social'],
    ...iconsMap['search'],
  ],
  Dating: [...iconsMap['messaging'], ...iconsMap['social']],
  'Finding travel buddies': [...iconsMap['location'], ...iconsMap['social']],
  'Finding roomates': [...iconsMap['location'], ...iconsMap['enterteinment']],
  'Finding project collaborators': [...iconsMap['productivity']],
  'Forming a study group': [...iconsMap['productivity'], ...iconsMap['search']],
  'Making friends in a new city': [
    ...iconsMap['location'],
    ...iconsMap['social'],
    ...iconsMap['enterteinment'],
  ],
  'Finding gym buddies': [
    ...iconsMap['location'],
    ...iconsMap['enterteinment'],
  ],
  'Finding a language teacher': [...iconsMap['search']],
};
export function PurposeSelection() {
  const [selectedOptions, setSelectedOptions] = useState<string[]>([
    'Analyzing myself',
    'Dating',
  ]);

  const [noSocial, setNoSocial] = useState(true);

  useEffect(() => {
    // Check if "Analyzing myself" is the only selected option
    setNoSocial(
      selectedOptions.length === 1 && selectedOptions[0] === 'Analyzing myself',
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
                  label={option}
                  variant={
                    selectedOptions.includes(option) ? 'primary' : 'tertiary'
                  }
                  key={index}
                  size="small"
                  onClick={() =>
                    setSelectedOptions((prev) =>
                      prev.includes(option)
                        ? prev.filter((item) => item !== option)
                        : [...prev, option],
                    )
                  }
                />
              ))}
            </div>
          </div>
          <Button
            label={
              selectedOptions.length == Object.keys(options).length
                ? 'Deselect all'
                : 'Select all'
            }
            variant="secondary"
            onClick={() => {
              if (selectedOptions.length < Object.keys(options).length) {
                setSelectedOptions(Object.keys(options));
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

          {selectedOptions.length > 0 &&
            (noSocial ? (
              <Button
                label="I do not want to connect anonymously with other similar users"
                variant="secondary"
                fullWidth
                className="mt-10 mb-10"
                //onClick={handleClick}
              />
            ) : (
              <Button
                label="Next"
                variant="primary"
                fullWidth
                className="mt-10 mb-10"
                //onClick={handleClick}
              />
            ))}
        </div>
      </div>
    </section>
  );
}
