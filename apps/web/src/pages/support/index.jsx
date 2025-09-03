import { useState } from 'react';
import { ChatBubbleLeftRightIcon, QuestionMarkCircleIcon, CurrencyDollarIcon, Cog6ToothIcon } from '@heroicons/react/24/solid';
import { SearchIcon } from 'lucide-react';
import { generalFaqs } from './data/generalFaqData';
import { billingFaqs } from './data/billingFaqData';
import { technicalFaqs } from './data/technicalFaqData';
import { useLoader } from '../../context/LoaderContext';
import Loader from '../../components/Loader';
import { useNavigate, useLocation } from 'react-router-dom';

const helpTopics = [
  {
    icon: <QuestionMarkCircleIcon className="h-10 w-10 text-primary-turquoise" />,
    title: 'General FAQs',
    description: 'Answers to common questions about our services and policies.',
    link: '/support/general',
  },
  {
    icon: <CurrencyDollarIcon className="h-10 w-10 text-primary-turquoise" />,
    title: 'Billing & Payments',
    description: 'Understanding your bill, payment methods, and due dates.',
    link: '/support/billing',
  },
  {
    icon: <Cog6ToothIcon className="h-10 w-10 text-primary-turquoise" />,
    title: 'Technical Support',
    description: 'Troubleshooting broadband issues and using your dashboard.',
    link: '/support/technical',
  },
  {
    icon: <ChatBubbleLeftRightIcon className="h-10 w-10 text-primary-turquoise" />,
    title: 'Contact Us',
    description: "Need to talk to someone? We're just a message away.",
    link: '/support/contact',
  },
];

