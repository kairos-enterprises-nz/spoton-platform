import {
  Info,
  Wrench,
  Gauge,
  ShieldCheck,
  CreditCard,
  Headphones,
  Power,
  Box,
  MapPin,
  Scale,
} from "lucide-react";

export const broadbandGeneralTerms = [
  {
    id: "overview",
    number: 1,
    title: "Overview",
    icon: <Info className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "These general terms apply to all broadband services provided by SpotOn, including fibre, fixed wireless, and rural broadband options."
      }
    ]
  },
  {
    id: "installation",
    number: 2,
    title: "Installation and Equipment",
    icon: <Wrench className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "Installation may require property access and scheduling with technicians.",
          "Customers may bring their own router or rent/purchase one from SpotOn.",
          "Additional setup charges may apply for non-standard installations."
        ]
      }
    ]
  },
  {
    id: "usage",
    number: 3,
    title: "Speed and Usage",
    icon: <Gauge className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Broadband speeds are indicative and may vary based on network congestion, equipment, and service type."
      },
      {
        type: "list",
        items: [
          "Fibre plans offer the most consistent speed.",
          "Wireless and rural plans may be affected by signal quality and location.",
          "Actual speeds may be lower during peak hours."
        ]
      }
    ]
  },
  {
    id: "fairuse",
    number: 4,
    title: "Fair Use Policy",
    icon: <ShieldCheck className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "SpotOn applies a Fair Use Policy to ensure quality of service for all users."
      },
      {
        type: "list",
        items: [
          "Unusually high or malicious usage may be shaped or suspended.",
          "Peer-to-peer file sharing and high-volume streaming may be deprioritized on rural networks."
        ]
      }
    ]
  },
  {
    id: "billing",
    number: 5,
    title: "Billing & Payments",
    icon: <CreditCard className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "Billing is monthly, with invoices sent via email or available online.",
          "Payment methods include direct debit, card, or bank transfer.",
          "Late payment may result in suspension of services or recovery charges."
        ]
      }
    ]
  },
  {
    id: "support",
    number: 6,
    title: "Technical Support",
    icon: <Headphones className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Support is available via phone, chat, or email during business hours. Urgent faults are handled 24/7."
      }
    ]
  },
  {
    id: "termination",
    number: 7,
    title: "Service Termination",
    icon: <Power className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Services may be terminated by either party with notice. Minimum terms and early exit fees may apply."
      }
    ]
  },
  {
    id: "equipment",
    number: 8,
    title: "Equipment Responsibility",
    icon: <Box className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "Customers are responsible for keeping routers and other equipment safe.",
          "Damaged rental equipment must be returned or may incur charges."
        ]
      }
    ]
  },
  {
    id: "addresschange",
    number: 9,
    title: "Moving Address",
    icon: <MapPin className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Please inform us at least 10 business days in advance to arrange service relocation. Availability may vary at the new address."
      }
    ]
  },
  {
    id: "compliance",
    number: 10,
    title: "Legal and Regulatory",
    icon: <Scale className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "All broadband services are delivered in accordance with New Zealand telecommunications regulations and Fair Trading standards."
      }
    ]
  }
];
