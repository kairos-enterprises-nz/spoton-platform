import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { mobileFaqData } from '../data/mobileFaqData';
import BreadcrumbNav from '../components/BreadcrumbNav';
import SearchBar from '../components/SearchBar';

export default function MobileSupport() {
  const [expandedFaq, setExpandedFaq] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const toggleFaq = (index) => {
    setExpandedFaq(expandedFaq === index ? null : index);
  };

  const filteredFaqs = mobileFaqData.filter(
    (faq) =>
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <main className="max-w-4xl mx-auto px-6 py-8">
      <BreadcrumbNav path={['Support', 'Mobile']} />
      
      <div className="mt-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Mobile Support</h1>
        <p className="text-gray-600 mb-8">
          Find answers to common questions about your mobile service, including data usage, coverage, and account management.
        </p>

        <SearchBar onSearch={setSearchQuery} />

        <div className="mt-8 space-y-4">
          {filteredFaqs.map((faq, index) => (
            <div
              key={index}
              className="border border-gray-200 rounded-lg overflow-hidden"
            >
              <button
                className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-50"
                onClick={() => toggleFaq(index)}
              >
                <span className="font-semibold text-gray-900">{faq.question}</span>
                {expandedFaq === index ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>
              {expandedFaq === index && (
                <div className="px-6 py-4 bg-gray-50">
                  <p className="text-gray-600">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-12 p-6 bg-gray-50 rounded-lg">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Need More Help?</h2>
          <p className="text-gray-600 mb-4">
            If you couldn't find the answer you're looking for, our support team is here to help.
          </p>
          <div className="space-y-2">
            <p className="text-gray-600">
              <strong>Phone:</strong> 0800 SPOTON (Mon–Fri, 8am–6pm)
            </p>
            <p className="text-gray-600">
              <strong>Email:</strong> mobile.support@spoton.co.nz
            </p>
            <p className="text-gray-600">
              <strong>Live Chat:</strong> Available on our website and mobile app
            </p>
          </div>
        </div>
      </div>
    </main>
  );
} 