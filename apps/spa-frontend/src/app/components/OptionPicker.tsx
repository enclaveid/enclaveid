import { useState } from 'react';

export function OptionPicker({
  options,
  label,
  onChange,
  defaultSelected = null,
}) {
  const [selectedOption, setSelectedOption] = useState(defaultSelected);

  const handleOptionSelect = (option) => {
    setSelectedOption(option);
    onChange(option);
  };

  return (
    <div className="flex flex-col space-y-2 w-full">
      <div className="flex space-x-2 w-full">
        {options.map((option) => (
          <button
            key={option}
            onClick={() => handleOptionSelect(option)}
            className={`px-6 py-2 rounded-md text-sm transition-colors duration-200 w-full ${
              selectedOption === option
                ? 'bg-greenBg text-white font-medium'
                : 'bg-white text-gray-400 border border-[#E5E8EE]  hover:bg-gray-100'
            }`}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}
