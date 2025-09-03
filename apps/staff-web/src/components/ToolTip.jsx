// components/Tooltip.jsx
export default function Tooltip({ children, text }) {
  return (
    <div className="relative flex items-center group cursor-pointer">
      {children}
      <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-3 py-1 text-xs text-white bg-gray-800 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
        {text}
      </div>
    </div>
  );
}
