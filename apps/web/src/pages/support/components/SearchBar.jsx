import { useState } from 'react';
import { SearchIcon } from 'lucide-react';

export default function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');

  const handleInput = (e) => {
    const value = e.target.value;
    setQuery(value);
    if (onSearch) {
      onSearch(value);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-xl mx-auto mt-8">
      <label htmlFor="help-search" className="sr-only">
        Search help topics
      </label>
      <input
        id="help-search"
        type="text"
        value={query}
        onChange={handleInput}
        placeholder="Search for topics, FAQs, or help..."
        className="w-full rounded-md border border-gray-300 px-4 py-3 pr-10 text-gray-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-turquoise"
      />
      <button type="submit" className="absolute right-3 top-3.5 text-gray-400 hover:text-primary-turquoise">
        <SearchIcon className="h-5 w-5" />
      </button>
    </form>
  );
}
