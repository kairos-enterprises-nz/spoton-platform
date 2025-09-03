import { useEffect, useRef, useState, cloneElement, useCallback } from "react";
import { useLocation } from "react-router-dom"; // ✅ ADDED
import {
  Wifi,
  Globe,
  Signal,
  ChevronDown,
  ChevronUp,
  Menu,
} from "lucide-react";

import { broadbandGeneralTerms } from "./data/BroadbandGeneralTerms";
import { fibrePlanTerms } from "./data/FibrePlanTerms";
import { ruralPlanTerms } from "./data/RuralPlanTerms";
import { wirelessPlanTerms } from "./data/WirelessPlanTerms";
import { fibreDisclosure } from "./data/FibreDisclosure";
import { wirelessDisclosure } from "./data/WirelessDisclosure";
import { ruralDisclosure } from "./data/RuralDisclosure";

const plans = [
  {
    id: "fibre",
    name: "Fibre Broadband",
    summary: "High-speed fibre internet with unlimited data.",
    icon: <Globe className="w-5 h-5 text-primary-turquoise" />,
    content: fibrePlanTerms,
    disclosure: fibreDisclosure,
    updated: "March 2025",
  },
  {
    id: "wireless",
    name: "Fixed Wireless",
    summary: "Reliable wireless connectivity for suburban locations.",
    icon: <Wifi className="w-5 h-5 text-primary-turquoise" />,
    content: wirelessPlanTerms,
    disclosure: wirelessDisclosure,
    updated: "March 2025",
  },
  {
    id: "rural",
    name: "Rural Broadband",
    summary: "Internet access for rural and remote areas.",
    icon: <Signal className="w-5 h-5 text-primary-turquoise" />,
    content: ruralPlanTerms,
    disclosure: ruralDisclosure,
    updated: "March 2025",
  },
];

