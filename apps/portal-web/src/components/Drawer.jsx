import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';

export default function Drawer({
  isOpen,
  onClose,
  title,
  headerLeft,
  children,
  footer,
  widthClass = 'max-w-xs w-80',
  side = 'left',
  panelClassName = ''
}) {
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

  const sideIsRight = side === 'right';
  const enterFrom = sideIsRight ? 'translate-x-full' : '-translate-x-full';
  const sidePositionClass = sideIsRight ? 'right-0 rounded-l-2xl' : 'left-0 rounded-r-2xl';

  return (
    <Transition show={isOpen} as={React.Fragment}>
      <Dialog as="div" className="fixed inset-0 z-[13000]" onClose={onClose}>
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
          <Dialog.Panel
            className={`fixed top-0 bottom-0 ${sidePositionClass} ${widthClass} bg-white shadow-xl flex flex-col z-[13001] ${panelClassName}`}
          >
            <div className="flex items-center justify-between px-4 py-4">
              <div className="flex items-center gap-3 min-h-[28px]">
                {headerLeft}
                {title ? (
                  <Dialog.Title className="text-lg font-semibold text-gray-100">{title}</Dialog.Title>
                ) : (
                  <Dialog.Title className="text-lg font-semibold text-gray-100">Navigation</Dialog.Title>
                )}
              </div>
              <button onClick={onClose} className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-800 border border-gray-700 text-gray-200 hover:bg-gray-700 hover:text-white hover:border-primary-turquoise transition-all duration-200 shadow-sm" aria-label="Close drawer">
                <span className="text-sm font-medium">Close</span>
                <XMarkIcon className="h-4 w-4 text-gray-300" />
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
      </Dialog>
    </Transition>
  );
}

Drawer.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.node,
  headerLeft: PropTypes.node,
  children: PropTypes.node,
  footer: PropTypes.node,
  widthClass: PropTypes.string,
  side: PropTypes.oneOf(['left', 'right']),
  panelClassName: PropTypes.string
};

