import {
  CreditCard,
  ReceiptText,
  CalendarCheck2,
  AlertCircle,
  Banknote,
  Download,
  HelpCircle,
  BadgeDollarSign,
  Timer,
} from 'lucide-react';

export const billingCategories = [
  "All",
  "Invoices",
  "Payments",
  "Due Dates",
  "Account Issues"
];

export const billingFaqs = [
  {
    category: "Invoices",
    icon: ReceiptText,
    title: "How do I read my bill?",
    content: [
      { type: "paragraph", text: "Each section of your bill outlines different charges including energy usage, fixed fees, and applicable taxes." },
      { type: "image", src: "/images/sample-invoice-breakdown.png", alt: "Annotated bill explaining each line item" }
    ]
  },
  {
    category: "Invoices",
    icon: ReceiptText,
    title: "How do I view my invoices?",
    content: [
      { type: "paragraph", text: "You can view all your past and current invoices from the 'Billing' section in your SpotOn dashboard." },
      { type: "link", href: "/account/billing", text: "Go to Billing →" }
    ]
  },
  {
    category: "Invoices",
    icon: Download,
    title: "How do I download or print my invoice?",
    content: [
      { type: "paragraph", text: "Every invoice has a download option. Just click the 'Download PDF' button on your invoice page." },
      { type: "image", src: "/images/invoice-download-icon.png", alt: "PDF download icon location" }
    ]
  },
  {
    category: "Payments",
    icon: CreditCard,
    title: "What payment methods are accepted?",
    content: [
      { type: "paragraph", text: "We accept all major credit/debit cards, bank transfers, and direct debit. You can manage your preferred method in the payment settings." },
      { type: "list", items: [
        "Visa / Mastercard",
        "Direct Debit",
        "Bank Transfer (New Zealand only)"
      ]}
    ]
  },
  {
    category: "Payments",
    icon: CreditCard,
    title: "Can I set up automatic payments?",
    content: [
      { type: "paragraph", text: "Yes. You can enable AutoPay to ensure your bill is paid automatically before the due date each month." },
      { type: "link", href: "/account/autopay", text: "Set up AutoPay →" }
    ]
  },
  {
    category: "Payments",
    icon: Banknote,
    title: "Where do I update my payment method?",
    content: [
      { type: "paragraph", text: "Login to your dashboard, go to the 'Payment Settings' section, and update your credit card or bank account." },
      { type: "link", href: "/account/payment-settings", text: "Update Payment Info →" }
    ]
  },
  {
    category: "Due Dates",
    icon: CalendarCheck2,
    title: "When is my bill due?",
    content: [
      { type: "paragraph", text: "Your bill is typically due 14 days after it's issued. You can find the exact due date on your invoice." },
      { type: "image", src: "/images/sample-invoice-due-date.png", alt: "Example highlighting due date on invoice" }
    ]
  },
  {
    category: "Due Dates",
    icon: Timer,
    title: "Can I get a payment extension?",
    content: [
      { type: "paragraph", text: "Yes — if you need more time to pay, you can request a payment extension from your dashboard or by contacting support." },
      { type: "link", href: "/support/contact", text: "Request Extension →" }
    ]
  },
  {
    category: "Account Issues",
    icon: AlertCircle,
    title: "Why is my bill higher this month?",
    content: [
      { type: "paragraph", text: "There could be several reasons: increased usage, end of a promotional period, or one-off charges." },
      { type: "table", headers: ["Possible Reason", "Details"], rows: [
        ["Increased Usage", "Usage spike during holidays or seasonal changes."],
        ["Plan Expiry", "You may have moved from a promo to standard rate."],
        ["One-off Charges", "Additional service, missed payment fee, or equipment costs."]
      ]}
    ]
  },
  {
    category: "Account Issues",
    icon: HelpCircle,
    title: "I paid, but it's not showing. What should I do?",
    content: [
      { type: "paragraph", text: "Payments can take up to 24 hours to reflect. If it's been longer, please reach out with your payment reference." },
      { type: "link", href: "/support/contact", text: "Contact Support →" }
    ]
  },
  {
    category: "Account Issues",
    icon: BadgeDollarSign,
    title: "Can I get a refund or bill adjustment?",
    content: [
      { type: "paragraph", text: "If you're eligible for a refund or were overcharged, our billing team will review your account and process adjustments accordingly." },
      { type: "link", href: "/support/contact", text: "Request Review →" }
    ]
  }
];
