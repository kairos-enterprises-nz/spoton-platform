import {
  Wifi,
  Zap,
  MonitorCheck,
  SlidersHorizontal,
  Server,
  Cpu,
  Power,
  AlertTriangle,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';

export const technicalCategories = [
  "All",
  "Power",
  "Broadband",
  "Mobile",
  "Dashboard",
  "Settings"
];

export const technicalFaqs = [
  {
    category: "Broadband",
    icon: Wifi,
    title: "My internet is slow — what should I check first?",
    content: [
      { type: "paragraph", text: "Check if it's a device-specific issue, and reboot your router. You can also use our speed test from the dashboard." },
      { type: "link", href: "/dashboard/speed-test", text: "Run a Speed Test →" }
    ]
  },
  {
    category: "Broadband",
    icon: Wifi,
    title: "What does the WAN light on my router mean?",
    content: [
      { type: "paragraph", text: "The WAN light indicates your router's connection to the internet. If it's off or red, there may be a line issue." },
      { type: "list", items: [
        "Green or white: online",
        "Blinking: syncing",
        "Red or off: line problem or no connection"
      ] }
    ]
  },
  {
    category: "Broadband",
    icon: Server,
    title: "Why is my connection dropping intermittently?",
    content: [
      { type: "paragraph", text: "This could be due to signal interference, firmware issues, or line quality. Check router placement and updates first." },
      { type: "link", href: "/support/internet-troubleshooting", text: "Read More on Fixes →" }
    ]
  },
  {
    category: "Power",
    icon: Zap,
    title: "What should I do during a power outage?",
    content: [
      { type: "paragraph", text: "Check your local outage map or contact us to see if it's a scheduled interruption. Never attempt to fix lines yourself." },
      { type: "link", href: "/support/contact", text: "Contact Support →" }
    ]
  },
  {
    category: "Power",
    icon: Power,
    title: "How do I report a power fault?",
    content: [
      { type: "paragraph", text: "Use your dashboard's 'Outage' tab to log an issue or call our support line. We'll check your ICP and escalate to the network provider if needed." }
    ]
  },
  {
    category: "Dashboard",
    icon: MonitorCheck,
    title: "How can I track my usage?",
    content: [
      { type: "paragraph", text: "Log into your SpotOn dashboard and navigate to the 'Usage' tab to see your daily, weekly, or monthly consumption." },
      { type: "image", src: "/images/usage-graph-example.png", alt: "Usage graph screenshot" }
    ]
  },
  {
    category: "Dashboard",
    icon: Cpu,
    title: "Is my usage data live or delayed?",
    content: [
      { type: "paragraph", text: "Usage data updates every 2–4 hours. Real-time monitoring is in beta for selected plans." },
      { type: "table", headers: ["Data Type", "Delay"], rows: [
        ["Electricity", "Up to 4 hours"],
        ["Broadband", "Up to 2 hours"],
        ["Combined dashboard", "Near real-time"]
      ]}
    ]
  },
  {
    category: "Settings",
    icon: SlidersHorizontal,
    title: "How do I reset my password?",
    content: [
      { type: "paragraph", text: "Click 'Forgot Password' on the login page, or change your password from your dashboard settings under Account > Security." },
      { type: "list", items: [
        "Click your avatar in the top right",
        "Go to Account Settings",
        "Select 'Security' tab"
      ]}
    ]
  },
  {
    category: "Settings",
    icon: SlidersHorizontal,
    title: "Can I update my contact preferences?",
    content: [
      { type: "paragraph", text: "Yes — go to Settings > Notifications to update how and when we contact you." },
      { type: "link", href: "/account/settings/notifications", text: "Manage Preferences →" }
    ]
  },
  {
    category: "Broadband",
    icon: RefreshCw,
    title: "Should I restart my modem regularly?",
    content: [
      { type: "paragraph", text: "It's a good idea to restart your modem/router every few weeks to refresh your connection and apply any firmware updates." }
    ]
  },
  {
    category: "Power",
    icon: AlertTriangle,
    title: "How do I know if an outage is affecting my area?",
    content: [
      { type: "paragraph", text: "We'll notify you in the dashboard if your ICP is affected. You can also check the network operator's website for live updates." }
    ]
  },
  {
    category: "Dashboard",
    icon: ShieldCheck,
    title: "Can I export my usage data?",
    content: [
      { type: "paragraph", text: "Yes — you can export your usage records as CSV or PDF from your dashboard's 'Usage History' section." }
    ]
  },
  {
    category: "Mobile",
    icon: Wifi,
    question: "How do I troubleshoot mobile network connectivity issues?",
    answer: "If you're experiencing mobile network issues, try these steps: 1) Check if your device is in airplane mode, 2) Restart your device, 3) Check if you're in a coverage area, 4) Update your device's software, 5) Reset your network settings. If problems persist, contact our technical support team."
  },
  {
    category: "Mobile",
    icon: Wifi,
    question: "Why is my mobile data speed slow?",
    answer: "Slow mobile data speeds can be caused by: 1) Network congestion in your area, 2) Distance from the nearest cell tower, 3) Physical obstacles blocking the signal, 4) Device settings or software issues. Try moving to a different location or restarting your device. If the issue continues, contact our support team."
  },
  {
    category: "Mobile",
    icon: Wifi,
    question: "How do I set up mobile hotspot on my device?",
    answer: "To set up a mobile hotspot: 1) Go to your device's settings, 2) Find 'Hotspot' or 'Tethering' settings, 3) Enable the hotspot, 4) Set a secure password, 5) Connect other devices using the provided network name and password. Note that using hotspot may count against your data allowance."
  }
];
