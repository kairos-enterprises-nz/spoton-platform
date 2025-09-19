import PropTypes from 'prop-types';
import { Calendar, AlertCircle, Activity, Settings, ChevronRight } from "lucide-react";

const defaultActions = [
  {
    id: 'pay-bill',
    label: 'Pay Bill',
    icon: Calendar,
    href: '/billing'
  },
  {
    id: 'report-issue',
    label: 'Report Issue',
    icon: AlertCircle,
    href: '/support'
  },
  {
    id: 'usage-history',
    label: 'Usage History',
    icon: Activity,
    href: '/power'
  },
  {
    id: 'account-settings',
    label: 'Account Settings',
    icon: Settings,
    href: '/profile'
  }
];

export default function QuickActions({ actions, title = "Quick Actions" }) {
  const actionsToRender = actions || defaultActions;

  return (
    <div className="bg-white rounded-xl shadow-md p-3 sm:p-6 hover:shadow-lg transition-all duration-300">
      <h2 className="font-bold text-lg text-[#364153] mb-3 sm:mb-4 flex items-center">
        <span className="w-2 h-2 bg-[#40E0D0] rounded-full mr-2"></span>
        {title}
      </h2>
      <div className="space-y-1.5 sm:space-y-2">
        {actionsToRender.map((action) => (
          <a
            key={action.id}
            href={action.href}
            className="w-full flex items-center justify-between p-2 sm:p-3 bg-gray-50 hover:bg-[#40E0D0]/10 rounded-lg transition-all duration-300 group no-underline"
          >
            <span className="font-medium text-[#364153] group-hover:text-[#40E0D0] flex items-center text-sm">
              <action.icon size={14} className="mr-1.5 text-gray-400 group-hover:text-[#40E0D0]" />
              {action.label}
            </span>
            <ChevronRight size={14} className="text-gray-400 group-hover:text-[#40E0D0] transition-transform group-hover:translate-x-1" />
          </a>
        ))}
      </div>
    </div>
  );
}

QuickActions.propTypes = {
  actions: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    icon: PropTypes.elementType.isRequired,
    href: PropTypes.string.isRequired
  })),
  title: PropTypes.string
}; 