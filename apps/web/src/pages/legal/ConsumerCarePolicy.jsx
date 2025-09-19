import {
  ChevronDown,
  ChevronUp,
  Menu,
} from "lucide-react";
import React, { useEffect, useState, useRef } from "react";
import { consumerCareSections } from "./data/ConsumerCarePolicy.jsx";

export default function ConsumerCarePolicy() {
  const [isOpen, setIsOpen] = useState(false);
  const [isStickyVisible, setIsStickyVisible] = useState(false);
  const topRef = useRef(null);
  const sections = consumerCareSections;

  useEffect(() => {
    const target = topRef.current;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsStickyVisible(!entry.isIntersecting);
      },
      { threshold: 0.01 }
    );

    if (target) observer.observe(target);

    return () => {
      if (target) observer.unobserve(target);
    };
  }, []);

  const handleJumpTo = () => {
    setIsOpen((prev) => !prev);
  };

  return (
    <main className="relative text-gray-800 scroll-smooth isolate overflow-x-visible">
      {/* === TOP MARKER === */}
      <div
        ref={topRef}
        className="absolute top-[120px] h-1 w-full"
        aria-hidden="true"
      />

      {/* === PAGE HEADER === */}
      <header className="max-w-5xl mx-auto px-6 pt-20 pb-6 text-center relative z-10">
        <h1 className="text-4xl font-extrabold tracking-tight mb-2">Consumer Care Policy</h1>
        <p className="text-base text-gray-600 max-w-4xl mx-auto">
          This policy outlines how SpotOn supports customers, handles complaints, and ensures fair access to utility services.
        </p>
        <div className="mt-6">
          <button
            onClick={handleJumpTo}
            className="flex items-center gap-2 text-accent-green font-bold text-sm mx-auto"
          >
            <Menu className="w-4 h-4" />
            {isOpen ? "Hide" : "Jump to Section"}
            {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* === STICKY HEADER (border hides when isOpen) === */}
      {isStickyVisible && (
        <div
          className={`fixed top-0 inset-x-0 z-30 max-w-4xl mx-auto bg-white transition-all duration-300 ${
            isOpen ? "border-b-transparent" : "border-b border-accent-lightturquoise"
          }`}
        >
          <div className="max-w-4xl mx-auto px-6 py-4 text-center">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Consumer Care Policy</h2>
            <button
              onClick={handleJumpTo}
              className="flex items-center gap-2 text-accent-green font-bold text-sm mx-auto"
            >
              <Menu className="w-4 h-4" />
              {isOpen ? "Hide" : "Jump to Section"}
              {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>
      )}

      {/* === DROPDOWN under top header === */}
      {isOpen && !isStickyVisible && (
        <div className="max-w-4xl mx-auto py-2 border-accent-lightturquoise bg-white border-b">
<ul className="max-w-full sm:max-w-md md:max-w-lg lg:max-w-2xl xl:max-w-2/5 bg-gray-50 shadow mx-auto px-6 py-3 space-y-2 text-sm border-t border-b rounded border-accent-green">
{sections.map((section) => (
              <li key={section.id}>
                <a
                  href={`#${section.id}`}
                  onClick={() => setIsOpen(false)}
                  className="flex items-center gap-2 hover:font-bold text-gray-700"
                >
                  <span className="text-gray-400">{section.number}.</span>
                  {section.icon &&
                    React.cloneElement(section.icon, {
                      className: "w-4 h-4 text-accent-purple",
                    })}
                  <span>{section.title}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* === DROPDOWN under sticky header === */}
      {isOpen && isStickyVisible && (
        <div className="fixed top-[92px] inset-x-0 z-20 max-w-4xl mx-auto border-b border-accent-lightturquoise border-t border-t-accent-green py-2 bg-white">
<ul className="max-w-full sm:max-w-md md:max-w-lg lg:max-w-xl xl:max-w-2/5 mx-auto px-6 py-3 space-y-2 bg-gray-50 text-sm shadow border-t border-b rounded border-accent-green">
            {sections.map((section) => (
              <li key={section.id}>
                <a
                  href={`#${section.id}`}
                  onClick={() => setIsOpen(false)}
                  className="flex items-center gap-2 hover:font-bold text-gray-700"
                >
                  <span className="text-gray-400">{section.number}.</span>
                  {section.icon &&
                    React.cloneElement(section.icon, {
                      className: "w-4 h-4 text-accent-purple",
                    })}
                  <span>{section.title}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* === MAIN SECTION === */}
      <div className="relative z-10 max-w-4xl mx-auto px-6 py-6 pb-24 space-y-10 text-base leading-relaxed">
        {sections.map((section) => (
          <section id={section.id} key={section.id} className="scroll-mt-[120px]">
            <div className="flex items-center gap-3 mb-4">
              <div className="text-accent-purple">
                {section.icon &&
                  React.cloneElement(section.icon, {
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
                default:
                  return null;
              }
            })}
          </section>
        ))}
      </div>

      {/* === FOOTER === */}
      <footer className="p-2 border border-accent-lightturquoise max-w-4xl mx-auto text-xs text-gray-500">
        <p className="text-start">Last updated: April 2025.</p>
      </footer>
    </main>
  );
}
