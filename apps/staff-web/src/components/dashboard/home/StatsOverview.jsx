import PropTypes from 'prop-types';
import { TrendingUp, Wifi, Zap, AlertCircle, Clock, Calendar } from "lucide-react";

const StatCard = ({ title, value, subtitle, icon: Icon, color, href, trend }) => (
  <a href={href} className={`bg-white rounded-xl shadow-md p-5 border-l-4 border-${color} hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 group no-underline`}>
    <div className="flex justify-between items-start">
      <div>
        <p className="text-gray-500 text-sm">{title}</p>
        <h3 className={`text-2xl font-bold mt-1 text-[#364153] group-hover:text-${color} transition-colors`}>{value}</h3>
        <p className={`text-sm flex items-center mt-1 ${trend?.type === 'positive' ? 'text-[#4eb14e]' : trend?.type === 'negative' ? 'text-[#b14e4e]' : 'text-gray-500'}`}>
          {trend?.icon && <trend.icon size={16} className="mr-1" />}
          {subtitle}
        </p>
      </div>
      <div className={`p-3 bg-gray-100 rounded-lg group-hover:bg-${color}/10 transition-all duration-300`}>
        <Icon size={24} className={`text-${color}`} />
      </div>
    </div>
  </a>
);

StatCard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  subtitle: PropTypes.string.isRequired,
  icon: PropTypes.elementType.isRequired,
  color: PropTypes.string.isRequired,
  href: PropTypes.string.isRequired,
  trend: PropTypes.shape({
    type: PropTypes.oneOf(['positive', 'negative', 'neutral']),
    icon: PropTypes.elementType
  })
};

export default function StatsOverview({ stats }) {
  const defaultStats = [
    {
      title: "Current Power Usage",
      value: "2.4 kWh",
      subtitle: "12% below average",
      icon: Zap,
      color: "[#40E0D0]",
      href: "/authenticated/power",
      trend: { type: 'positive', icon: TrendingUp }
    },
    {
      title: "Broadband Speed",
      value: "285 Mbps",
      subtitle: "Last tested 2h ago",
      icon: Wifi,
      color: "[#b14eb1]",
      href: "/authenticated/broadband",
      trend: { type: 'neutral', icon: Clock }
    },
    {
      title: "Next Bill Due",
      value: "Jun 3, 2025",
      subtitle: "13 days remaining",
      icon: AlertCircle,
      color: "[#b14e4e]",
      href: "/authenticated/billing",
      trend: { type: 'neutral', icon: Calendar }
    }
  ];

  const statsToRender = stats || defaultStats;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 sm:gap-4 mb-4 sm:mb-6">
      {statsToRender.map((stat, index) => (
        <StatCard key={index} {...stat} />
      ))}
    </div>
  );
}

StatsOverview.propTypes = {
  stats: PropTypes.arrayOf(PropTypes.shape({
    title: PropTypes.string.isRequired,
    value: PropTypes.string.isRequired,
    subtitle: PropTypes.string.isRequired,
    icon: PropTypes.elementType.isRequired,
    color: PropTypes.string.isRequired,
    href: PropTypes.string.isRequired,
    trend: PropTypes.shape({
      type: PropTypes.oneOf(['positive', 'negative', 'neutral']),
      icon: PropTypes.elementType
    })
  }))
}; 