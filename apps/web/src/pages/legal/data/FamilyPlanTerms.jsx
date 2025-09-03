import {
  Phone,
  CreditCard,
  Clock,
  AlertTriangle,
  RefreshCcw,
  Shield,
  Users,
  Wifi,
} from "lucide-react";

export const familyPlanTerms = [
  {
    id: "overview",
    number: 1,
    title: "Plan Overview",
    icon: <Users className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Family plans allow multiple lines to share data and minutes under a single account. Each line can have its own device and number."
      }
    ]
  },
  {
    id: "billing",
    number: 2,
    title: "Billing & Payments",
    icon: <CreditCard className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Single monthly bill for all lines",
          "Primary account holder responsible for all charges",
          "Individual line charges itemized on bill",
          "Shared data pool for all lines"
        ]
      }
    ]
  },
  {
    id: "data-sharing",
    number: 3,
    title: "Data Sharing",
    icon: <Wifi className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Data is shared across all lines in the family plan. Individual data limits can be set for each line to prevent excessive usage."
      }
    ]
  },
  {
    id: "line-management",
    number: 4,
    title: "Line Management",
    icon: <Phone className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Up to 5 lines per family plan",
          "Each line can have different devices",
          "Individual line settings and restrictions available",
          "Line transfers between accounts not permitted"
        ]
      }
    ]
  },
  {
    id: "fair-use",
    number: 5,
    title: "Fair Use Policy",
    icon: <Shield className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Family plans are subject to fair use policies to prevent network abuse and ensure quality service for all customers."
      }
    ]
  },
  {
    id: "changes",
    number: 6,
    title: "Plan Changes",
    icon: <RefreshCcw className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Changes to shared data pool require 30 days notice",
          "Individual line changes can be made immediately",
          "Adding/removing lines may affect monthly charges",
          "Plan changes may reset billing cycle"
        ]
      }
    ]
  },
  {
    id: "roaming",
    number: 7,
    title: "International Roaming",
    icon: <Clock className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Available for all lines in family plan",
          "Individual activation required per line",
          "Shared data pool not available while roaming",
          "Separate roaming charges per line"
        ]
      }
    ]
  },
  {
    id: "emergency",
    number: 8,
    title: "Emergency Services",
    icon: <AlertTriangle className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Emergency calls (111) are free and available on all lines, even if the account is suspended or data limits are exceeded."
      }
    ]
  }
]; 