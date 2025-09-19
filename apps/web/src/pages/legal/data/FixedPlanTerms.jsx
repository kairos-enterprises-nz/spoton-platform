import { FileText, ShieldCheck, Lock, CalendarCheck, Clock, AlertCircle } from "lucide-react";

export const fixedPlanTerms = [
  {
    id: "intro",
    number: 1,
    title: "Plan Overview",
    icon: <FileText className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Fixed Rate plans provide stable pricing for the duration of your agreement, helping you avoid unexpected spikes in your electricity bill."
      }
    ]
  },
  {
    id: "pricing-structure",
    number: 2,
    title: "Pricing Structure",
    icon: <ShieldCheck className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Unit rates and daily charges are fixed for the contracted period.",
          "Your usage will still be measured by your smart meter and billed monthly.",
          "Any changes to the plan during the term will be communicated in writing."
        ]
      }
    ]
  },
  {
    id: "early-exit",
    number: 3,
    title: "Early Exit Policy",
    icon: <Lock className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "You may be charged an early exit fee if you choose to terminate your Fixed Rate plan before the agreed term ends."
      },
      {
        type: "list",
        items: [
          "Exit fees are based on the remaining term and your average usage.",
          "If you are moving, you may be able to transfer the plan to your new premises."
        ]
      }
    ]
  },
  {
    id: "budgeting",
    number: 4,
    title: "Budget Certainty",
    icon: <CalendarCheck className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Fixed Rate plans are recommended for customers who value certainty and want to manage their electricity budget."
      },
      {
        type: "list",
        items: [
          "Predictable pricing month-to-month.",
          "No exposure to wholesale market volatility."
        ]
      }
    ]
  },
  {
    id: "plan-renewal",
    number: 5,
    title: "Renewal Terms",
    icon: <Clock className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Your Fixed Rate plan may be eligible for renewal at the end of its term."
      },
      {
        type: "list",
        items: [
          "SpotOn will provide renewal offers with updated pricing, if available.",
          "You may need to agree to new terms depending on market conditions."
        ]
      }
    ]
  },
  {
    id: "support",
    number: 6,
    title: "Need Support?",
    icon: <AlertCircle className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "If you have questions about your Fixed Rate plan or need help understanding your contract, our support team is here to help."
      }
    ]
  }
];