export default function BroadbandTermsIndex() {
  const location = useLocation(); // ✅ FIXED
  const sectionTopRef = useRef(null);
  
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const [showPlans, setShowPlans] = useState(false);
  const [showGeneral, setShowGeneral] = useState(false);
  const [activeTab, setActiveTab] = useState("terms");
  const [isOpen, setIsOpen] = useState(false);

  const selectedPlan = plans.find((p) => p.id === selectedPlanId);

  // ✅ Move scrollToContent UP
  const scrollToContent = useCallback(() => {
    setTimeout(() => {
      sectionTopRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }, []);

  const handleSelectPlan = useCallback((id) => {
    setSelectedPlanId(id);
    setShowGeneral(false);
    setShowPlans(false);
    setActiveTab("terms");
    setIsOpen(false);
    scrollToContent();
  }, [scrollToContent]);

  const forceShowGeneral = useCallback(() => {
    setShowGeneral(true);
    setShowPlans(false);
    setSelectedPlanId(null);
    setIsOpen(false);
    scrollToContent();
  }, [scrollToContent]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sectionParam = params.get('section');
    const planParam = params.get('plan');

    if (sectionParam === 'general') {
      forceShowGeneral();
    } else if (['fibre', 'wireless', 'rural'].includes(planParam)) {
      handleSelectPlan(planParam);
    }
  }, [location, forceShowGeneral, handleSelectPlan]);

  const sections = showGeneral
    ? broadbandGeneralTerms
    : activeTab === "terms"
    ? selectedPlan?.content || []
    : selectedPlan?.disclosure || [];

  
  return (
    <main className="relative bg-white text-gray-800 scroll-smooth isolate overflow-x-visible">
      <header className={`max-w-5xl mx-auto px-6 ${showGeneral ? "pt-12 pb-6" : "pt-20 pb-12"} text-center`}>
        <h1 className="text-4xl font-extrabold mb-4">Broadband Legals</h1>
        <p className="text-base text-gray-600 max-w-4xl mx-auto">
          Learn about our general broadband terms or explore the specific legal terms of each plan.
        </p>
      </header>

      <div className="sticky top-0 z-30 bg-white max-w-4xl mx-auto pt-4">
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button
            onClick={() => {
              setShowGeneral(!showGeneral);
              setShowPlans(false);
              setSelectedPlanId(null);
              setActiveTab("terms");
              setIsOpen(false);
              scrollToContent();
            }}
            className="bg-white text-secondary-darkgray border border-primary-turquoise hover:bg-secondary-darkgray hover:border-none hover:text-white transition py-3 px-6 rounded-lg text-sm font-semibold shadow"
          >
            {showGeneral ? "Hide General Terms" : "View General Broadband Terms"}
          </button>

          <button
            onClick={() => {
              setShowPlans(!showPlans);
              setShowGeneral(false);
              setSelectedPlanId(null);
              setActiveTab("terms");
              setIsOpen(false);
              scrollToContent();
            }}
            className="border border-gray-300 py-3 px-6 rounded-lg text-sm font-semibold flex items-center gap-2 hover:bg-gray-100 transition shadow"
          >
            {showPlans ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />} Explore Plan Terms
          </button>
        </div>

        {(showGeneral || selectedPlan) && (
          <div className="mt-6 pb-2 border-b border-accent-lightturquoise text-center max-w-4xl">
            <h2 className="text-2xl font-bold text-gray-700 mb-3">
              {showGeneral ? "General Broadband Terms" : `${selectedPlan.name} – Legal`}
            </h2>

            {!showGeneral && (
              <div className="flex justify-center gap-4 mb-4">
                <button
                  className={`px-4 py-1.5 rounded text-sm font-semibold ${
                    activeTab === "terms"
                      ? "bg-primary-turquoise text-white"
                      : "bg-gray-100 text-gray-700"
                  }`}
                  onClick={() => {
                    setActiveTab("terms");
                    setIsOpen(false);
                    scrollToContent();
                  }}
                >
                  Terms
                </button>
                <button
                  className={`px-4 py-1.5 rounded text-sm font-semibold ${
                    activeTab === "disclosure"
                      ? "bg-primary-turquoise text-white"
                      : "bg-gray-100 text-gray-700"
                  }`}
                  onClick={() => {
                    setActiveTab("disclosure");
                    setIsOpen(false);
                    scrollToContent();
                  }}
                >
                  Disclosure
                </button>
              </div>
            )}

            {sections.length > 0 && (
              <div className="mb-4">
                <button
                  onClick={() => setIsOpen(!isOpen)}
                  className="flex items-center gap-2 text-accent-green font-semibold text-sm mx-auto"
                >
                  <Menu className="w-4 h-4" />
                  {isOpen ? "Hide" : "Jump to Section"}
                  {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>
            )}

            {isOpen && (
              <div className="bg-gray-50 shadow rounded border-t border-b border-accent-green w-full sm:max-w-md md:max-w-lg lg:max-w-3/5 xl:max-w-2/5 mx-auto">
                <ul className="px-6 py-4 space-y-2 text-sm">
                  {sections.map((section) => (
                    <li key={section.id}>
                      <a
                        href={`#${section.id}`}
                        onClick={() => setIsOpen(false)}
                        className="flex items-center gap-2 text-gray-700 hover:font-bold"
                      >
                        <span className="text-gray-400">{section.number}.</span>
                        {section.icon &&
                          cloneElement(section.icon, { className: "w-5 h-5 text-accent-purple" })}
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
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl mx-auto mt-6 mb-12">
          {plans.map((plan) => (
            <div
              key={plan.id}
              onClick={() => {
                setSelectedPlanId(plan.id);
                setShowGeneral(false);
                setShowPlans(false);
                setActiveTab("terms");
                scrollToContent();
              }}
              className="cursor-pointer border border-gray-200 p-5 rounded-xl hover:shadow-lg transition group hover:bg-gray-700"
            >
              <div className="flex items-center gap-3 font-semibold text-primary-turquoise group-hover:text-white">
                {plan.icon}
                {plan.name}
              </div>
              <p className="text-sm mt-2 text-start text-gray-600 group-hover:text-white">
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
                {section.icon &&
                  cloneElement(section.icon, {
                    className: "w-5 h-5 text-accent-purple",
                  })}
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
                case "heading":
                  return (
                    <h3
                      key={i}
                      className="text-lg font-semibold text-gray-900 mt-6 mb-2 border-l-4 border-primary-turquoise pl-3"
                    >
                      {block.text}
                    </h3>
                  );
                case "table":
                  return (
                    <div key={i} className="overflow-x-auto mt-4 mb-6 border rounded-md shadow-sm">
                      <table className="min-w-full text-sm text-left text-gray-700 border-collapse">
                        <thead className="bg-gray-100 text-xs uppercase font-semibold">
                          <tr>
                            {block.columns.map((col, idx) => (
                              <th key={idx} className="px-4 py-2 border-b border-gray-200">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {block.rows.map((row, rowIdx) => (
                            <tr key={rowIdx} className="even:bg-white odd:bg-gray-50">
                              {row.map((cell, cellIdx) => (
                                <td key={cellIdx} className="px-4 py-2 border-b border-gray-100">
                                  {cell}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
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
          <p className="text-start">
            Last updated: {showGeneral ? "March 2025" : selectedPlan?.updated || ""}
          </p>
        </footer>
      )}
    </main>
  );
}
