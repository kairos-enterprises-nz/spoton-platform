import { useState } from "react";
import Icon from '../../assets/utilitycopilot-icon.webp';
import { AlertCircle } from 'lucide-react';

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [emailError, setEmailError] = useState("");
  const [emailExistsError, setEmailExistsError] = useState("");
  const [loading, setLoading] = useState(false); // To handle loading state

  const validateEmail = (e) => {
    const value = e.target.value;
    setEmail(value);

    // Basic email format validation
    const emailRegex = /\S+@\S+\.\S+/;
    if (!emailRegex.test(value)) {
      setEmailError("Please enter a valid email.");
    } else {
      setEmailError("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate email before sending request
    if (emailError) return;

    setLoading(true); // Start loading state

    try {
      const res = await fetch("http://localhost:8000/forgotpassword/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage(data.message || "Password reset link sent successfully!");
      } else {
        setMessage(data.message || "This email is not registered.");
        if (data.error === "Email does not exist") {
          setEmailExistsError("This email is not registered.");
        }
      }
    } catch {
      setMessage("An error occurred. Please try again.");
    } finally {
      setLoading(false); // End loading state
    }
  };

  return (
    <>
      <div className="flex min-h-full flex-1 flex-col justify-center py-14 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <img alt="Utility Copilot" src={Icon} className="mx-auto h-24 w-auto animate-pulse" />
        </div>
        <h2 className="mt-16 text-center text-2xl font-bold text-gray-900">Forgot your password?</h2>
        <p className="mt-8 text-center text-sm text-gray-600">Don&apos;t fret! Just type in your email and we will send you a code to reset your password!</p>
        <div className="p-12 sm:mx-auto sm:w-full sm:max-w-[350px] md:max-w-[500px]">
          <div className="bg-gray-100 px-6 py-8 shadow-sm sm:rounded-lg sm:px-12">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Input */}
              <div className="mt-2 relative">
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Email Address"
                  autoComplete="email"
                  value={email}
                  onChange={validateEmail}
                  className={`block w-full rounded-md bg-white py-1.5 pr-10 pl-3 text-base outline-1 placeholder-gray-400 focus:outline-2 sm:text-sm
                    ${emailError || emailExistsError ? 'text-red-900 outline-red-300 focus:outline-red-600' : 'text-gray-900 outline-gray-300 focus:outline-primary-turquoise'}`}
                />
                {emailError || emailExistsError ? (
                  <AlertCircle className="absolute right-3 top-2.5 w-5 h-5 text-red-500" />
                ) : null}
                {emailError && <p className="mt-2 text-sm text-red-600">{emailError}</p>}
                {emailExistsError && <p className="mt-2 text-sm text-red-600">{emailExistsError}</p>}
              </div>

              {/* Submit Button */}
              <div>
                <button
                  type="submit"
                  disabled={emailError || loading}
                  className={`flex w-full justify-center rounded-md px-3 py-1.5 text-sm font-semibold text-white shadow-xs
                    ${emailError || loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-secondary-darkgray hover:bg-primary-turquoise focus-visible:outline-2 focus-visible:outline-primary-turquoise'}`}
                >
                  {loading ? 'Sending...' : 'Reset password'}
                </button>
              </div>
            </form>
      {/* Display Message */}
      <div className="mt-2">
        {message && (
            <div className={`text-center p-4 ${message.includes("sent") ? "text-secondary-darkgray" : "text-secondary-darkgray"}`}>
           {message}
          </div>
        )}
      </div>
          </div>
        </div>
      </div>

      <div className="text-center mt-5">
        <a href="/login" className="text-gray-500 text-sm hover:text-primary-turquoise">
          Back to Sign In
        </a>
      </div>

      <footer className="py-12 text-center text-sm text-gray-600">
        {'\u00A9'} 2025 Utility Copilot. All rights reserved.
      </footer>
    </>
  );
};

export default ForgotPassword;
