import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import BreadcrumbNav from '../components/BreadcrumbNav';
import { generalFaqs, faqCategories } from '../data/generalFaqData';

export default function GeneralSupport() {
  const [openIndex, setOpenIndex] = useState(null);
  const [activeCategory, setActiveCategory] = useState("All");
  const [query, setQuery] = useState('');

  // Scroll to anchor with smooth scrolling and reset state if needed
  useEffect(() => {
    const anchor = location.hash?.replace('#', '');
    const index = generalFaqs.findIndex(faq => {
      const anchorTitle = faq.title?.toLowerCase().replace(/[^a-z0-9]+/g, '-');
      const anchorQuestion = faq.question?.toLowerCase().replace(/[^a-z0-9]+/g, '-');
      return anchorTitle === anchor || anchorQuestion === anchor;
    });
    if (index !== -1) {
      setOpenIndex(index);
      setTimeout(() => {
        const targetElement = document.getElementById(anchor);
        if (targetElement) {
          const yOffset = -70;
          const y = targetElement.getBoundingClientRect().top + window.pageYOffset + yOffset;
          window.scrollTo({ top: y, behavior: 'smooth' });
        }
      }, 500);
    }
  }, []);

  const toggleFaq = (index) => {
    setOpenIndex(index === openIndex ? null : index);
  };

  const filteredFaqs = generalFaqs.filter(faq =>
    (faq.title && faq.title.toLowerCase().includes(query.toLowerCase())) ||
    (faq.question && faq.question.toLowerCase().includes(query.toLowerCase())) ||
    (faq.content && faq.content.some(block => block.text?.toLowerCase().includes(query.toLowerCase()))) ||
    (faq.answer && faq.answer.toLowerCase().includes(query.toLowerCase()))
  );

  return (
    <div className="bg-white min-h-screen">
      {/* === HERO === */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-teal-900 px-4 sm:px-6 pt-16 pb-8 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-white mb-4">General FAQs</h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Quick answers to the most common questions about SpotOn's services.
          </p>
        </div>
        <BreadcrumbNav
          path={[
            { label: 'Support', to: '/support' },
            { label: 'General FAQs' },
          ]}
        />
      </section>

      {/* === FILTER TABS === */}
      <div className="sticky top-0 bg-white border-b border-gray-200 z-10 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto py-3 flex flex-wrap gap-2 justify-start sm:justify-center">
          {faqCategories.map((cat, i) => {
            const matchedIcon = generalFaqs.find(f => f.category === cat && f.icon)?.icon;
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
                  setOpenIndex(null); // Reset openIndex when changing category
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
          const anchorId = faq.title?.toLowerCase().replace(/[^a-z0-9]+/g, '-') || faq.question?.toLowerCase().replace(/[^a-z0-9]+/g, '-');
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
                <h2 className="text-sm sm:text-lg font-medium text-gray-900">{faq.title || faq.question}</h2>
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
                  {faq.content
                    ? faq.content.map((block, i) => {
                      switch (block.type) {
                        case 'paragraph':
                          return <p key={i}>{block.text}</p>;
                        case 'link':
                          return (
                            <a
                              key={i}
                              href={block.href}
                              className="text-primary-turquoise hover:underline inline-block"
                            >
                              {block.text}
                            </a>
                          );
                        case 'list':
                          return (
                            <ul key={i} className="list-disc pl-5 space-y-1">
                              {block.items.map((item, li) => <li key={li}>{item}</li>)}
                            </ul>
                          );
                        case 'table':
                          return (
                            <div key={i} className="overflow-x-auto">
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
                              key={i}
                              src={block.src}
                              alt={block.alt}
                              className="rounded-md border max-w-full mt-2"
                            />
                          );
                        default:
                          return null;
                      }
                    })
                    : <p>{faq.answer}</p>
                  }
                </div>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}
