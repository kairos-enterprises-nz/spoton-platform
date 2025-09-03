import {
  Lock,
  Eye,
  Cloud,
  ShieldCheck,
  Trash2,
  Share2,
  FileLock2,
  FileWarning,
  Info,
} from "lucide-react";

export const privacySections = [
  {
    id: "introduction",
    number: 1,
    title: "Introduction",
    icon: <Lock className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "Your privacy matters to us. This Privacy Policy explains how SpotOn collects, uses, shares, and protects your personal data across our services and platforms.",
      },
    ],
  },
  {
    id: "what-we-collect",
    number: 2,
    title: "What We Collect",
    icon: <Eye className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "We collect only the data necessary to operate our services effectively. This may include:",
      },
      {
        type: "list",
        items: [
          "Contact details (e.g., name, email address, phone number)",
          "Service and product preferences",
          "Payment and billing details",
          "Usage behavior and interaction data on our website and dashboard",
          "Device identifiers, IP address, and location (where applicable)",
        ],
      },
    ],
  },
  {
    id: "how-we-use",
    number: 3,
    title: "How We Use Your Data",
    icon: <Cloud className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "We use your data to provide, personalize, and improve our services, comply with obligations, and deliver helpful, relevant information.",
      },
      {
        type: "list",
        items: [
          "To process sign-ups and service activations",
          "To manage your utility account and billing",
          "To personalize recommendations and updates",
          "To provide technical and customer support",
          "To send usage reports, alerts, and newsletters (if subscribed)",
        ],
      },
    ],
  },
  {
    id: "data-sharing",
    number: 4,
    title: "Data Sharing & Disclosure",
    icon: <Share2 className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "We do not sell your personal information. Data is only shared with third parties where necessary to deliver services or fulfill legal obligations.",
      },
      {
        type: "list",
        items: [
          "Payment providers (for billing and refunds)",
          "Service delivery partners (e.g., meter data collectors, broadband installers)",
          "Legal authorities when required by law or warrant",
          "Analytics providers (aggregated usage insights only)",
        ],
      },
    ],
  },
  {
    id: "data-protection",
    number: 5,
    title: "Data Security & Protection",
    icon: <ShieldCheck className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "We take data protection seriously and follow industry best practices to prevent unauthorized access, misuse, or loss of your data.",
      },
      {
        type: "callout",
        icon: <ShieldCheck className="inline w-4 h-4 mr-1" />,
        text: "We use encryption, firewalls, access logs, and third-party security assessments to secure your data.",
      },
    ],
  },
  {
    id: "your-rights",
    number: 6,
    title: "Your Rights & Choices",
    icon: <Trash2 className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "You have the right to request, update, or delete your personal information. You can also control how we contact or market to you.",
      },
      {
        type: "list",
        items: [
          "Request a copy of your stored data",
          "Correct or update inaccurate details",
          "Request account deletion and data removal",
          "Control marketing or promotional preferences",
        ],
      },
    ],
  },
  {
    id: "data-retention",
    number: 7,
    title: "Data Retention",
    icon: <FileLock2 className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "We retain personal data only as long as necessary for legitimate business or legal purposes, such as billing history or dispute resolution.",
      },
    ],
  },
  {
    id: "policy-changes",
    number: 8,
    title: "Policy Updates & Notification",
    icon: <FileWarning className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "We may update this Privacy Policy to reflect changes in technology, law, or business operations. Significant updates will be communicated through your dashboard or email.",
      },
    ],
  },
  {
    id: "contact",
    number: 9,
    title: "Contact & Questions",
    icon: <Info className="w-5 h-5" />,
    content: [
      {
        type: "paragraph",
        text: "If you have any questions or concerns about your privacy, you can reach us directly via email at privacy@spoton.co.nz.",
      },
      {
        type: "callout",
        icon: <Info className="inline w-4 h-4 mr-1" />,
        text: "We're committed to addressing any concerns promptly and transparently.",
      },
    ],
  },
];
