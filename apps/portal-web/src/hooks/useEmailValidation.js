import { useState, useEffect } from 'react';
import { useDebounce } from './useDebounce'; // Adjust path as needed
import { checkEmailExists } from '../services/verificationService'; // Adjust path as needed

export function useEmailValidation(email, delay = 2500) {
  const [status, setStatus] = useState(''); // '', 'checking', 'not_found', 'inactive', 'invalid', 'valid'
  const debouncedEmail = useDebounce(email, delay);

  useEffect(() => {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!debouncedEmail || !emailPattern.test(debouncedEmail)) {
      setStatus('');
      return;
    }

    const check = async () => {
      setStatus('checking');
      try {
        const result = await checkEmailExists(debouncedEmail);
        if (result.error) {
          setStatus('invalid');
        } else if (!result.exists) {
          setStatus('not_found');
        } else if (!result.active) {
          setStatus('inactive');
        } else {
          setStatus('valid');
        }
      } catch {
        setStatus('invalid');
      }
    };

    check();
  }, [debouncedEmail]);

  return { status };
}
