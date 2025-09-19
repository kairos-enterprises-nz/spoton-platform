import {
  Sparkles,
  UserCheck,
  Layers,
  Info,
  ShieldCheck,
  ArrowRightLeft,
  Settings,
  Globe,
} from 'lucide-react';

export const faqCategories = ["All", "Getting Started", "Plans & Pricing", "Bundles", "Experience"];

export const generalFaqs = [
  {
    category: "Getting Started",
    icon: Sparkles,
    color: "bg-blue-100 text-blue-800",
    title: "What is SpotOn?",
    content: [
      { type: "paragraph", text: "SpotOn is a smart, modern utility provider that brings power and broadband together in a single platform. We focus on transparency, digital-first tools, and flexibility." }
    ]
  },
  {
    category: "Getting Started",
    icon: UserCheck,
    color: "bg-green-100 text-green-800",
    title: "How do I join SpotOn?",
    content: [
      { type: "paragraph", text: "Click 'Get Started' and follow the sign-up prompts. All you need is your address, an email, and a few minutes. We'll guide you from there." }
    ]
  },
  {
    category: "Getting Started",
    icon: UserCheck,
    color: "bg-green-100 text-green-800",
    title: "Can I use my own router?",
    content: [
      { type: "paragraph", text: "Absolutely. If you have a compatible device, you can BYO. Or, we can ship you one that's pre-configured." }
    ]
  },
  {
    category: "Plans & Pricing",
    icon: Layers,
    color: "bg-yellow-100 text-yellow-800",
    title: "Do I have to sign a contract?",
    content: [
      { type: "paragraph", text: "No. Most of our services are open-term with no lock-ins. You can leave at any time, or choose fixed plans if you're after long-term savings." }
    ]
  },
  {
    category: "Plans & Pricing",
    icon: ArrowRightLeft,
    color: "bg-yellow-100 text-yellow-800",
    title: "How do I change my plan?",
    content: [
      { type: "paragraph", text: "You can change your power or broadband plan anytime from your dashboard. Changes usually apply from your next billing cycle." },
      { type: "link", href: "/account/plans", text: "Manage My Plans →" }
    ]
  },
  {
    category: "Plans & Pricing",
    icon: ShieldCheck,
    color: "bg-yellow-100 text-yellow-800",
    title: "Are there any hidden fees?",
    content: [
      { type: "paragraph", text: "No hidden charges. We show all fees upfront — including usage, service, and network-related charges if applicable." }
    ]
  },
  {
    category: "Bundles",
    icon: Layers,
    color: "bg-purple-100 text-purple-800",
    title: "Can I get power and internet together?",
    content: [
      { type: "paragraph", text: "Yes. You can sign up for either service on its own, or bundle them for simplicity — one bill, one dashboard, one provider." }
    ]
  },
  {
    category: "Bundles",
    icon: Layers,
    color: "bg-purple-100 text-purple-800",
    title: "Do I have to bundle services?",
    content: [
      { type: "paragraph", text: "Nope. You can choose power only, broadband only, or both. You decide what fits your lifestyle best." }
    ]
  },
  {
    category: "Experience",
    icon: Info,
    color: "bg-gray-100 text-gray-800",
    title: "What makes SpotOn different?",
    content: [
      { type: "paragraph", text: "We're digital by design, focused on automation, useful insights, and giving you control. Our support, plans, and pricing are built around flexibility and clarity." }
    ]
  },
  {
    category: "Experience",
    icon: Globe,
    color: "bg-gray-100 text-gray-800",
    title: "Is SpotOn available nationwide?",
    content: [
      { type: "paragraph", text: "Yes — we're expanding across New Zealand. Enter your address during sign-up to check if we're live in your area." }
    ]
  },
  {
    category: "Experience",
    icon: Settings,
    color: "bg-gray-100 text-gray-800",
    title: "Can I manage everything online?",
    content: [
      { type: "paragraph", text: "Yes. Our dashboard gives you full control — view usage, update details, change plans, download invoices, and more." }
    ]
  },
  {
    question: "How do I check my mobile data usage?",
    answer: "You can check your mobile data usage through your SpotOn account dashboard or mobile app. Navigate to the 'Mobile' section and you'll find your current data usage, remaining data, and usage history."
  },
  {
    question: "What should I do if I have poor mobile network coverage?",
    answer: "If you're experiencing poor network coverage, try these steps: 1) Check if you're in a coverage area using our coverage map, 2) Ensure your device is updated to the latest software, 3) Try toggling airplane mode on and off, 4) If issues persist, contact our technical support team."
  },
  {
    question: "How do I set up international roaming for my mobile plan?",
    answer: "To set up international roaming, log into your SpotOn account, go to the Mobile section, and select 'International Roaming'. You can enable roaming for specific countries or regions. Remember that roaming charges may apply based on your destination."
  },
  {
    question: "What happens if I exceed my mobile data limit?",
    answer: "If you exceed your mobile data limit, you'll be charged for additional data usage according to your plan's rates. You can monitor your usage through the SpotOn app or dashboard to avoid unexpected charges. We also send notifications when you're close to your limit."
  },
  {
    question: "How do I transfer my mobile number to SpotOn?",
    answer: "To transfer your mobile number to SpotOn, you'll need your current account number and PIN. Log into your SpotOn account, go to the Mobile section, and select 'Transfer Number'. Follow the prompts to complete the transfer process. The transfer typically takes 1-2 business days."
  }
];
