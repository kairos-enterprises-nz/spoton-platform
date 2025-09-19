import { Link } from 'react-router-dom';

export default function BreadcrumbNav({ path = [] }) {
  if (!path.length) return null;

  return (
    <nav
      className="text-base font-bold text-gray-300 mt-6"
      aria-label="Breadcrumb"
    >
      <ol className="inline-flex items-center justify-center space-x-1">
        {path.map((item, index) => (
          <li key={index} className="inline-flex items-center">
            {item.to ? (
              <Link to={item.to} className="hover:underline text-primary-turquoise">
                {item.label}
              </Link>
            ) : (
              <span className="text-gray-300">{item.label}</span>
            )}
            {index < path.length - 1 && (
              <span className="mx-1 text-gray-400">/</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
} 