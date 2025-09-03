import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Icon from '../../assets/utilitycopilot-icon.webp';

const ResetPassword = () => {
  const { uidb64, token } = useParams(); // Capture the uidb64 and token from the URL
  const navigate = useNavigate(); // Hook to handle navigation
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  useEffect(() => {
    // Optionally: You can validate the token or perform any checks when the component mounts
  }, [uidb64, token]);

  const validatePassword = (e) => {
    const value = e.target.value;
    setPassword(value);
    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    if (!passwordPattern.test(value)) {
      setPasswordError("Password must be 8+ characters with a mix of uppercase, lowercase, numbers, and symbols.");
    } else {
      setPasswordError("");
    }
  };

  const validateConfirmPassword = (e) => {
    const value = e.target.value;
    setConfirmPassword(value);
    if (value !== password) {
      setConfirmPasswordError("Passwords do not match!");
    } else {
      setConfirmPasswordError("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Additional client-side validation to check if passwords match
    if (password !== confirmPassword) {
      setMessage("Passwords do not match!");
      return;
    }

    // Send request to reset password
    const res = await fetch(`http://localhost:8000/resetpassword/${uidb64}/${token}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ password }),
    });

    const data = await res.json();

    if (res.ok) {
      setMessage("Password reset successful!");
      // Redirect to the sign-in page after successful password reset
      setTimeout(() => {
        navigate("/login"); // Navigate to the login page after successful password reset
      }, 2000);
    } else {
      setMessage(data.error || "An error occurred. Please try again.");
    }
  };

  return (
    <>
      <div className="flex min-h-full flex-1 flex-col justify-center py-14 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <img alt="Utility Copilot" src={Icon} className="mx-auto h-24 w-auto animate-pulse" />
        </div>
        <h2 className="mt-16 text-center text-2xl font-bold text-gray-900">Forgot your password?</h2>
        <p className="mt-8 text-center text-sm text-gray-600">Enter your new password below to reset it!</p>
        <div className="p-12 sm:mx-auto sm:w-full sm:max-w-[350px] md:max-w-[500px]">
          <div className="bg-gray-100 px-6 py-8 shadow-sm sm:rounded-lg sm:px-12">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Password Input */}
              <div className="mt-2 relative">
                <input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="New Password"
                  value={password}
                  onChange={validatePassword}
                  className={`block w-full rounded-md bg-white py-1.5 pr-10 pl-3 text-base outline-1 placeholder-gray-400 focus:outline-2 sm:text-sm
                    ${passwordError ? 'text-red-900 outline-red-300 focus:outline-red-600' : 'text-gray-900 outline-gray-300 focus:outline-primary-turquoise'}`}
                />
                {passwordError && <p className="mt-2 text-sm text-red-600">{passwordError}</p>}
              </div>

              {/* Confirm Password Input */}
              <div className="mt-2 relative">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  placeholder="Confirm New Password"
                  value={confirmPassword}
                  onChange={validateConfirmPassword}
                  className={`block w-full rounded-md bg-white py-1.5 pl-3 pr-10 text-base outline-1 placeholder-gray-400 focus:outline-2 sm:text-sm
                    ${confirmPasswordError ? 'text-red-900 outline-red-300 focus:outline-red-600' : 'text-gray-900 outline-gray-300 focus:outline-primary-turquoise'}`}
                />
                {confirmPasswordError && <p className="mt-2 text-sm text-red-600">{confirmPasswordError}</p>}
              </div>

              {/* Submit Button */}
              <div>
                <button
                  type="submit"
                  disabled={passwordError || confirmPasswordError || password !== confirmPassword}
                  className={`flex w-full justify-center rounded-md px-3 py-1.5 text-sm font-semibold text-white shadow-xs
                    ${passwordError || confirmPasswordError || password !== confirmPassword ? 'bg-gray-400 cursor-not-allowed' : 'bg-secondary-darkgray hover:bg-primary-turquoise focus-visible:outline-2 focus-visible:outline-primary-turquoise'}`}
                >
                  Reset Password
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
          Take me to Sign In
        </a>
      </div>

      <footer className="py-12 text-center text-sm text-gray-600">
        &copy; 2025 Utility Copilot. All rights reserved.
      </footer>
    </>
  );
};

export default ResetPassword;
