import { Wrench, Satellite, ShieldCheck, Power, Headphones, Info } from "lucide-react";

export const ruralPlanTerms = [
  {
    id: "overview",
    number: 1,
    title: "Rural Broadband Overview",
    icon: <Info className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Rural broadband plans are designed for customers in non-urban areas where standard fibre connections may not be available. These services often rely on long-range wireless or satellite technology."
      }
    ]
  },
  {
    id: "installation",
    number: 2,
    title: "Installation & Equipment",
    icon: <Wrench className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "Installation times may vary due to regional infrastructure.",
          "You may require external equipment such as directional antennas or satellite dishes.",
          "SpotOn will coordinate with local providers for optimal setup."
        ]
      }
    ]
  },
  {
    id: "performance",
    number: 3,
    title: "Performance & Conditions",
    icon: <Satellite className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Performance may be affected by terrain, distance from towers, or weather conditions."
      },
      {
        type: "list",
        items: [
          "Service may differ in reliability compared to fibre or fixed wireless.",
          "Signal strength and speed can vary based on location.",
          "We aim to maintain stable connectivity using partner networks."
        ]
      }
    ]
  },
  {
    id: "fairuse",
    number: 4,
    title: "Fair Use & Data Limits",
    icon: <ShieldCheck className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Plans are subject to a Fair Use Policy and may include data caps."
      },
      {
        type: "list",
        items: [
          "Heavy usage may be shaped to protect network quality.",
          "Streaming and downloads may be deprioritized during peak times.",
          "Excessive or malicious use may result in temporary throttling."
        ]
      }
    ]
  },
  {
    id: "support",
    number: 5,
    title: "Technical Support",
    icon: <Headphones className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Support is provided via phone, chat, or email. Response times may vary by location or provider."
      }
    ]
  },
  {
    id: "termination",
    number: 6,
    title: "Termination & Exit Terms",
    icon: <Power className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "Fixed-term plans may incur early exit fees if cancelled before term ends.",
          "Open-term plans may be cancelled with 30 days’ notice.",
          "Equipment must be returned in working condition."
        ]
      }
    ]
  }
];
