// pages/support/ContactSupport.jsx
import { useState } from 'react';
import BreadcrumbNav from '../components/BreadcrumbNav';

export default function ContactSupport() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    topic: '',
    message: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await fetch('/api/send-contact-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      alert('Your message has been sent.');
      setFormData({ name: '', email: '', phone: '', topic: '', message: '' });
    } catch (error) {
      alert('Something went wrong. Please try again later.');
    }
  };

  return (
    <div className="bg-white min-h-screen">
      {/* === HERO SECTION === */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-teal-900 px-6 pt-16 pb-8 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-white mb-4">Contact Support</h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Need help? Reach out via the form below. We're here to support you.
          </p>
        </div>
        <BreadcrumbNav
          path={[{ label: 'Support', to: '/support' }, { label: 'Contact Us' }]}
        />
      </section>

      {/* Contact Form Only */}
      <section className="max-w-4xl mx-auto px-6 py-16">
        <div className="bg-white p-10 rounded-2xl shadow-lg border border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">Send Us a Message</h2>
          <form className="space-y-6 max-w-xl mx-auto" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="name" className="block text-left text-sm font-medium text-gray-700">Your Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="e.g., Alex Smith"
                className="mt-1 w-full rounded-md border border-gray-300 px-4 py-2 focus:ring-2 focus:ring-primary-turquoise focus:outline-none"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-left text-sm font-medium text-gray-700">Your Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="you@example.com"
                className="mt-1 w-full rounded-md border border-gray-300 px-4 py-2 focus:ring-2 focus:ring-primary-turquoise focus:outline-none"
              />
            </div>

            <div>
              <label htmlFor="phone" className="block text-left text-sm font-medium text-gray-700">Your Phone Number</label>
              <input
                type="tel"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="e.g., 021 123 4567"
                className="mt-1 w-full rounded-md border border-gray-300 px-4 py-2 focus:ring-2 focus:ring-primary-turquoise focus:outline-none"
              />
            </div>

            <div>
              <label htmlFor="topic" className="block text-left text-sm font-medium text-gray-700">Query Related To</label>
              <select
                id="topic"
                name="topic"
                value={formData.topic}
                onChange={handleChange}
                required
                className="mt-1 w-full rounded-md border border-gray-300 px-4 py-2 focus:ring-2 focus:ring-primary-turquoise focus:outline-none"
              >
                <option value="">Select a topic...</option>
                <option value="general">General Inquiry</option>
                <option value="billing">Billing & Payments</option>
                <option value="technical">Technical Support</option>
                <option value="account">My Account</option>
              </select>
            </div>

            <div>
              <label htmlFor="message" className="block text-left text-sm font-medium text-gray-700">Your Message</label>
              <textarea
                id="message"
                name="message"
                rows="5"
                value={formData.message}
                onChange={handleChange}
                required
                placeholder="How can we help you today?"
                className="mt-1 w-full rounded-md border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-primary-turquoise focus:outline-none"
              ></textarea>
            </div>

            <div className="text-center pt-4">
              <button
                type="submit"
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-turquoise px-6 py-3 text-sm font-semibold text-white shadow-md hover:bg-secondary-darkgray transition"
              >
                Submit Message
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}