export default function SupportIndex() {
  const [query, setQuery] = useState('');
  const { loading, setLoading } = useLoader();
  const navigate = useNavigate();
  const location = useLocation();

  const allFaqs = [
    ...generalFaqs.map(faq => ({ ...faq, source: 'general' })),
    ...billingFaqs.map(faq => ({ ...faq, source: 'billing' })),
    // Include only broadband/internet technical FAQs, exclude Power and Mobile
    ...technicalFaqs
      .filter(faq => !['Power', 'Mobile'].includes(faq.category))
      .map(faq => ({ ...faq, source: 'technical' })),
  ];

  const searchResults = allFaqs.filter(faq => {
    const searchText = query.toLowerCase();
    // Handle both old and new FAQ structures
    if (faq.title) {
      // Old structure
      return faq.title.toLowerCase().includes(searchText) ||
        faq.content?.some(block => block.text?.toLowerCase().includes(searchText));
    } else if (faq.question) {
      // New structure
      return faq.question.toLowerCase().includes(searchText) ||
        faq.answer?.toLowerCase().includes(searchText);
    }
    return false;
  }).slice(0, 5);

  // Handle the navigation and scroll logic for both search results and Popular Topics links
  const handleNavigate = (path) => {
    const [targetPath, hash] = path.split('#');
    const currentPath = location.pathname;
  
    setLoading(true); // Start loading
  
    // Delay the navigation and loader visibility
    setTimeout(() => {
      if (currentPath === targetPath && hash) {
        // Scroll to the anchor directly on the current page
        const anchor = hash.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, ''); // Clean anchor
        const el = document.getElementById(anchor);
        if (el) {
          const yOffset = -70;
          const y = el.getBoundingClientRect().top + window.pageYOffset + yOffset;
          window.scrollTo({ top: y, behavior: 'smooth' });
  
          el.classList.add('ring', 'ring-primary-turquoise', 'ring-offset-2');
          setTimeout(() => el.classList.remove('ring', 'ring-primary-turquoise', 'ring-offset-2'), 5000);
        }
      } else {
        navigate(path); // Navigate to the path if it's not the same page
      }
    }, 600); // Delay of 600ms
  
    // Stop loading after 1 second (to ensure loader stays visible)
    setTimeout(() => setLoading(false), 1000);  // 1000ms = 1 second
  };
  

  return (
    <div className="bg-white min-h-screen">
      {loading && <Loader fullscreen size="xl" />}

      {/* HERO */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-teal-900 py-20 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">Support Center</h1>
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Find answers, troubleshoot issues, or get in touch — we're here to help.
          </p>

          <div className="mt-8 flex justify-center">
            <div className="relative w-full max-w-xl">
              <label htmlFor="support-search" className="sr-only">Search help topics</label>
              <input
                id="support-search"
                type="text"
                placeholder="Search for topics, FAQs, or help..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-white placeholder-gray-300 px-6 py-4 pr-12 shadow-lg focus:outline-none focus:ring-2 focus:ring-purple-500/60 focus:border-transparent transition-all"
              />
              <SearchIcon className="absolute right-4 top-4.5 h-5 w-5 text-gray-300" />
            </div>
          </div>
        </div>
      </section>

      {/* SEARCH RESULTS */}
      {query && (
        <section className="px-6 py-12 bg-white max-w-6xl mx-auto">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Search Results</h2>
          {searchResults.length === 0 ? (
            <p className="text-sm text-gray-600">No matching results found.</p>
          ) : (
            <ul className="space-y-4">
              {searchResults.map((faq, idx) => {
                const basePath = faq.source ? `/support/${faq.source}` : '/support/general';
                const anchor = (faq.title || faq.question).toLowerCase().replace(/[^a-z0-9]+/g, '-');
                return (
                  <li
                    key={idx}
                    onClick={() => handleNavigate(`${basePath}#${anchor}`)}
                    className="block border border-gray-200 rounded-lg p-4 hover:shadow cursor-pointer transition"
                  >
                    <h3 className="text-base font-semibold text-primary-turquoise mb-1 line-clamp-1">
                      {faq.title || faq.question}
                    </h3>
                    <p className="text-sm text-gray-700 line-clamp-2">
                      {faq.content?.find(c => c.text)?.text || faq.answer || ''}
                    </p>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      )}

      {/* BROWSE HELP TOPICS */}
      <section className="py-20 px-6 bg-gradient-to-br from-slate-50 via-white to-teal-50/30">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">Browse Help Topics</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {helpTopics.map((item, idx) => (
              <div
                key={idx}
                onClick={() => handleNavigate(item.link)}
                className="group rounded-2xl border border-slate-200/80 bg-white p-6 hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer"
              >
                <div className="text-center">
                  <div className="flex justify-center mb-4">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-teal-500 to-slate-600 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <div className="text-white [&>svg]:w-6 [&>svg]:h-6">
                        {item.icon}
                      </div>
                    </div>
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 group-hover:text-teal-600 mb-2">
                    {item.title}
                  </h3>
                  <p className="text-sm text-slate-600">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>


{/* FEATURED ARTICLES */}
<section className="py-20 px-6 bg-gray-50/80">
  <div className="max-w-6xl mx-auto">
    <h2 className="text-2xl font-bold text-accent-green text-center mb-12 uppercase tracking-wide">Popular Topics</h2>
    <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
      {[{
        title: 'How do I read my bill?',
        description: 'Learn to understand your bill breakdown and charges by section.',
        link: '/support/billing#how-do-i-read-my-bill-',
      },
      {
        title: 'How to change your plan?',
        description: 'Switch between broadband plans — it only takes a minute.',
        link: '/support/general#how-do-i-change-my-plan-', 
      },
      {
        title: 'Where do I update my payment method?',
        description: 'Keep your payment info current through your dashboard settings.',
        link: '/support/billing#where-do-i-update-my-payment-method-',
      },
      {
        title: 'How do I contact support?',
        description: 'Get help through chat, email, or request a callback from our team.',
        link: '/support/contact',
      }].map((article, idx) => (
        <div
          key={idx}
          onClick={() => handleNavigate(article.link)}
          className="bg-white p-6 rounded-xl border border-gray-200 hover:shadow-lg transition duration-200 cursor-pointer"
        >
          <h3 className="text-lg font-bold text-gray-900">{article.title}</h3>
          <p className="mt-2 text-sm text-gray-600">{article.description}</p>
          <p className="mt-3 text-sm text-accent-blue hover:underline">Learn more →</p>
        </div>
      ))}
    </div>
  </div>
</section>

      {/* CONTACT CTA */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-teal-900 py-20 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Still need help?</h2>
          <p className="text-xl text-slate-300 mb-8">
            Our support team is ready — chat, email, or request a callback.
          </p>
          <button
            onClick={() => handleNavigate('/support/contact')}
            className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-teal-500 to-slate-600 hover:from-teal-400 hover:to-slate-500 text-white font-bold text-lg rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl hover:ring-2 hover:ring-teal-400/60 hover:ring-offset-2 hover:ring-offset-slate-800"
          >
            Contact Support
          </button>
        </div>
      </section>
    </div>
  );
}
