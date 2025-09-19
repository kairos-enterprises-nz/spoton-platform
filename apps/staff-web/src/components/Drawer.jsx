import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';

export default function Drawer({ isOpen, onClose, title, children, footer, widthClass = 'max-w-xs w-80' }) {
  useEffect(() => {
    if (!isOpen) return;
    const htmlEl = document.documentElement;
    const bodyEl = document.body;
    const prevHtmlPadding = htmlEl.style.paddingRight;
    const prevBodyPadding = bodyEl.style.paddingRight;
    const prevHtmlOverflow = htmlEl.style.overflow;

    htmlEl.style.paddingRight = '0px';
    bodyEl.style.paddingRight = '0px';
    htmlEl.style.overflow = 'hidden';

    return () => {
      htmlEl.style.paddingRight = prevHtmlPadding;
      bodyEl.style.paddingRight = prevBodyPadding;
      htmlEl.style.overflow = prevHtmlOverflow;
    };
  }, [isOpen]);

  return (
    <Transition show={isOpen} as={React.Fragment}>
      <Dialog as="div" className="fixed inset-0 z-50" onClose={onClose}>
        <Transition.Child
          as={React.Fragment}
          enter="ease-out duration-200" enterFrom="opacity-0" enterTo="opacity-100"
          leave="ease-in duration-150" leaveFrom="opacity-100" leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/40" />
        </Transition.Child>

        <div className="fixed inset-0">
          <div className="absolute inset-0">
            <div className="pointer-events-none fixed inset-y-0 left-0 flex">
              <Transition.Child
                as={React.Fragment}
                enter="transform transition ease-in-out duration-200"
                enterFrom="-translate-x-full" enterTo="translate-x-0"
                leave="transform transition ease-in-out duration-200"
                leaveFrom="translate-x-0" leaveTo="-translate-x-full"
              >
                <Dialog.Panel className={`pointer-events-auto ${widthClass} bg-white shadow-xl flex flex-col`}>
                  <div className="flex items-center justify-between px-4 py-3 border-b">
                    <Dialog.Title className="text-sm font-semibold text-gray-900">{title}</Dialog.Title>
                    <button onClick={onClose} className="p-1 rounded hover:bg-gray-100" aria-label="Close drawer">
                      <XMarkIcon className="h-5 w-5 text-gray-500" />
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto p-4">
                    {children}
                  </div>

                  {footer && (
                    <div className="border-t p-3">
                      {footer}
                    </div>
                  )}
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

Drawer.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.node,
  children: PropTypes.node,
  footer: PropTypes.node,
  widthClass: PropTypes.string
};

