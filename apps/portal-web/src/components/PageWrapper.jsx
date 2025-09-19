import PropTypes from 'prop-types';

export default function PageWrapper({ children }) {
  return (
    <div className="relative isolate min-h-screen w-full bg-gradient-to-br from-white via-slate-100 to-white overflow-hidden px-0.5 py-14 sm:px-6 lg:px-8">
      {/* Radial SVG background pattern */}
      <svg
        aria-hidden="true"
        className="absolute inset-x-0 top-0 -z-10 h-[64rem] w-full stroke-gray-200 [mask-image:radial-gradient(32rem_32rem_at_center,white,transparent)]"
      >
        <defs>
          <pattern
            id="spoton-pattern"
            width={200}
            height={200}
            x="50%"
            y={-1}
            patternUnits="userSpaceOnUse"
          >
            <path d="M.5 200V.5H200" fill="none" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#spoton-pattern)" />
      </svg>

      {/* LEFT blob */}
      <div
        aria-hidden="true"
        className="absolute top-[-20%] left-[-10%] -z-10 transform-gpu overflow-hidden blur-3xl"
      >
        <div
          className="aspect-[801/1036] w-[45rem] bg-gradient-to-tr from-[hsl(234,96%,78%)] to-[#c4ffff] opacity-30"
          style={{
            clipPath:
              'polygon(63.1% 29.5%, 100% 17.1%, 76.6% 3%, 48.4% 0%, 44.6% 4.7%, 54.5% 25.3%, 59.8% 49%, 55.2% 57.8%, 44.4% 57.2%, 27.8% 47.9%, 35.1% 81.5%, 0% 97.7%, 39.2% 100%, 35.2% 81.4%, 97.2% 52.8%, 63.1% 29.5%)',
          }}
        />
      </div>

      {/* RIGHT blob (mirrored horizontally) */}
      <div
        aria-hidden="true"
        className="absolute top-[-20%] right-[-10%] -z-10 transform-gpu overflow-hidden blur-3xl scale-x-[-1]"
      >
        <div
          className="aspect-[801/1036] w-[45rem] bg-gradient-to-tr from-[#90aeff] to-[#c1fffa] opacity-30"
          style={{
            clipPath:
              'polygon(63.1% 29.5%, 100% 17.1%, 76.6% 3%, 48.4% 0%, 44.6% 4.7%, 54.5% 25.3%, 59.8% 49%, 55.2% 57.8%, 44.4% 57.2%, 27.8% 47.9%, 35.1% 81.5%, 0% 97.7%, 39.2% 100%, 35.2% 81.4%, 97.2% 52.8%, 63.1% 29.5%)',
          }}
        />
      </div>

      <div className="relative z-10">{children}</div>
    </div>
  );
}

PageWrapper.propTypes = {
  children: PropTypes.node.isRequired,
};
