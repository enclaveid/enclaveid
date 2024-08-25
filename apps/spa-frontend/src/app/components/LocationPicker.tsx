import { useState, useMemo } from 'react';
import Select from 'react-select';
import countryList from 'react-select-country-list';
import Flag from 'react-world-flags';

const customStyles = {
  control: (provided) => ({
    ...provided,
    //backgroundColor: '#f8f9fa',
    borderColor: '#e2e8f0',
    borderRadius: '0.375rem',
    padding: '0.5rem',
    boxShadow: 'none',
    '&:hover': {
      borderColor: '#e2e8f0',
    },
  }),
  placeholder: (provided) => ({
    ...provided,
    color: '#a0aec0',
  }),
  singleValue: (provided) => ({
    ...provided,
    color: '#4a5568',
  }),
  option: (provided, state) => ({
    ...provided,
    backgroundColor: state.isSelected ? '#e2e8f0' : 'white',
    color: '#4a5568',
    '&:hover': {
      backgroundColor: '#edf2f7',
    },
  }),
  dropdownIndicator: (provided) => ({
    ...provided,
    color: '#a0aec0',
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
