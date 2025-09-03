import { useRef, useState, cloneElement, useCallback } from "react";
import {
  Phone,
  FileText,
  Clock,
  ChevronDown,
  ChevronUp,
  Menu,
  Wifi,
  Shield,
  Battery,
  MapPin,
} from "lucide-react";
import { generalMobileSections } from "./data/GeneralMobileTerms";
import { prepaidPlanTerms } from "./data/PrepaidPlanTerms";
import { postpaidPlanTerms } from "./data/PostpaidPlanTerms";
import { familyPlanTerms } from "./data/FamilyPlanTerms";
import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const plans = [
  {
    id: "prepaid",
    name: "Prepaid",
    summary: "Pay-as-you-go with no lock-in contracts.",
    icon: <Phone className="w-5 h-5 text-primary-turquoise" />,
    content: prepaidPlanTerms,
    updated: "March 2025",
  },
  {
    id: "postpaid",
    name: "Postpaid",
    summary: "Monthly billing with flexible data options.",
    icon: <FileText className="w-5 h-5 text-primary-turquoise" />,
    content: postpaidPlanTerms,
    updated: "April 2025",
  },
  {
    id: "family",
    name: "Family Plan",
    summary: "Shared data and minutes for multiple lines.",
    icon: <Wifi className="w-5 h-5 text-primary-turquoise" />,
    content: familyPlanTerms,
    updated: "April 2025",
  },
];

