import { useState, useMemo } from 'react';
import Select from 'react-select';
import countryList from 'react-select-country-list';
import Flag from 'react-world-flags';

const customStyles = {
  option: (provided) => ({
    ...provided,
    display: 'flex',
    alignItems: 'center',
    padding: '8px 12px',
  }),
  singleValue: (provided) => ({
    ...provided,
    display: 'flex',
    alignItems: 'center',
  }),
};

function formatOptionLabel({ label, value }) {
  return (
    <div className="flex items-center">
      <div className="w-10 h-6 mr-2 flex-shrink-0 relative shadow-lg">
        <Flag
          code={value}
          fallback={<span className="text-xl">🏳</span>}
          className="absolute inset-0 w-full h-full object-cover rounded-sm"
        />
      </div>
      <span>{label}</span>
    </div>
  );
}

export function LocationPicker() {
  const [value, setValue] = useState<{ label: string; value: string }>();
  const options = useMemo(() => countryList().getData(), []);

  return (
    <Select
      options={options}
      styles={customStyles}
      value={value}
      onChange={(value) => setValue(value)}
      formatOptionLabel={formatOptionLabel}
      className="w-64"
      placeholder="Select your location..."
    />
  );
}
