// pages/support/BillingSupport.jsx
import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ChevronDown, ChevronUp } from 'lucide-react';
import BreadcrumbNav from '../components/BreadcrumbNav';
import { billingFaqs, billingCategories } from '../data/billingFaqData';

export default function BillingSupport() {
  const [openIndex, setOpenIndex] = useState(null);
  const [activeCategory, setActiveCategory] = useState("All");
  const location = useLocation();

  useEffect(() => {
    const anchor = location.hash?.replace('#', '');
    const index = billingFaqs.findIndex(faq =>
      faq.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') === anchor
    );
    if (index !== -1) {
      setOpenIndex(index);
      setTimeout(() => {
        const targetElement = document.getElementById(anchor);
        if (targetElement) {
          const yOffset = -70;
          const y = targetElement.getBoundingClientRect().top + window.pageYOffset + yOffset;
          window.scrollTo({ top: y, behavior: 'smooth' });
        }
      }, 100);
    }
  }, [location]);

  const toggleFaq = (index) => {
    setOpenIndex(index === openIndex ? null : index);
  };

  const filteredFaqs = activeCategory === "All"
    ? billingFaqs
    : billingFaqs.filter(faq => faq.category === activeCategory);

  return (
    <div className="bg-white min-h-screen">
      {/* === HERO === */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-teal-900 px-4 sm:px-6 pt-16 pb-8 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-white mb-4">Billing & Payments</h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Understand your bill, payment options, due dates, and more.
          </p>
        </div>
        <BreadcrumbNav
          path={[
            { label: 'Support', to: '/support' },
            { label: 'Billing & Payments' },
          ]}
        />
      </section>

      {/* === FILTER TABS === */}
      <div className="sticky top-0 bg-white border-b border-gray-200 z-10 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto py-3 flex flex-wrap gap-2 justify-start sm:justify-center">
          {billingCategories.map((cat, i) => {
            const matchedIcon = billingFaqs.find(f => f.category === cat && f.icon)?.icon;
            const Icon = matchedIcon || null;

            return (
              <button
                key={i}
                className={`px-3 py-2 rounded-full text-sm font-medium border flex items-center gap-1 ${
                  activeCategory === cat
                    ? 'bg-primary-turquoise text-white border-primary-turquoise'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-gray-300'
                } transition duration-150`}
                onClick={() => {
                  setActiveCategory(cat);
                  setOpenIndex(null);
                }}
              >
                {Icon && <Icon className="h-4 w-4" />}
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* === FAQ ACCORDION === */}
      <section className="px-4 sm:px-6 py-14 max-w-4xl mx-auto space-y-3">
        {filteredFaqs.length === 0 && (
          <p className="text-left text-gray-500 text-sm">No FAQs available under this category.</p>
        )}
        {filteredFaqs.map((faq, idx) => {
          const Icon = faq.icon;
          const anchorId = faq.title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
          return (
            <div
              key={idx}
              id={anchorId}
              className="rounded-md border border-gray-200 transition hover:shadow-sm"
            >
              <button
                className="w-full flex justify-between items-center text-left px-4 py-3 bg-white hover:bg-gray-50 focus:outline-none"
                onClick={() => toggleFaq(idx)}
              >
                <h2 className="text-sm sm:text-lg font-medium text-gray-900">{faq.title}</h2>
                <div className="flex items-center gap-1 ml-2">
                  {Icon && <Icon className="h-4 w-4 text-gray-500" />}
                  <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full whitespace-nowrap">
                    {faq.category}
                  </span>
                  {openIndex === idx
                    ? <ChevronUp className="h-4 w-4 text-gray-500 ml-2" />
                    : <ChevronDown className="h-4 w-4 text-gray-500 ml-2" />
                  }
                </div>
              </button>

              {openIndex === idx && (
                <div className="px-4 py-4 text-sm sm:text-base text-gray-700 space-y-4 text-left">
                  {faq.content.map((block, bi) => {
                    switch (block.type) {
                      case 'paragraph':
                        return <p key={bi}>{block.text}</p>;
                      case 'link':
                        return (
                          <a
                            key={bi}
                            href={block.href}
                            className="text-primary-turquoise hover:underline inline-block"
                          >
                            {block.text}
                          </a>
                        );
                      case 'list':
                        return (
                          <ul key={bi} className="list-disc pl-5 space-y-1">
                            {block.items.map((item, li) => <li key={li}>{item}</li>)}
                          </ul>
                        );
                      case 'table':
                        return (
                          <div key={bi} className="overflow-x-auto">
                            <table className="w-full border mt-2 text-sm text-left">
                              <thead>
                                <tr className="bg-gray-100">
                                  {block.headers.map((h, hi) => (
                                    <th key={hi} className="border px-2 py-1">{h}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {block.rows.map((row, ri) => (
                                  <tr key={ri}>
                                    {row.map((cell, ci) => (
                                      <td key={ci} className="border px-2 py-1">{cell}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        );
                      case 'image':
                        return (
                          <img
                            key={bi}
                            src={block.src}
                            alt={block.alt}
                            className="rounded-md border max-w-full mt-2"
                          />
                        );
                      default:
                        return null;
                    }
                  })}
                </div>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}
