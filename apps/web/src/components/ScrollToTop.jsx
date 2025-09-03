import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useLoader } from "../context/LoaderContext";

export default function ScrollToTop() {
  const { pathname, hash } = useLocation();
  const { setLoading } = useLoader();

  useEffect(() => {
    // If there is a hash, scroll to that element
    if (hash) {
      const targetElement = document.getElementById(hash.substring(1)); // Remove the '#' part
      if (targetElement) {
        const yOffset = -70;
        const y = targetElement.getBoundingClientRect().top + window.pageYOffset + yOffset;
        window.scrollTo({ top: y, behavior: 'smooth' });

        // Add visual focus (optional)
        targetElement.classList.add('ring', 'ring-primary-turquoise', 'ring-offset-2', 'rounded-md');
        setTimeout(() => {
          targetElement.classList.remove('ring', 'ring-primary-turquoise', 'ring-offset-2', 'rounded-md');
        }, 2000);
      }
    } else {
      // If there's no hash, scroll to the top
      window.scrollTo(0, 0);
    }

    // Ensure loading state is false after scroll
    setLoading(false);
  }, [pathname, hash, setLoading]);

  return null;
}
