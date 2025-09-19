import { motion } from 'framer-motion';

export default function MethodSelection({ onMethodSelect, submitError }) {
  return (
    <motion.div
      key="method-selection"
      className="relative bg-white/10 backdrop-blur-lg px-4 py-5 shadow-xl rounded-2xl border border-white/10"
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -30, scale: 0.95 }}
      transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <motion.div
        className="space-y-4"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, delay: 0.1, ease: 'easeOut' }}
      >
        {/* Primary: Google */}
        <motion.button
          onClick={() => onMethodSelect('google')}
          className="group relative flex h-11 items-center justify-center gap-3 w-full rounded-lg bg-white text-gray-900 border border-white/10 shadow-sm hover:shadow transition-all"
          title="Sign up with Google"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={{ type: 'spring', stiffness: 450, damping: 28, mass: 0.5 }}
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          <span className="text-sm font-semibold">Sign up with Google</span>
        </motion.button>

        {/* Secondary: Email */}
        <motion.button
          onClick={() => onMethodSelect('email')}
          className="group relative w-full rounded-lg h-11 border border-white/20 text-slate-200 hover:text-white bg-transparent hover:bg-white/5 transition-colors"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          <div className="flex items-center justify-center gap-2">
            <svg className="h-4 w-4 text-slate-300 group-hover:text-slate-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
            </svg>
            <span className="text-sm font-medium">Sign up with Email</span>
          </div>
        </motion.button>

        {/* Small reassurance */}
        <p className="text-[11px] text-center text-slate-300/80">We never see your Google password.</p>

        {/* Error display */}
        {submitError && (
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 backdrop-blur-sm">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-red-500/20">
                <svg className="h-3 w-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-xs text-red-300">{submitError}</p>
            </div>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}