import PropTypes from 'prop-types';
import { FileX } from 'lucide-react';

export default function EmptyState({ 
  icon: Icon = FileX, 
  title = "No data available", 
  description = "There's nothing to show here yet.",
  actionText,
  onAction
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 mb-4 max-w-sm">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="bg-[#40E0D0] hover:bg-[#40E0D0]/80 text-[#364153] font-medium py-2 px-4 rounded-lg transition-all duration-300"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}

EmptyState.propTypes = {
  icon: PropTypes.elementType,
  title: PropTypes.string,
  description: PropTypes.string,
  actionText: PropTypes.string,
  onAction: PropTypes.func
}; 