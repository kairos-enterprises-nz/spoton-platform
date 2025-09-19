import React from 'react';
import PropTypes from 'prop-types';

const SkipLink = ({ 
  href = '#main-content',
  children = 'Skip to main content',
  className = ''
}) => {
  return (
    <a
      href={href}
      className={`
        sr-only focus:not-sr-only
        fixed top-4 left-4 z-[1600]
        bg-primary-turquoise-600 text-white
        px-4 py-2 rounded-md
        font-medium text-sm
        focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-turquoise-600
        transition-all duration-200
        ${className}
      `}
      onFocus={(e) => {
        // Ensure the skip link is visible when focused
        e.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }}
    >
      {children}
    </a>
  );
};

// Multiple skip links for complex layouts
const SkipLinks = ({ links = [], className = '' }) => {
  const defaultLinks = [
    { href: '#main-content', text: 'Skip to main content' },
    { href: '#navigation', text: 'Skip to navigation' },
    { href: '#footer', text: 'Skip to footer' }
  ];

  const skipLinks = links.length > 0 ? links : defaultLinks;

  return (
    <div className={`sr-only focus-within:not-sr-only ${className}`}>
      <nav aria-label="Skip links" className="fixed top-4 left-4 z-[1600] space-y-2">
        {skipLinks.map((link, index) => (
          <SkipLink
            key={index}
            href={link.href}
            className="block"
          >
            {link.text}
          </SkipLink>
        ))}
      </nav>
    </div>
  );
};

SkipLink.propTypes = {
  href: PropTypes.string,
  children: PropTypes.node,
  className: PropTypes.string
};

SkipLinks.propTypes = {
  links: PropTypes.arrayOf(PropTypes.shape({
    href: PropTypes.string.isRequired,
    text: PropTypes.string.isRequired
  })),
  className: PropTypes.string
};

export { SkipLinks };
export default SkipLink;
