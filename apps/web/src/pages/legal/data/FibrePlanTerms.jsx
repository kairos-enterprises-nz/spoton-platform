import {
  Info,
  Wrench,
  Router,
  Gauge,
  CreditCard,
  MapPin,
  Power,
  Headphones,
  ShieldCheck,
  Scale,
} from "lucide-react";

export const fibrePlanTerms = [
  {
    id: "overview",
    number: 1,
    title: "Overview",
    icon: <Info className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Fiber plans use the national UFB (Ultra-Fast Broadband) network to provide high-speed, reliable connectivity to eligible premises."
      }
    ]
  },
  {
    id: "installation",
    number: 2,
    title: "Installation",
    icon: <Wrench className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "Installation may require external and internal cabling work.",
          "A technician may need access to your property during business hours.",
          "Consent may be required from landlords or property managers."
        ]
      }
    ]
  },
  {
    id: "equipment",
    number: 3,
    title: "Equipment",
    icon: <Router className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "You may bring your own compatible router or rent/purchase one from SpotOn."
      }
    ]
  },
  {
    id: "speeds",
    number: 4,
    title: "Speeds & Performance",
    icon: <Gauge className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "Typical speeds vary by plan tier and time of day.",
          "Actual performance may be impacted by Wi-Fi interference or internal wiring.",
          "Speed claims are based on national averages and lab-tested conditions."
        ]
      }
    ]
  },
  {
    id: "billing",
    number: 5,
    title: "Billing & Term",
    icon: <CreditCard className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Billing is monthly in advance. Fixed-term contracts may apply for certain plans or promotions."
      }
    ]
  },
  {
    id: "relocation",
    number: 6,
    title: "Relocation",
    icon: <MapPin className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "If you move house, additional charges may apply to relocate fiber services to your new address."
      }
    ]
  },
  {
    id: "termination",
    number: 7,
    title: "Termination",
    icon: <Power className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "You may cancel anytime on open-term plans with 30 days’ notice.",
          "Early exit fees may apply for fixed-term plans."
        ]
      }
    ]
  },
  {
    id: "support",
    number: 8,
    title: "Support",
    icon: <Headphones className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Our team provides technical support via phone, chat, or email. Network issues may be escalated to the LFC (Local Fibre Company)."
      }
    ]
  },
  {
    id: "fairuse",
    number: 9,
    title: "Fair Use Policy",
    icon: <ShieldCheck className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Plans are subject to fair usage and must not interfere with network integrity or other users’ experience."
      }
    ]
  },
  {
    id: "regulations",
    number: 10,
    title: "Compliance",
    icon: <Scale className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "All services are governed by New Zealand telecommunications regulations and are subject to LFC installation policies."
      }
    ]
  }
];
