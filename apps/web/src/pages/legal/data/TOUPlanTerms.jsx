import { Clock, LayoutList, ShieldCheck, Home, Map, Info } from "lucide-react";

export const touPlanTerms = [
  {
    id: "overview",
    number: 1,
    title: "Overview",
    icon: <Clock className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Time-of-Use (TOU) plans charge different rates depending on the time of day electricity is consumed, encouraging off-peak usage."
      }
    ]
  },
  {
    id: "time-bands",
    number: 2,
    title: "Peak and Off-Peak Hours",
    icon: <LayoutList className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Peak hours typically include weekdays from 5pm to 9pm.",
          "Off-peak hours include overnight, weekends, and public holidays.",
          "Smart meters are required to accurately measure and bill usage across time bands."
        ]
      }
    ]
  },
  {
    id: "suitability",
    number: 3,
    title: "Plan Suitability",
    icon: <Home className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "TOU plans are best suited for households that can shift consumption to off-peak periods to take advantage of lower rates."
      }
    ]
  },
  {
    id: "tariffs",
    number: 4,
    title: "Regional Tariffs",
    icon: <Map className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Tariffs are published annually and may vary by distributor region.",
          "Peak and off-peak definitions are subject to your network provider’s specific guidelines."
        ]
      }
    ]
  },
  {
    id: "compliance",
    number: 5,
    title: "Smart Meter Compliance",
    icon: <ShieldCheck className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Enrollment in a TOU plan requires a smart meter capable of recording half-hourly usage to ensure accurate billing."
      }
    ]
  },
  {
    id: "support",
    number: 6,
    title: "More Information",
    icon: <Info className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Reach out to SpotOn support if you’d like to check your eligibility for TOU plans or receive guidance on optimizing your usage."
      }
    ]
  }
];
