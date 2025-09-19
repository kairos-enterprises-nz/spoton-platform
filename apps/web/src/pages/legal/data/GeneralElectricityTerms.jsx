import {
  FileText,
  LayoutPanelTop,
  ShieldCheck,
  CalendarClock,
  Receipt,
  PlugZap,
  Move,
  XCircle,
  RefreshCcw,
  Scale,
} from "lucide-react";

export const generalElectricitySections = [
  {
    id: "overview",
    number: 1,
    title: "Overview",
    icon: <FileText className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "paragraph",
        text: "These general terms apply to all electricity services provided by SpotOn, regardless of which pricing plan you’re on."
      }
    ]
  },
  {
    id: "access-meter",
    number: 2,
    title: "Access & Metering",
    icon: <LayoutPanelTop className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "list",
        items: [
          "You must maintain safe and unobstructed access to your electricity meter.",
          "SpotOn may conduct remote or on-site meter reads as required."
        ]
      }
    ]
  },
  {
    id: "safety-regulation",
    number: 3,
    title: "Safety & Regulations",
    icon: <ShieldCheck className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "paragraph",
        text: "You agree to use electricity safely and in compliance with all relevant safety codes, regulations, and health standards."
      }
    ]
  },
  {
    id: "planned-outages",
    number: 4,
    title: "Planned Outages",
    icon: <CalendarClock className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "paragraph",
        text: "SpotOn will provide timely and reasonable notice for any planned service outages that may impact your electricity supply."
      }
    ]
  },
  {
    id: "billing",
    number: 5,
    title: "Billing & Invoicing",
    icon: <Receipt className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "list",
        items: [
          "Invoices are issued monthly unless otherwise specified in your plan.",
          "All billing cycles and practices follow regulatory guidelines and may be updated with prior notice."
        ]
      }
    ]
  },
  {
    id: "disconnection",
    number: 6,
    title: "Disconnection Policy",
    icon: <PlugZap className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "paragraph",
        text: "In the event of disconnection due to unpaid bills, SpotOn will issue advance notices and provide clear options for resolving any outstanding balances."
      }
    ]
  },
  {
    id: "moving-premises",
    number: 7,
    title: "Moving Premises",
    icon: <Move className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "list",
        items: [
          "Customers must notify SpotOn in advance when vacating a property to arrange a final meter read.",
          "Accountability for charges remains until a final read has been processed."
        ]
      }
    ]
  },
  {
    id: "termination",
    number: 8,
    title: "Early Termination",
    icon: <XCircle className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "paragraph",
        text: "Early termination of a contract may incur fees depending on the specific terms of your plan, including minimum term commitments."
      }
    ]
  },
  {
    id: "updates",
    number: 9,
    title: "Terms Updates",
    icon: <RefreshCcw className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "paragraph",
        text: "SpotOn reserves the right to amend these terms with at least 30 days’ notice provided through your registered email or dashboard."
      }
    ]
  },
  {
    id: "regulatory",
    number: 10,
    title: "Regulatory Compliance",
    icon: <Scale className="w-5 h-5 text-primary-turquoise" />, 
    content: [
      {
        type: "paragraph",
        text: "These terms are governed by New Zealand’s electricity regulations and standards as defined by the Electricity Authority."
      }
    ]
  }
];
