import {
  Info,
  Globe,
  CreditCard,
  Wrench,
  Router,
  ListOrdered,
  MapPin,
  Power,
  ShieldCheck,
  AlertTriangle,
  CheckCircle,
  Scale,
  Gauge,
} from "lucide-react";

export const fibreDisclosure = [
  {
    id: "disclosure-overview",
    number: "D1",
    title: "Product Disclosure Overview",
    icon: <Info className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "This disclosure outlines key features and terms for Fibre Broadband. Applies to signups or changes from 10 Feb 2022."
      }
    ]
  },
  {
    id: "disclosure-service",
    number: "D2",
    title: "Service Overview",
    icon: <Globe className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Broadband and optional home phone services are available. Availability depends on location. Visit www.2degreesbroadband.co.nz or call 0800 022 202."
      }
    ]
  },
  {
    id: "disclosure-charges",
    number: "D3",
    title: "Service Charges",
    icon: <CreditCard className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "table",
        columns: ["Charge", "Monthly Data", "Access Type"],
        rows: [
          ["$65", "Unlimited", "Fibre 50"],
          ["$95", "Unlimited", "Fibre 300"],
          ["$110", "Unlimited", "Fibre 900"],
          ["$149", "Unlimited", "Hyperfibre 2"],
          ["$179", "Unlimited", "Hyperfibre 4"],
        ]
      },
      {
        type: "callout",
        text: "*Fair Use Policy applies. $10 discount with eligible mobile. Prices current as of 4 Nov 2024."
      }
    ]
  },
  {
    id: "disclosure-setup",
    number: "D4",
    title: "Additional Setup Charges",
    icon: <Wrench className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: [
          "$99 connection fee (open term)",
          "$199 modem charge (+$15 delivery)",
          "12-month term may include free connection & $5/month modem rental"
        ]
      }
    ]
  },
  {
    id: "disclosure-modem",
    number: "D5",
    title: "Modem Return & Charges",
    icon: <Router className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Leased modems must be returned or you may be charged:"
      },
      {
        type: "table",
        columns: ["Modem", "< 12 mo", "> 12 mo", "Charger Fee"],
        rows: [
          ["Fritz 7490", "$165", "$110", "Current"],
          ["Fritz 7590", "$299", "$200", "Current"],
          ["ORBI (Hyperfibre)", "$499", "$499", "Current"],
          ["TP Link HB810", "$499", "$499", "Current"]
        ]
      }
    ]
  },
  {
    id: "disclosure-access",
    number: "D6",
    title: "Access Type",
    icon: <ListOrdered className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Fibre is standard. ADSL or VDSL may be used where Fibre is unavailable (may incur $4/month fee)."
      }
    ]
  },
  {
    id: "disclosure-contract",
    number: "D7",
    title: "Minimum Contract Term",
    icon: <MapPin className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "list",
        items: ["Open term", "12-month term", "Or a promotional term offered to you"]
      }
    ]
  },
  {
    id: "disclosure-early-exit",
    number: "D8",
    title: "Early Termination",
    icon: <Power className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Early exit fees up to $199 may apply. Promotional credits must be repaid if cancelled early."
      }
    ]
  },
  {
    id: "disclosure-notice",
    number: "D9",
    title: "Notice Period",
    icon: <AlertTriangle className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Cancel before your next billing cycle to avoid charges for the following month."
      }
    ]
  },
  {
    id: "disclosure-traffic",
    number: "D10",
    title: "Traffic Management",
    icon: <Gauge className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "No throttling on unlimited plans. We may manage peak traffic to ensure quality service."
      }
    ]
  },
  {
    id: "disclosure-fairuse",
    number: "D11",
    title: "Fair Use Policy",
    icon: <ShieldCheck className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "No excessive, automated, or commercial usage. Violations may lead to restrictions or service cancellation."
      }
    ]
  },
  {
    id: "disclosure-backup",
    number: "D12",
    title: "Power Backup Notice",
    icon: <Power className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "Service depends on mains power. In outages, home phone or alarm services may not work without backup."
      }
    ]
  },
  {
    id: "disclosure-disputes",
    number: "D13",
    title: "Disputes & Complaints",
    icon: <Scale className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "For disputes, see our complaints process or the TDR Scheme at tdr.org.nz. All prices include GST."
      }
    ]
  },
  {
    id: "disclosure-final",
    number: "D14",
    title: "Final Note",
    icon: <CheckCircle className="w-4 h-4 text-accent-purple" />,
    content: [
      {
        type: "paragraph",
        text: "This is a product summary only. Full legal terms are available online and should be reviewed in full."
      }
    ]
  }
];
