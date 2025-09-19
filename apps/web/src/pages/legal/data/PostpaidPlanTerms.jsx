import {
  Phone,
  CreditCard,
  Clock,
  AlertTriangle,
  RefreshCcw,
  Shield,
  FileText,
} from "lucide-react";

export const postpaidPlanTerms = [
  {
    id: "overview",
    number: 1,
    title: "Plan Overview",
    icon: <Phone className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Postpaid plans provide monthly billing with flexible data options and included minutes. Service is billed in arrears based on actual usage."
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
          "Monthly billing cycle based on activation date",
          "Payment due within 14 days of invoice",
          "Late payment fees may apply",
          "Direct debit and credit card payment options available"
        ]
      }
    ]
  },
  {
    id: "data-usage",
    number: 3,
    title: "Data Usage",
    icon: <RefreshCcw className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Data usage is measured in bytes and rounded up to the nearest kilobyte. Excess data charges apply after plan allowance is used."
      }
    ]
  },
  {
    id: "contract",
    number: 4,
    title: "Contract Terms",
    icon: <FileText className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "12 or 24-month terms available",
          "Early termination fees may apply",
          "Plan changes allowed with 30 days notice"
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
        text: "Postpaid services are subject to fair use policies to prevent network abuse and ensure quality service for all customers."
      }
    ]
  },
  {
    id: "roaming",
    number: 6,
    title: "International Roaming",
    icon: <Clock className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Available in selected countries",
          "Rates vary by destination",
          "Data roaming packs available",
          "Must be activated before travel"
        ]
      }
    ]
  },
  {
    id: "emergency",
    number: 7,
    title: "Emergency Services",
    icon: <AlertTriangle className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Emergency calls (111) are free and available even if your account is suspended or you have exceeded your plan limits."
      }
    ]
  }
]; 