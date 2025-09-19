import PropTypes from 'prop-types'
import { useEffect, useState } from 'react'

export default function Testimonials({ testimonials = [] }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [fade, setFade] = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      setFade(false)
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % testimonials.length)
        setFade(true)
      }, 300)
    }, 4000)
    return () => clearInterval(interval)
  }, [testimonials.length])

  const visibleTestimonials =
    testimonials.length > 3
      ? [
          testimonials[currentIndex],
          testimonials[(currentIndex + 1) % testimonials.length],
          testimonials[(currentIndex + 2) % testimonials.length],
        ]
      : testimonials

  return (
    <div className="relative bg-white py-24 px-6 lg:px-8 overflow-hidden">
      <div
        aria-hidden="true"
        className="absolute bottom-0 left-1/2 -translate-x-1/4 w-[200%] h-25 bg-gradient-to-r from-teal-200 via-indigo-200 to-pink-200 opacity-25 blur-2xl animate-shimmer"
      ></div>

      <div className="mx-auto max-w-6xl text-center relative z-10">
        <h2 className="text-2xl font-semibold text-teal-600 tracking-wide uppercase">
          What our customers say
        </h2>
        <p className="mt-2 text-3xl font-bold text-gray-900">Real stories. Real satisfaction.</p>

        <div
          className={`mt-16 grid gap-10 sm:grid-cols-2 lg:grid-cols-3 transform transition-all duration-500 ${
            fade ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
          }`}
        >
          {visibleTestimonials.map((testimonial, index) => (
            <figure
              key={index}
              className="rounded-2xl bg-white p-6 border border-gray-200 shadow-sm transition-all duration-300 hover:shadow-md hover:scale-[1.02]"
            >
              <blockquote className="text-gray-700 text-base italic leading-relaxed">
                <p>“{testimonial.quote}”</p>
              </blockquote>
              <figcaption className="mt-6 flex items-center gap-x-4">
                <img
                  src={testimonial.image}
                  alt={testimonial.name}
                  className="h-10 w-10 rounded-full border border-gray-300"
                />
                <div className="text-left">
                  <div className="text-sm font-bold text-gray-900">{testimonial.name}</div>
                  <div className="text-sm text-gray-500">{testimonial.role}</div>
                </div>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </div>
  )
}

Testimonials.propTypes = {
  testimonials: PropTypes.arrayOf(
    PropTypes.shape({
      quote: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      role: PropTypes.string,
      image: PropTypes.string,
    })
  ).isRequired,
}