export default function MobileTermsIndex() {
  const [isOpen, setIsOpen] = useState(false);
  const [showPlans, setShowPlans] = useState(false);
  const [showGeneral, setShowGeneral] = useState(false);
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const sectionTopRef = useRef(null);
  const selectedPlan = plans.find((p) => p.id === selectedPlanId);
  const sections = showGeneral ? generalMobileSections : selectedPlan?.content || [];
  const location = useLocation();

  const scrollToContent = useCallback(() => {
    setTimeout(() => {
      sectionTopRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }, []);

  const scrollToTop = useCallback(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const handleShowGeneral = useCallback(() => {
    setShowGeneral((prev) => {
      const newValue = !prev;
      if (newValue) scrollToContent();
      else scrollToTop();
      return newValue;
    });
    setIsOpen(false);
    setShowPlans(false);
    setSelectedPlanId(null);
  }, [scrollToContent, scrollToTop]);

  const forceShowGeneral = useCallback(() => {
    setShowGeneral(true);
    setShowPlans(false);
    setSelectedPlanId(null);
    setIsOpen(false);
    scrollToContent();
  }, [scrollToContent]);

  const handleSelectPlan = useCallback((id) => {
    setSelectedPlanId(id);
    setShowGeneral(false);
    setShowPlans(false);
    setIsOpen(false);
    scrollToContent();
  }, [scrollToContent]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sectionParam = params.get('section');
    const planParam = params.get('plan');
  
    if (sectionParam === 'general') {
      forceShowGeneral();
    } else if (['prepaid', 'postpaid', 'family'].includes(planParam)) {
      handleSelectPlan(planParam);
    }
  }, [location, forceShowGeneral, handleSelectPlan]);

  return (
    <main className="relative bg-white text-gray-800 scroll-smooth isolate overflow-x-visible">
      <header className="max-w-5xl mx-auto px-6 pt-20 pb-12 text-center relative z-10">
        <h1 className="text-4xl font-extrabold tracking-tight mb-4">Mobile Legals</h1>
        <p className="text-base text-gray-600 max-w-5xl mx-auto">
          Learn about our general mobile terms and conditions or explore the specific legal terms of each available plan.
        </p>
      </header>
      <div className="sticky top-0 z-30 max-w-4xl mx-auto bg-white pt-4">
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button
            onClick={handleShowGeneral}
            className="bg-white text-secondary-darkgray border border-primary-turquoise hover:bg-secondary-darkgray hover:border-none hover:text-white transition py-3 px-6 rounded-lg text-sm font-semibold shadow"
          >
            {showGeneral ? "Hide General Terms" : "View General Mobile Terms"}
          </button>
          <button
            onClick={() => {
              setShowPlans((prev) => !prev);
              setShowGeneral(false);
              setSelectedPlanId(null);
              setIsOpen(false);
              scrollToTop();
            }}
            className="border border-gray-300 py-3 px-6 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 hover:bg-gray-100 transition shadow"
          >
            {showPlans ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />} Explore Plan Terms
          </button>
        </div>
        {(showGeneral || selectedPlan) && (
          <div className="mt-6 pb-2 border-b border-accent-lightturquoise text-center max-w-4xl">
            <h2 className="text-2xl font-bold text-gray-700 mb-3">
              {showGeneral ? "General Mobile Terms" : `${selectedPlan?.name} – Legal Terms`}
            </h2>
            {sections.length > 0 && (
              <div className="mb-1 flex justify-center">
                <button
                  onClick={() => setIsOpen(!isOpen)}
                  className="flex items-center gap-2 text-accent-green font-bold text-sm"
                >
                  <Menu className="w-4 h-4" />
                  {isOpen ? "Hide" : "Jump to Section"}
                  {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>
            )}
            {isOpen && (
              <div className="bg-gray-50 shadow rounded border-t border-b border-accent-green w-full sm:max-w-md md:max-w-lg lg:max-w-3/5 xl:max-w-2/5 mx-auto">
                <ul className="px-6 py-2 space-y-2 text-sm w-full max-w-2xl mx-auto">
                  {sections.map((section) => (
                    <li key={section.id}>
                      <a
                        href={`#${section.id}`}
                        onClick={() => setIsOpen(false)}
                        className="flex items-center gap-2 hover:font-bold text-gray-700"
                      >
                        <span className="text-gray-400">{section.number}.</span>
                        {cloneElement(section.icon, { className: "w-5 h-5 text-accent-purple" })}
                        <span>{section.title}</span>
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
      {showPlans && (
        <section className="mb-12 grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl mx-auto mt-6">
          {plans.map((plan) => (
            <div
              key={plan.id}
              onClick={() => handleSelectPlan(plan.id)}
              className="cursor-pointer border border-gray-200 p-5 rounded-xl hover:shadow-lg transition group hover:bg-gray-700"
            >
              <div className="flex items-center gap-3 font-semibold text-primary-turquoise group-hover:text-white">
                {plan.icon}
                {plan.name}
              </div>
              <p className="text-sm text-start text-gray-600 mt-2 leading-snug group-hover:text-white">
                {plan.summary}
              </p>
            </div>
          ))}
        </section>
      )}
      <div className="relative z-10 max-w-4xl mx-auto px-6 pt-10 pb-24 text-base leading-relaxed space-y-6">
        {sections.map((section, index) => (
          <section
            id={section.id}
            key={section.id}
            ref={index === 0 ? sectionTopRef : null}
            className="scroll-mt-[180px]"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="text-accent-purple">
                {cloneElement(section.icon, { className: "w-5 h-5 text-accent-purple" })}
              </div>
              <h2 className="text-xl font-semibold">
                {section.number}. {section.title}
              </h2>
            </div>
            {section.content.map((block, i) => {
              switch (block.type) {
                case "paragraph":
                  return (
                    <p key={i} className="mb-4 text-sm text-start">
                      {block.text}
                    </p>
                  );
                case "list":
                  return (
                    <ul
                      key={i}
                      className="list-disc list-inside mt-2 text-sm text-start text-gray-700 space-y-1"
                    >
                      {block.items.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  );
                case "callout":
                  return (
                    <div
                      key={i}
                      className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 p-2 text-sm text-start text-yellow-800 rounded"
                    >
                      {block.icon}
                      {block.text}
                    </div>
                  );
                default:
                  return null;
              }
            })}
          </section>
        ))}
      </div>
      {sections.length > 0 && (
        <footer className="p-2 border border-accent-lightturquoise max-w-4xl mx-auto text-xs text-gray-500">
          <p className="max-w-4xl mx-auto text-start">
            Last updated: {showGeneral ? "April 2025" : selectedPlan?.updated || ""}
          </p>
        </footer>
      )}
    </main>
  );
} 