import PropTypes from 'prop-types';

export default function WelcomeBanner({ userName = "Welcome back!" }) {
  return (
    <div className="bg-gradient-to-r from-[#40E0D0] to-[#364153] rounded-xl shadow-lg mb-6 p-6 text-white relative overflow-hidden group">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxkZWZzPjxwYXR0ZXJuIGlkPSJwYXR0ZXJuIiB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSIgcGF0dGVyblRyYW5zZm9ybT0icm90YXRlKDEzNSkiPjxwYXRoIGQ9Ik0gMjAgMjAgTCAyMCA0MCBNIDM1IDM1IEwgNDAgNDAgTSAxNSAxNSBMIDQwIDQwIE0gMCAwIEwgMzUgMzUgTSAwIDEwIEwgMzAgNDAgTSAwIDIwIEwgMjAgNDAgTSAwIDMwIEwgMTAgNDAiIHN0cm9rZT0iI2ZmZmZmZiIgc3Ryb2tlLXdpZHRoPSIxIiBzdHJva2Utb3BhY2l0eT0iMC4xIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI3BhdHRlcm4pIi8+PC9zdmc+')] opacity-30 animate-shimmer group-hover:opacity-40 transition-opacity duration-700"></div>
      <div className="absolute -right-16 -top-16 w-64 h-64 bg-white/10 rounded-full blur-3xl group-hover:bg-white/15 transition-all duration-700 transform group-hover:scale-110"></div>
      <div className="relative z-10 transform transition-transform duration-700 sm:translate-y-0 flex flex-col sm:flex-row justify-between">
        <div>
          <h2 className="text-2xl sm:text-3xl font-semibold mb-2">{userName}</h2>
          <p className="opacity-90 text-sm sm:text-base">Here&apos;s your utility dashboard for {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <div className="hidden sm:block">
          <div className="p-4 bg-white/10 rounded-lg mt-4 sm:mt-0 backdrop-blur-sm transform transition-transform duration-300 hover:scale-105">
            <div className="text-xs uppercase tracking-wider opacity-70 mb-1">Daily Energy Tip</div>
            <p className="text-sm">Smart thermostats can reduce energy costs by up to 15%</p>
          </div>
        </div>
      </div>
    </div>
  );
}

WelcomeBanner.propTypes = {
  userName: PropTypes.string
}; 