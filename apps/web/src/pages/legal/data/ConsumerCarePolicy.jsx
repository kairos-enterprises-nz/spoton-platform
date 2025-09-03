import {
    Handshake,
    AlertTriangle,
    HelpCircle,
    Phone,
    ShieldCheck,
    Info,
    SmilePlus,
    Clock,
    BookOpenCheck,
    Users,
  } from "lucide-react";
  
  export const consumerCareSections = [
    {
      id: "your-rights",
      number: 1,
      title: "Your Rights as a Consumer",
      icon: <Handshake className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "You have the right to fair treatment, transparent communication, and safe, reliable utility services. SpotOn is committed to upholding your rights in accordance with consumer protection laws.",
        },
        {
          type: "list",
          items: [
            "Fair and respectful service at all times",
            "Clear and timely communication",
            "Accurate billing and flexible payment options",
            "Support for vulnerable and medically dependent customers",
          ],
        },
      ],
    },
    {
      id: "making-a-complaint",
      number: 2,
      title: "How to Make a Complaint",
      icon: <AlertTriangle className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "We take all feedback seriously. If you're dissatisfied with our service, we encourage you to submit a complaint through one of our official channels so we can resolve the issue promptly.",
        },
        {
          type: "callout",
          icon: <AlertTriangle className="inline w-4 h-4 mr-1" />,
          text: "Complaints will be acknowledged within 2 business days and resolved within 20 working days, unless otherwise communicated.",
        },
      ],
    },
    {
      id: "support-vulnerable",
      number: 3,
      title: "Support for Vulnerable Customers",
      icon: <HelpCircle className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "SpotOn provides additional support for customers who may be vulnerable due to health, age, disability, or financial circumstances.",
        },
        {
          type: "list",
          items: [
            "Priority assistance during outages",
            "Payment flexibility and debt support",
            "Referral to external support services",
            "Safe disconnection practices with additional care steps",
          ],
        },
      ],
    },
    {
      id: "disconnection-support",
      number: 4,
      title: "Disconnection & Payment Support",
      icon: <ShieldCheck className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "We aim to prevent disconnection wherever possible. Customers experiencing financial difficulty can request alternative payment arrangements or apply for hardship support.",
        },
        {
          type: "callout",
          icon: <ShieldCheck className="inline w-4 h-4 mr-1" />,
          text: "Disconnection is always a last resort. You will be given multiple notices, support options, and a clear pathway to reconnect.",
        },
      ],
    },
    {
      id: "contact",
      number: 5,
      title: "Contact & Response Times",
      icon: <Phone className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "Our customer care team is available via phone, email, or chat. We aim to respond to all enquiries quickly and resolve most queries within 2 business days.",
        },
        {
          type: "list",
          items: [
            "Phone: 0800 SPOTON (Mon–Fri, 8am–6pm)",
            "Email: support@spoton.co.nz",
            "Live Chat: Available on our website and dashboard",
          ],
        },
      ],
    },
    {
      id: "accessibility-inclusion",
      number: 6,
      title: "Accessibility & Inclusion",
      icon: <SmilePlus className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "We are committed to delivering services that are inclusive and accessible to all. We will make reasonable accommodations to support customers with disabilities or language barriers.",
        },
      ],
    },
    {
      id: "consumer-rights-info",
      number: 7,
      title: "Understanding Your Rights",
      icon: <Info className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "You can learn more about your rights under New Zealand consumer law by visiting www.consumerprotection.govt.nz or by speaking to our team. We’ll gladly walk you through your entitlements.",
        },
      ],
    },
    {
      id: "response-timeframes",
      number: 8,
      title: "Response Timeframes",
      icon: <Clock className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "We aim to meet the following timeframes for customer care processes:",
        },
        {
          type: "list",
          items: [
            "Complaints: Initial acknowledgment within 2 business days",
            "Email support: Response within 1–2 business days",
            "Urgent faults or disconnections: Same-day triage",
          ],
        },
      ],
    },
    {
      id: "service-standards",
      number: 9,
      title: "Customer Service Standards",
      icon: <BookOpenCheck className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "We adhere to high standards of service delivery and aim to treat all customers fairly, with dignity and respect, regardless of their circumstances or background.",
        },
      ],
    },
    {
      id: "community-focus",
      number: 10,
      title: "Community & Wellbeing Focus",
      icon: <Users className="w-5 h-5" />,
      content: [
        {
          type: "paragraph",
          text: "SpotOn believes in building long-term community relationships and contributing to wellbeing by supporting local initiatives, education around energy use, and inclusive service access.",
        },
      ],
    },
  ];
  