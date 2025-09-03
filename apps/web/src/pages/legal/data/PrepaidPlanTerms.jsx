import {
  Phone,
  CreditCard,
  Clock,
  AlertTriangle,
  RefreshCcw,
  Shield,
} from "lucide-react";

export const prepaidPlanTerms = [
  {
    id: "overview",
    number: 1,
    title: "Plan Overview",
    icon: <Phone className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Prepaid plans offer pay-as-you-go mobile services with no lock-in contracts. Credit must be purchased in advance."
      }
    ]
  },
  {
    id: "credit",
    number: 2,
    title: "Credit & Validity",
    icon: <CreditCard className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Credit expires after 12 months from purchase",
          "Minimum top-up amount is $10",
          "Unused credit is forfeited upon expiration"
        ]
      }
    ]
  },
  {
    id: "data-packs",
    number: 3,
    title: "Data Packs",
    icon: <RefreshCcw className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Data packs can be purchased separately and have their own validity periods. Unused data expires at the end of the pack period."
      }
    ]
  },
  {
    id: "fair-use",
    number: 4,
    title: "Fair Use Policy",
    icon: <Shield className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Prepaid services are subject to fair use policies to prevent network abuse and ensure quality service for all customers."
      }
    ]
  },
  {
    id: "expiry",
    number: 5,
    title: "Service Expiry",
    icon: <Clock className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Service remains active as long as credit is valid",
          "Grace period of 30 days after credit expiry",
          "Number may be reassigned after grace period"
        ]
      }
    ]
  },
  {
    id: "emergency",
    number: 6,
    title: "Emergency Services",
    icon: <AlertTriangle className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Emergency calls (111) are free and available even without credit or active service."
      }
    ]
  }
]; 