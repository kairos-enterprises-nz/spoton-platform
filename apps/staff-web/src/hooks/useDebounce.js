// src/hooks/useDebounce.js (or your preferred hooks location)
import { useState, useEffect } from 'react';

export function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // Set up a timer to update the debounced value after the specified delay
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up the timer if the value changes (user is still typing)
    // or if the component unmounts
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]); // Re-run the effect if value or delay changes

  return debouncedValue;
}