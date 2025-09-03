import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { Dialog, Transition, Portal } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';

export default function Drawer({ isOpen, onClose, title, headerLeft, children, footer, widthClass = 'max-w-xs w-80', side = 'left' }) {
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

  const sideClass = side === 'right' ? 'right-0 rounded-l-2xl' : 'left-0 rounded-r-2xl';
  const enterFrom = side === 'right' ? 'translate-x-full' : '-translate-x-full';

  return (
    <Transition show={isOpen} as={React.Fragment}>
      <Portal>
        <Dialog as="div" className="fixed inset-0 z-[1000]" onClose={onClose}>
          <Transition.Child
            as={React.Fragment}
            enter="ease-out duration-200" enterFrom="opacity-0" enterTo="opacity-100"
            leave="ease-in duration-150" leaveFrom="opacity-100" leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black/40" />
          </Transition.Child>

          <Transition.Child
            as={React.Fragment}
            enter="transform transition ease-in-out duration-200"
            enterFrom={enterFrom} enterTo="translate-x-0"
            leave="transform transition ease-in-out duration-200"
            leaveFrom="translate-x-0" leaveTo={enterFrom}
          >
            <Dialog.Panel className={`fixed top-0 bottom-0 ${sideClass} ${widthClass} bg-white shadow-xl flex flex-col z-[1001]`}>
              <div className="flex items-center justify-between px-4 py-4">
                <div className="flex items-center gap-3 min-h-[28px]">
                  {headerLeft}
                  {title ? (
                    <Dialog.Title className="text-lg font-semibold text-gray-900">{title}</Dialog.Title>
                  ) : (
                    <Dialog.Title className="text-lg font-semibold text-gray-900">Navigation</Dialog.Title>
                  )}
                </div>
                <motion.button
                  onClick={onClose}
                  whileHover={{ scale: 1.05, rotate: 90 }}
                  whileTap={{ scale: 0.95 }}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-gray-50 to-white hover:from-red-50 hover:to-red-100 border border-gray-200 hover:border-red-200 transition-all duration-200 shadow-sm hover:shadow-md"
                  aria-label="Close drawer"
                >
                  <span className="text-sm font-medium text-gray-700 hover:text-red-700">Close</span>
                  <XMarkIcon className="h-4 w-4 text-gray-600 hover:text-red-600" />
                </motion.button>
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
        </Dialog>
      </Portal>
    </Transition>
  );
}

Drawer.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.node,
  children: PropTypes.node,
  footer: PropTypes.node,
  widthClass: PropTypes.string,
  side: PropTypes.oneOf(['left', 'right'])
};

