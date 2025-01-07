import React from 'react';

interface SearchBoxProps {
  searchTerm: string;
  onSearchTermChange: (newTerm: string) => void;
}

export function SearchBox({ searchTerm, onSearchTermChange }: SearchBoxProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSearchTermChange(e.target.value);
  };

  return (
    <div
      style={{
        position: 'absolute',
        top: 20,
        left: 20,
        zIndex: 9999,
        padding: '8px',
        background: 'rgba(255, 255, 255, 0.8)',
        borderRadius: 4,
      }}
    >
      <input
        type="text"
        value={searchTerm}
        onChange={handleChange}
        placeholder="Search by label..."
        style={{ width: '200px' }}
      />
    </div>
  );
}
