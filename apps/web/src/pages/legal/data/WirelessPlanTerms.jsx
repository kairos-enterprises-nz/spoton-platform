import {
  Router,
  AlertTriangle,
  Power,
  ShieldCheck,
  Info,
} from "lucide-react";

export const wirelessPlanTerms = [
  {
    id: "overview",
    number: 1,
    title: "Wireless Overview",
    icon: <Info className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Fixed Wireless broadband delivers internet to your premises using radio signals from a nearby tower, ideal for locations without fibre access."
      },
      {
        type: "list",
        items: [
          "Installation may require an outdoor antenna.",
          "Line-of-sight to the nearest wireless tower is required for service.",
          "Speeds may vary depending on signal strength and weather conditions."
        ]
      }
    ]
  },
  {
    id: "equipment",
    number: 2,
    title: "Equipment & Setup",
    icon: <Router className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "SpotOn may provide or rent wireless routers and antennas. Customers may also bring their own compatible equipment."
      }
    ]
  },
  {
    id: "speed-usage",
    number: 3,
    title: "Speeds & Fair Usage",
    icon: <ShieldCheck className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "Speeds are subject to tower load and distance from transmitter.",
          "Fixed Wireless is suitable for standard browsing, email, and streaming.",
          "Data may be subject to fair use management policies."
        ]
      }
    ]
  },
  {
    id: "outages",
    number: 4,
    title: "Service Interruptions",
    icon: <AlertTriangle className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Outages may be caused by weather or network issues. SpotOn will work to restore service as quickly as possible."
      }
    ]
  },
  {
    id: "termination",
    number: 5,
    title: "Contract & Termination",
    icon: <Power className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Early termination fees may apply if you end your contract before the agreed minimum term."
      }
    ]
  }
];
