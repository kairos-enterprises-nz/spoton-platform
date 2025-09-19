import {
  ShieldCheck,
  User,
  Globe,
  AlertCircle,
  XCircle,
  Lock,
  CreditCard,
  FileText,
  RefreshCw,
  HelpCircle,
  Eye,
  Trash2,
} from "lucide-react";

export const termsSections = [
  {
    id: "account",
    number: 1,
    title: "Account Registration",
    icon: <User className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "You must be at least 18 years old and provide accurate, up-to-date information during registration. You are responsible for maintaining the security of your account credentials.",
      },
    ],
  },
  {
    id: "availability",
    number: 2,
    title: "Service Availability",
    icon: <Globe className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "We strive for consistent service uptime, but access may occasionally be interrupted for maintenance, updates, or external outages.",
      },
      {
        type: "callout",
        icon: <AlertCircle className="inline w-4 h-4 mr-1" />,
        text: "Planned outages will be communicated via your registered email or dashboard notifications.",
      },
    ],
  },
  {
    id: "usage",
    number: 3,
    title: "Usage Guidelines",
    icon: <ShieldCheck className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "You agree to use our services only for lawful purposes. Misuse of the platform is prohibited, including unauthorized access or actions that harm the service or other users.",
      },
      {
        type: "list",
        items: [
          "No spamming, phishing, or fraudulent activity",
          "No unauthorized automation or data scraping",
          "No attempt to bypass security features or access restricted areas",
        ],
      },
    ],
  },
  {
    id: "billing",
    number: 4,
    title: "Billing & Payments",
    icon: <CreditCard className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "All payments are due as outlined in your billing agreement. Failure to pay may result in suspension or cancellation of service.",
      },
      {
        type: "list",
        items: [
          "Invoices will be issued monthly via email or dashboard",
          "Late payments may incur penalties or service disruption",
          "You are responsible for keeping your payment method up to date",
        ],
      },
    ],
  },
  {
    id: "data-policy",
    number: 5,
    title: "Privacy & Data Handling",
    icon: <Eye className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "Your data is handled in accordance with our Privacy Policy. We take steps to ensure your personal information is secure and only used for legitimate business operations.",
      },
      {
        type: "callout",
        icon: <Lock className="inline w-4 h-4 mr-1" />,
        text: "For full details, refer to our separate Privacy Policy page.",
      },
    ],
  },
  {
    id: "termination",
    number: 6,
    title: "Termination of Service",
    icon: <XCircle className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "We reserve the right to terminate your account if you breach these terms, misuse the service, or fail to meet payment obligations.",
      },
      {
        type: "list",
        items: [
          "We will attempt to notify you before suspension or termination",
          "Some terminations may occur immediately for severe abuse or fraud",
        ],
      },
    ],
  },
  {
    id: "changes",
    number: 7,
    title: "Service Modifications",
    icon: <RefreshCw className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "We may modify or discontinue parts of the service at any time. Significant changes will be communicated to affected users in advance.",
      },
    ],
  },
  {
    id: "support",
    number: 8,
    title: "Customer Support",
    icon: <HelpCircle className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "SpotOn provides support through email, live chat, and help center documentation. We aim to respond within 2 business days for general inquiries.",
      },
      {
        type: "list",
        items: [
          "For urgent billing issues, use the Support > Billing category",
          "Support hours: Mon–Fri, 9am–5pm NZST",
        ],
      },
    ],
  },
  {
    id: "legal",
    number: 9,
    title: "Governing Law & Disputes",
    icon: <FileText className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "These terms are governed by the laws of New Zealand. Disputes will be resolved under New Zealand jurisdiction unless otherwise specified.",
      },
    ],
  },
  {
    id: "deletion",
    number: 10,
    title: "Account Deletion",
    icon: <Trash2 className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "You may request account deletion at any time. All associated data will be removed except as required by law or for billing recordkeeping.",
      },
    ],
  },
];
