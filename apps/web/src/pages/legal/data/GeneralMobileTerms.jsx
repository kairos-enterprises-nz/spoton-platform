import {
  Phone,
  Shield,
  Battery,
  MapPin,
  Wifi,
  CreditCard,
  Clock,
  AlertTriangle,
  RefreshCcw,
  Scale,
} from "lucide-react";

export const generalMobileSections = [
  {
    id: "overview",
    number: 1,
    title: "Overview",
    icon: <Phone className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "These general terms apply to all mobile services provided by SpotOn, regardless of which plan you're on."
      }
    ]
  },
  {
    id: "coverage",
    number: 2,
    title: "Network Coverage",
    icon: <MapPin className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Our mobile network coverage extends across New Zealand, with varying signal strength depending on location and terrain."
      },
      {
        type: "list",
        items: [
          "Coverage maps are available on our website",
          "Rural areas may have limited coverage",
          "Indoor coverage may vary based on building materials"
        ]
      }
    ]
  },
  {
    id: "data-usage",
    number: 3,
    title: "Data Usage",
    icon: <Wifi className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Data usage is measured in bytes and rounded up to the nearest kilobyte. Fair use policies apply to all data plans."
      }
    ]
  },
  {
    id: "billing",
    number: 4,
    title: "Billing & Payments",
    icon: <CreditCard className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Monthly billing for postpaid plans",
          "Prepaid plans require advance payment",
          "Late payments may result in service suspension"
        ]
      }
    ]
  },
  {
    id: "roaming",
    number: 5,
    title: "International Roaming",
    icon: <MapPin className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "International roaming is available in selected countries. Rates and coverage vary by destination."
      }
    ]
  },
  {
    id: "device-support",
    number: 6,
    title: "Device Support",
    icon: <Phone className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "list",
        items: [
          "Compatible with most unlocked GSM devices",
          "Limited support for CDMA devices",
          "Device-specific features may vary"
        ]
      }
    ]
  },
  {
    id: "fair-use",
    number: 7,
    title: "Fair Use Policy",
    icon: <Shield className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Our fair use policy ensures quality service for all customers by preventing network abuse and excessive usage."
      }
    ]
  },
  {
    id: "emergency",
    number: 8,
    title: "Emergency Services",
    icon: <AlertTriangle className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "Emergency calls (111) are free and available even without credit or active service."
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
        text: "We may update these terms with 30 days' notice. Continued use of our services constitutes acceptance of updated terms."
      }
    ]
  },
  {
    id: "compliance",
    number: 10,
    title: "Regulatory Compliance",
    icon: <Scale className="w-5 h-5 text-primary-turquoise" />,
    content: [
      {
        type: "paragraph",
        text: "All services comply with New Zealand telecommunications regulations and consumer protection laws."
      }
    ]
  }
]; 