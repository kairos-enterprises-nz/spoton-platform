import { useState } from 'react';
import PropTypes from 'prop-types';
import { AlertCircle, CheckCircle, Info, BellOff, ChevronRight } from "lucide-react";

const mockNotifications = [
  {
    id: 1,
    type: "alert",
    message: "Unusually high power consumption detected yesterday",
    time: "2 hours ago",
  },
  {
    id: 2,
    type: "info",
    message: "Broadband speed test completed",
    time: "Yesterday",
  },
  {
    id: 3,
    type: "success",
    message: "Bill payment confirmed",
    time: "3 days ago",
  },
  {
    id: 4,
    type: "alert",
    message: "Payment for Jun 3, 2025 is due soon.",
    time: "1 day ago",
  },
  {
    id: 5,
    type: "info",
    message: "Your water usage report is available",
    time: "Just now",
  }
];

export default function NotificationsPanel({ notifications: propNotifications, maxVisible = 5 }) {
  const [notifications, setNotifications] = useState(propNotifications || mockNotifications);

  // Helper function to get notification icon based on type
  const getNotificationIcon = (type) => {
    switch (type) {
      case "alert":
        return <AlertCircle size={16} />;
      case "info":
        return <Info size={16} />;
      case "success":
        return <CheckCircle size={16} />;
      default:
        return <Info size={16} />;
    }
  };

  // Helper function to get notification background and text colors
  const getNotificationColors = (type) => {
    switch (type) {
      case "alert":
        return "bg-red-50 text-[#b14e4e]";
      case "info":
        return "bg-blue-50 text-[#4e80b1]";
      case "success":
        return "bg-green-50 text-[#4eb14e]";
      default:
        return "bg-gray-100 text-[#364153]";
    }
  };

  // Function to dismiss a notification
  const dismissNotification = (id, e) => {
    e.stopPropagation();
    setNotifications(notifications.filter(notification => notification.id !== id));
  };

  // Function to dismiss all notifications
  const dismissAllNotifications = () => {
    setNotifications([]);
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-3 sm:p-6 hover:shadow-lg transition-all duration-300 group relative">
      <div className="flex justify-between items-center mb-3 sm:mb-4">
        <h2 className="font-bold text-lg text-[#364153] flex items-center">
          <span className="w-2 h-2 bg-[#b14e4e] rounded-full mr-2"></span>
          Notifications
        </h2>
        <div className="flex items-center gap-2">
          <span className="bg-[#b14e4e]/10 text-[#b14e4e] text-xs px-2.5 py-1 rounded-full font-medium">
            {notifications.length} {notifications.length === 1 ? 'new' : 'new'}
          </span>
          {notifications.length > 0 && (
            <button 
              onClick={dismissAllNotifications}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-gray-400 hover:bg-[#b14e4e]/10 hover:text-[#b14e4e] transition-colors duration-300 focus:outline-none"
              title="Dismiss all notifications"
            >
              <BellOff size={16} />
              <span className="text-xs font-medium">Clear All</span>
            </button>
          )}
        </div>
      </div>
      
      {notifications.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-gray-400">
          <BellOff size={24} className="mb-2" />
          <p className="text-sm">No notifications</p>
        </div>
      ) : (
        <div className="space-y-2 sm:space-y-3 max-h-[400px] overflow-hidden relative">
          <div className="flex flex-col gap-2 sm:gap-3">
            {notifications.slice(0, maxVisible).map((notification) => (
              <div 
                key={notification.id} 
                className="group/item bg-gray-50 rounded-lg overflow-hidden transition-all duration-300 hover:shadow-md relative"
              >
                <div className="flex items-start p-2 sm:p-3">
                  <div className={`p-1.5 sm:p-2 rounded-full mr-2 sm:mr-3 ${getNotificationColors(notification.type)}`}>
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className="flex-1 pr-8">
                    <p className="text-xs sm:text-sm text-[#364153] font-medium">{notification.message}</p>
                    <p className="text-xs text-gray-500 mt-0.5 sm:mt-1">{notification.time}</p>
                  </div>
                  
                  <div className="absolute right-0 top-0 h-full transform translate-x-full group-hover/item:translate-x-0 transition-transform duration-300 ease-in-out flex items-center">
                    <button 
                      className="h-full px-4 bg-gradient-to-l from-[#b14e4e] to-[#b14e4e]/90 text-white opacity-90 hover:opacity-100 transition-all duration-300 flex items-center gap-2"
                      onClick={(e) => dismissNotification(notification.id, e)}
                    >
                      <BellOff size={14} />
                      <span className="text-xs font-medium whitespace-nowrap">Dismiss</span>
                    </button>
                  </div>

                  <div className="absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-[#b14e4e]/10 to-transparent opacity-0 group-hover/item:opacity-100 transition-opacity duration-300"></div>
                </div>
              </div>
            ))}
          </div>
          
          {notifications.length > maxVisible && (
            <div className="mt-2 text-center">
              <button 
                className="text-xs text-[#40E0D0] hover:text-[#40E0D0]/80 transition-colors duration-300 font-medium flex items-center mx-auto"
              >
                View {notifications.length - maxVisible} more notifications
                <ChevronRight size={12} className="ml-1 rotate-90" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

NotificationsPanel.propTypes = {
  notifications: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.number.isRequired,
    type: PropTypes.oneOf(['alert', 'info', 'success']).isRequired,
    message: PropTypes.string.isRequired,
    time: PropTypes.string.isRequired
  })),
  maxVisible: PropTypes.number
}; 