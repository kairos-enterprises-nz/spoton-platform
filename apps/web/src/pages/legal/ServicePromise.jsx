import { CheckCircle, Shield, Clock, DollarSign } from 'lucide-react';

export default function ServicePromise() {
  const principles = [
    {
      icon: <DollarSign className="w-6 h-6 text-white" />,
      title: "Transparent Pricing",
      description: "Clear, upfront pricing with no hidden fees or loyalty taxes. Same fair price for all customers."
    },
    {
      icon: <Shield className="w-6 h-6 text-white" />,
      title: "Digital-First Clarity",
      description: "Modern systems that provide real-time information, clear billing, and transparent service delivery."
    },
    {
      icon: <Clock className="w-6 h-6 text-white" />,
      title: "Long-Term Value",
      description: "Service designed for lasting value, not short-term profits. No price jumps or promotional traps."
    },
    {
      icon: <CheckCircle className="w-6 h-6 text-white" />,
      title: "Fair Service Delivery",
      description: "Consistent service quality and pricing that doesn't punish loyalty or reward churning."
    }
  ];

  const examples = [
    {
      title: "Power",
      description: "Power with transparent tariffs, real-time insights, and fair pricing that delivers long-term value."
    },
    {
      title: "Broadband", 
      description: "Broadband with reliable speeds, transparent pricing, and service that delivers long-term value."
    },
    {
      title: "Mobile",
      description: "Mobile with transparent pricing, simple data options, and long-term value."
    }
  ];

  return (
    <div className="bg-white">
      {/* Hero Section */}
      <div className="relative isolate bg-gradient-to-br from-slate-50 via-white to-teal-50/30 py-16 sm:py-24">
        <div className="mx-auto max-w-4xl px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-teal-50 to-slate-50 border border-teal-200/50 mb-8">
            <Shield className="w-5 h-5 text-teal-600" />
            <span className="text-sm font-medium text-slate-700">Our Commitment</span>
          </div>
          
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl mb-6">
            Our Service Promise
          </h1>
          <p className="text-xl text-slate-600 leading-relaxed max-w-2xl mx-auto">
            Clarity, fairness, and long-term value. No tricks — just transparent service across power, broadband, and mobile.
          </p>
        </div>
      </div>

      {/* Commitment Statement */}
      <section className="py-16 px-6 lg:px-8 bg-slate-50">
        <div className="mx-auto max-w-4xl text-center">
          <div className="bg-gradient-to-br from-teal-500 to-slate-600 rounded-3xl p-12 text-white">
            <h2 className="text-3xl font-bold mb-6">
              Our Promise to You
            </h2>
            <p className="text-xl leading-relaxed mb-8 opacity-95">
              We don't charge you additional rent to pay for someone else's welcome mat. 
              No tricks, no loyalty taxes — just fair service that respects your time and wallet.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="w-4 h-4" />
                <span>Parity across new and existing customers</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="w-4 h-4" />
                <span>Clear disclosure upfront</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="w-4 h-4" />
                <span>No honeymoon hangover</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* What Fair Pricing Means */}
      <section className="py-24 px-6 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              What "not tricks" means
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Our pricing philosophy is simple: transparency, fairness, and no surprises.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {principles.map((principle, index) => (
              <div
                key={index}
                className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 text-center hover:scale-[1.02]"
              >
                <div className="flex items-center justify-center w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-teal-500 to-slate-600 mb-4 shadow-lg">
                  {principle.icon}
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-3">
                  {principle.title}
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  {principle.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Service Examples */}
      <section className="py-24 px-6 lg:px-8 bg-slate-50">
        <div className="mx-auto max-w-4xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              How it works across our services
            </h2>
            <p className="text-lg text-slate-600">
              Fair pricing principles applied to every SpotOn service.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {examples.map((example, index) => (
              <div
                key={index}
                className="bg-white rounded-xl p-4 shadow-md border border-slate-200/50 hover:shadow-lg transition-all duration-300 hover:scale-[1.02]"
              >
                <h3 className="text-base font-bold text-slate-900 mb-2">
                  {example.title}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed mb-4">
                  {example.description}
                </p>
                <a
                  href={`/${example.title.toLowerCase()}`}
                  className="inline-block bg-teal-500 hover:bg-teal-400 text-white font-semibold text-xs px-3 py-2 rounded-lg transition-colors"
                >
                  Explore Plans
                </a>
              </div>
            ))}
          </div>
          
          <div className="mt-12 text-center">
            <a
              href="/getstarted"
              className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-teal-500 to-slate-600 hover:from-teal-400 hover:to-slate-500 text-white font-bold text-lg rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl hover:ring-2 hover:ring-teal-400/60 hover:ring-offset-2 hover:ring-offset-white"
            >
              Sign Me Up Today
            </a>
          </div>
        </div>
      </section>



    </div>
  );
}
