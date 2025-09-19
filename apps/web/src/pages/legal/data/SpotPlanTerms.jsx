import { LineChart, TrendingUp, Zap, ShieldCheck, AlertTriangle, Info } from "lucide-react";

export const spotPlanTerms = [
  {
    id: "overview",
    number: 1,
    title: "Overview",
    icon: <Zap className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Spot Pricing plans are linked to the wholesale electricity market, and prices may change every 30 minutes based on supply and demand."
      }
    ]
  },
  {
    id: "pricing-details",
    number: 2,
    title: "Pricing Details",
    icon: <LineChart className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Customers pay the actual spot price plus a fixed retailer margin.",
          "Spot prices can be volatile and may spike during high-demand periods.",
          "You will receive usage reports reflecting pricing fluctuations."
        ]
      }
    ]
  },
  {
    id: "suitability",
    number: 3,
    title: "Plan Suitability",
    icon: <TrendingUp className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Spot Pricing is not recommended for customers needing stable or predictable billing."
      },
      {
        type: "list",
        items: [
          "Ideal for energy-conscious users or those with solar generation.",
          "Requires comfort with price fluctuations."
        ]
      }
    ]
  },
  {
    id: "metering",
    number: 4,
    title: "Smart Meter Requirements",
    icon: <ShieldCheck className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Customers must have a smart meter capable of half-hourly reads to be eligible for this plan."
      }
    ]
  },
  {
    id: "disclaimer",
    number: 5,
    title: "Risk Disclaimer",
    icon: <AlertTriangle className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "SpotOn is not liable for price increases resulting from wholesale market spikes.",
          "Customers are responsible for managing their usage during high-price periods."
        ]
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
        text: "Contact SpotOn support to understand the latest wholesale trends or to evaluate if a Spot Pricing plan is right for you."
      }
    ]
  }
];
