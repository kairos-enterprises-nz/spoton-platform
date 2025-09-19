# Dashboard Components

This directory contains all the componentized dashboard components organized by page/feature for better maintainability.

## Structure

```
dashboard/
├── home/                    # Home/Dashboard page components
│   ├── WelcomeBanner.jsx   # Welcome banner with user greeting
│   ├── StatsOverview.jsx   # Overview stats cards
│   ├── PowerUsageChart.jsx # Power usage chart component
│   ├── BroadbandStatus.jsx # Broadband status panel
│   ├── NotificationsPanel.jsx # Notifications component
│   ├── QuickActions.jsx    # Quick actions panel
│   └── index.js           # Export all home components
├── power/                  # Power page components
│   ├── ConnectionsSection.jsx # Power connections management
│   ├── UsageChart.jsx      # Power usage charts
│   └── index.js           # Export all power components
├── broadband/             # Broadband page components
│   ├── ServiceStatusBanner.jsx # Service status banner
│   ├── CurrentPlanCard.jsx # Current plan information
│   ├── SpeedTestCard.jsx   # Speed test functionality
│   └── index.js           # Export all broadband components
├── mobile/                # Mobile page components
│   ├── NetworkStatusBanner.jsx # Network status banner
│   ├── MobilePlanCard.jsx  # Mobile plan information
│   └── index.js           # Export all mobile components
├── billing/               # Billing page components
│   ├── CurrentBalanceCard.jsx # Current balance display
│   ├── RecentTransactions.jsx # Recent transactions list
│   └── index.js           # Export all billing components
├── profile/               # Profile page components
│   ├── ProfileHeader.jsx   # Profile header with user info
│   └── index.js           # Export all profile components
├── shared/                # Shared/common components
│   ├── LoadingSpinner.jsx  # Loading spinner component
│   ├── EmptyState.jsx      # Empty state component
│   └── index.js           # Export all shared components
└── index.js               # Main export file for all components
```

## Usage

### Import specific components:
```jsx
import { WelcomeBanner, StatsOverview } from '@/components/dashboard/home';
import { ConnectionsSection } from '@/components/dashboard/power';
```

### Import from main index:
```jsx
import { 
  WelcomeBanner, 
  StatsOverview, 
  ConnectionsSection,
  LoadingSpinner 
} from '@/components/dashboard';
```

## Component Features

### All components include:
- **PropTypes validation** for type safety
- **Default props/data** for standalone usage
- **Responsive design** with mobile-first approach
- **Hover effects** and smooth transitions
- **Accessibility features** where applicable
- **Consistent styling** using Tailwind CSS

### Color Scheme:
- Primary: `#40E0D0` (Turquoise)
- Secondary: `#364153` (Dark Blue-Gray)
- Power: `#40E0D0` (Turquoise)
- Broadband: `#b14eb1` (Purple)
- Mobile: `#4e80b1` (Blue)
- Billing: `#40E0D0` (Turquoise)

## Best Practices

1. **Component Isolation**: Each component is self-contained with its own props and default data
2. **Reusability**: Components can be used across different pages with different data
3. **Maintainability**: Clear separation of concerns and organized file structure
4. **Performance**: Components use React best practices for optimal rendering
5. **Accessibility**: Semantic HTML and ARIA attributes where needed

## Adding New Components

1. Create the component file in the appropriate folder
2. Add PropTypes validation
3. Include default props/data
4. Export from the folder's index.js
5. Update this README if needed 