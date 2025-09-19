import { useState, useEffect,useRef} from "react";
import { QuestionMarkCircleIcon } from '@heroicons/react/16/solid'
import termsContent from '../data/termsContent'
import { sendOtp, verifyOtp } from "../services/verificationService";
import { useNavigate } from "react-router-dom";
import userService from "../services/userService"; 

export default function UserDetails() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    userType: "",
    phoneNumber: "",
    dateOfBirth: "",
    businessDetails: {
      businessName: "",
      tradingAs: "",
      isAuthorizedPersonSame: "No",
    },
    acceptedTerms: false,
    authorizedPerson: {
      firstName: "",
      lastName: "",
      email: "",
      phoneNumber: "",
    },
    profileComplete: "",
    phoneNumberVerified:"",
  });

  
  const [isValidPhone, setIsValidPhone] = useState(true);
  const [isValidDob, setIsValidDob] = useState(true);
  const [showTooltipA, setShowTooltipA] = useState(false);
  const [showTooltipB, setShowTooltipB] = useState(false);

  const [accepted, setAccepted] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [message, setMessage] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const otpInputRefs = useRef([]);

  const navigate = useNavigate(); // ✅ Initialize navigation


  const validatePhoneNumber = (phoneNumber) => {
    const countryCode = "+64";  // You can dynamically fetch the country code from the dropdown
    const fullPhone = countryCode + phoneNumber;  // Concatenate the country code with the entered phone number
  
    if (!phoneNumber) {
      setIsValidPhone(false);
      return;
    }
  
    // Phone number validation with country code
    const phoneRegex = /^[+][64]{2}[ ]?[1-9][0-9]{8,9}$/; // Adjusted regex to disallow starting with 0
    
    if (!phoneRegex.test(fullPhone)) {
      setIsValidPhone(false);
      return;
    }
  
    setIsValidPhone(true);
  };



  const validateDateOfBirth = (dob) => {
    // Regex to validate the date format as DD-MM-YYYY
    const dateRegex = /^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-\d{4}$/;
  
    if (!dateRegex.test(dob)) {
      setIsValidDob(false);
      return;
    }
  
    const [day, month, year] = dob.split("-");
    const dobDate = new Date(`${year}-${month}-${day}`); // Correcting date format to YYYY-MM-DD for JS Date
  
    // Validate that the year is greater than 1900 and the date is less than today's date
    const currentDate = new Date();
    const minDate = new Date();
    minDate.setFullYear(currentDate.getFullYear() - 16); // 16 years ago from today
  
    if (parseInt(year) <= 1900) {
      setIsValidDob(false);
      return;
    }
  
    if (dobDate > currentDate) {
      setIsValidDob(false);
      return;
    }
  
    if (dobDate > minDate) {
      setIsValidDob(false);
      return;
    }
  
    if (isNaN(dobDate.getTime())) {
      setIsValidDob(false);
      return;
    }
  
    setIsValidDob(true);
  };
  
  
// Update the phone number input handler to include the country code
const handleInputChange = (e) => {
  const { name, value } = e.target;

  if (name === "phoneNumber") {
    validatePhoneNumber(value); // Validate phone number on change
  }

  if (name === "dateOfBirth") {
    validateDateOfBirth(value); // Validate date of birth on change
  }

  setFormData((prevData) => ({
    ...prevData,
    [name]: value,
  }));
};

// Handle phone validation on blur
const handlePhoneBlur = () => {
  if (formData.phoneNumber) {
    validatePhoneNumber(formData.phoneNumber); // Validate phone number on blur
  }
};

  // Handle date of birth validation on blur
  const handleDobBlur = () => {
    if (formData.dateOfBirth) {
      validateDateOfBirth(formData.dateOfBirth);
    }
  };

  useEffect(() => {
    // Fetch user data from localStorage
    const user = JSON.parse(localStorage.getItem("user"));
    if (user) {
      setFormData({
        firstName: user.first_name || "",
        lastName: user.last_name || "",
        email: user.email || "",
        phoneNumber: user.phoneNumber || "",
        dateOfBirth: user.dateOfBirth || "",
        userType: user.userType || "",
        businessDetails: user.businessDetails || "",
      });
    } else {
    }
  }, []);

  // Handle step navigation with delay
  const delaySetStep = (nextStep) => {
    setTimeout(() => {
      setStep(nextStep);
    }, 1000);
  };

  const handleUserTypeSelect = (type) => {
    setFormData((prevData) => ({
      ...prevData,
      userType: type,
    }));
    delaySetStep(2);
  };
  
  const handleBusinessDetailsChange = (e) => {
    setFormData({
      ...formData,
      businessDetails: {
        ...formData.businessDetails,
        [e.target.name]: e.target.value,
      },
    });
  };

const handleAuthorizedPersonChange = (e) => {
    setFormData({
      ...formData,
      authorizedPerson: {
        ...formData.authorizedPerson,
        [e.target.name]: e.target.value,
      },
    });
  };


//-------------Step 4 ------------------//

const handleCheckboxChange = (e) => {
  setAccepted(e.target.checked); // Update acceptance state
};

const handleSubmit = (e) => {
  e.preventDefault();
  if (!accepted) {
    alert("You must accept the terms and conditions to proceed.");
  } else {
    delaySetStep(5);
  }
};

////-----------Step 5------------//

const handleSendOtp = async (e) => {
  e.preventDefault();

  try {
    const response = await sendOtp(formData.phoneNumber);

    if (response.success) {
      setOtpSent(true);
      setMessage("OTP sent successfully!");
    } else {
      setMessage(response.message || "Failed to send OTP.");
    }
  } catch (error) {
    setMessage("Error sending OTP. Please try again.");
  }
};

const handleVerifyOtp = async (e) => {
  e.preventDefault();

  try {
    const response = await verifyOtp(formData.phoneNumber, otpCode);

    if (response.success) {
      setMessage("OTP verified successfully!");

      // ✅ Step 1: Update `profileComplete` & `phoneNumberVerified` to boolean values (true or false)
      setFormData((prevData) => ({
        ...prevData,
        profileComplete: true, // Set to true instead of "Yes"
        phoneNumberVerified: true, // Set to true instead of "Yes"
      }));

      // ✅ Step 2: Send updated form data to backend
      const formDataToSend = {
        ...formData,
        profileComplete: true, // Set to true
        phoneNumberVerified: true, // Set to true
      };

      await sendFormDataToBackend(formDataToSend);

      // ✅ Step 3: Redirect after 1 second
      setTimeout(() => navigate("/dashboard"), 1000);
    } else {
      setMessage(response.message || "OTP verification failed.");
    }
  } catch (error) {
    setMessage("Error verifying OTP. Please try again.");
  }
};


// Function to send form data to the backend
const sendFormDataToBackend = async (data) => {
  try {
    // Update user details
    await userService.updateUserDetails(data);

    // If business details exist, update them
    if (data.businessDetails && data.businessDetails.businessName) {
      await userService.updateBusinessDetails(data.businessDetails);
    }

  } catch (error) {
  }
};

// -------------- Button Functions----------------//
  
  const handleNext = () => {
    const isFormValid = formData.phoneNumber && formData.dateOfBirth && isValidPhone && isValidDob;
  
    if (step === 2 && isFormValid) {
      const nextStep = formData.userType === "Residential" ? 4 : 3;
      delaySetStep(nextStep); // Proceed to the next step
    } else if (step === 3) {
      const nextStep = formData.userType === "Business" ? 4 : 3 ;
      delaySetStep(nextStep);
    }           
      else {
        alert("Please ensure all required fields are filled in correctly.");
      }   
  };
  
  const handlePrevious = () => {
    if (step === 5) {
      const previousStep = formData.userType === "Residential" ? 4 : 3;
      delaySetStep(previousStep); // Move to the correct previous step
    } else if (step === 4) {
      const previousStep = formData.userType === "Business" ? 3 : 2;
      delaySetStep(previousStep); // Move to the correct previous step
    } else if (step > 1) {
      delaySetStep(step - 1); // Move to the previous step normally
    }
  };

  const isNextButtonDisabled = () => {
    if (step === 2) {
      return !formData.phoneNumber || !formData.dateOfBirth || !isValidPhone || !isValidDob;
    }
    if (step === 3) {
      // Disable button until Yes or No is selected
      if (!formData.businessDetails?.isAuthorizedPersonSame) {
        return true;  // Disable the button if no value is selected
      }
  
      // If Yes is selected, check for tradingAs field
      if (formData.businessDetails?.isAuthorizedPersonSame === "Yes") {
        return !formData.businessDetails?.tradingAs;
      }
  
      // If No is selected, check for authorizedPerson details
      if (formData.businessDetails?.isAuthorizedPersonSame === "No") {
        return !formData.authorizedPerson?.firstName ||
               !formData.authorizedPerson?.lastName ||
               !formData.authorizedPerson?.email ||
               !formData.authorizedPerson?.phoneNumber;
      }
    } 
    return false;
  };
  
  return (
    <div className="flex min-h-full flex-1 flex-col justify-center py-14 sm:px-6 lg:px-8">
      <div className="p-12 sm:mx-auto sm:w-full sm:max-w-[350px] md:max-w-[800px]">
        <div className="bg-gray-50 border-gray-50 border-2 px-6 py-8 shadow-sm sm:rounded-lg sm:px-12">
          <form className="space-y-6">
            {/* Step 1: User Type */}
            {step === 1 && (
              <div>
                <h3 className="text-xl font-bold text-center mb-10">Select your User Type</h3>
                <div className="mt-4 flex justify-center space-x-5">
                  <button
                    type="button"
                    onClick={() => handleUserTypeSelect("Residential")}
                    className={`p-4 w-full text-center rounded ${formData.userType === "Residential" ? "bg-primary-turquoise font-bold text-white" : "bg-gray-200"}`}
                  >
                    Residential
                  </button>
                  <button
                    type="button"
                    onClick={() => handleUserTypeSelect("Business")}
                    className={`p-4 w-full text-center rounded ${formData.userType === "Business" ? "bg-primary-turquoise font-bold text-white" : "bg-gray-200"}`}
                  >
                    Business
                  </button>
                </div>
              </div>
            )}
            {/* Step 2: User Details */}
{step === 2 && (
    <div>
  <h3 className="text-xl font-bold mb-10">Your Details</h3>

  {/* First Name and Last Name */}
  <div className="flex space-x-4">
    <div className="w-1/2">
      <label htmlFor="firstName" className="block text-sm font-medium text-gray-500">First Name</label>
      <div className="mt-2">
        <input
          type="text"
          id="firstName"
          name="firstName"
          value={formData.firstName}
          readOnly
          className="block w-full rounded-md bg-gray-50 px-3 py-1.5 text-base text-gray-900 outline-1 outline-gray-300 sm:text-sm"
        />
      </div>
    </div>
    <div className="w-1/2">
      <label htmlFor="lastName" className="block text-sm font-medium text-gray-500">Last Name</label>
      <div className="mt-2">
        <input
          type="text"
          id="lastName"
          name="lastName"
          value={formData.lastName}
          readOnly
          className="block w-full rounded-md bg-gray-50 px-3 py-1.5 text-base text-gray-900 outline-1 outline-gray-300 sm:text-sm"
        />
      </div>
    </div>
  </div>

  {/* Date of Birth */}
  <div className="mt-8">
  <label htmlFor="dateOfBirth" className="block text-sm font-medium text-gray-500">Date of Birth </label>
  <div className="mt-2  grid grid-cols-1 ">
    <input
      type="text"
      id="dateOfBirth"
      name="dateOfBirth"
      value={formData.dateOfBirth}
      onChange={handleInputChange}
      onBlur={handleDobBlur}
      placeholder="dd-mm-yyyy"
      className="col-start-1 row-start-1 block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-turquoise sm:text-sm"
    />
    {!isValidDob && <p className="text-sm mt-2 text-red-500">Enter a valid date (dd-mm-yyyy).</p>}
    <div
          className="relative col-start-1 row-start-1 mr-3 size-5 self-center justify-self-end"
          onMouseEnter={() => setShowTooltipA(true)}
          onMouseLeave={() => setShowTooltipA(false)}
        >
          <QuestionMarkCircleIcon className="text-gray-400 sm:size-4" />
          {showTooltipA && (
            <div className="absolute right-6 bottom-6 w-44 text-xs bg-black text-white px-2 py-1 rounded-md shadow-lg">
              Must be 16+ years old.
            </div>
          )}
        </div>
  </div>
</div>

  {/* Email */}
  <div className="mt-8">
    <label htmlFor="email" className="block text-sm font-medium text-gray-500">Email</label>
    <div className="mt-2">
      <input
        type="email"
        id="email"
        name="email"
        value={formData.email}
        readOnly
        className="block w-full rounded-md bg-gray-50 px-3 py-1.5 text-base text-gray-900 outline-1 outline-gray-300 sm:text-sm"
      />
    </div>
  </div>
{/* Phone Number */}
<div className="mt-8 mb-16">
  <label htmlFor="phone-number" className="block text-sm font-medium text-gray-500">Phone Number</label>
  <div className="mt-2">
    <div className="flex items-center rounded-md bg-white border border-gray-300 focus-within:border-primary-turquoise focus-within:ring-1 focus-within:ring-primary-turquoise">
      <div className="flex-shrink-0">
        <select
          id="country"
          name="country"
          aria-label="Country code"
          className="w-20 rounded-l-md py-1.5 pl-3 pr-2 text-base text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-primary-turquoise sm:text-sm"
        >
          <option value="+64">+64</option>
          {/* Add more countries as needed */}
        </select>
      </div>
      <input
        id="phoneNumber"  // Update this id
        name="phoneNumber"  // Make sure it matches the state property
        type="text"
        value={formData.phoneNumber}  // Bind to the correct state property
        onChange={handleInputChange}  // Handle change with correct function
        onBlur={handlePhoneBlur}  // Ensure to call the validation function onBlur
        placeholder="Enter phone number"
        className="w-full rounded-r-md py-1.5 pr-7 pl-3 text-base text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-primary-turquoise sm:text-sm"
      />
    </div>
    {!isValidPhone && (
      <p className="text-sm text-red-500 mt-2">Please enter a valid phone number.</p>
    )}
  </div>
</div>
</div>

)}
{/* Step 3: Business Details */}
{step === 3 && formData.userType === "Business" && (
  <div>
    <h3 className="text-xl font-bold mb-5">Business Details</h3>

    {/* Business Name */}
    <div className="mt-8">
      <label htmlFor="businessName" className="block text-sm font-medium text-gray-500"> Registered Business Name </label>
     <div className="mt-2 grid grid-cols-1">
      <input
        type="text"
        name="businessName"
        value={formData.businessDetails?.businessName || ""}
        onChange={handleBusinessDetailsChange}
        placeholder="eg. New Zealand Company Limited"
        id="businessName"
        className="col-start-1 row-start-1 block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 placeholder:text-gray-400 outline-1 outline-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-turquoise sm:text-sm"
      />
          <div
          className="relative col-start-1 row-start-1 mr-3 size-5 self-center justify-self-end"
          onMouseEnter={() => setShowTooltipA(true)}
          onMouseLeave={() => setShowTooltipA(false)}
        >
          <QuestionMarkCircleIcon className="text-gray-400 sm:size-4" />
          {showTooltipA && (
            <div className="absolute right-6 bottom-6 w-44 text-xs bg-black text-white px-2 py-1 rounded-md shadow-lg">
              Leave blank if Sole Trader.
            </div>
          )}  
        </div>
    </div>
    </div>

    {/* Trading As */}
    <div className="mt-8">
      <label htmlFor="tradingAs" className="block text-sm font-medium text-gray-500">
        Trading As
      </label>
      <input
        type="text"
        name="tradingAs"
        value={formData.businessDetails?.tradingAs || ""}
        onChange={handleBusinessDetailsChange}
        placeholder="eg. John Doe's ToolShed"
        id="tradingAs"
        className="mt-2 block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 placeholder:text-gray-400 outline-1 outline-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-turquoise sm:text-sm"
      />
    </div>

    {/* Is Authorized Person Same */}
<div className="mt-8">
  <label className="text-sm font-medium text-gray-500">Is the authorised person same as user?</label>
  <div className="mt-2 flex items-center space-x-4">
    <label htmlFor="isAuthorizedPersonSameYes" className="inline-flex items-center space-x-2">
      <input
        type="radio"
        name="isAuthorizedPersonSame"
        id="isAuthorizedPersonSameYes"
        value="Yes"
        checked={formData.businessDetails?.isAuthorizedPersonSame === "Yes"}
        onChange={handleBusinessDetailsChange}
        className="h-4 w-4 text-primary-turquoise border-gray-300 focus:ring-primary-turquoise"
      />
      <span className="text-gray-600">Yes</span>
    </label>
    <label htmlFor="isAuthorizedPersonSameNo" className="inline-flex items-center space-x-2">
      <input
        type="radio"
        name="isAuthorizedPersonSame"
        id="isAuthorizedPersonSameNo"
        value="No"
        checked={formData.businessDetails?.isAuthorizedPersonSame === "No"}
        onChange={handleBusinessDetailsChange}
        className="h-4 w-4 text-primary-turquoise border-gray-300 focus:ring-primary-turquoise"
      />
      <span className="text-gray-600">No</span>
    </label>   
    <div
          className="relative col-start-1 row-start-1 mr-3 size-5 self-center justify-self-end"
          onMouseEnter={() => setShowTooltipB(true)}
          onMouseLeave={() => setShowTooltipB(false)}
        >
          <QuestionMarkCircleIcon className="text-gray-400 sm:size-4" />
          {showTooltipB && (
            <div className="absolute right-6 bottom-6 w-44 text-xs bg-black text-white px-2 py-1 rounded-md shadow-lg">
              The authorized person must be an owner, manager, or director of your business.
            </div>
          )}  
        </div>
  </div> 
</div>
    {/* Authorized Person Details */}
    {formData.businessDetails?.isAuthorizedPersonSame === "No" && (
      <div className="mt-10">
        <h4 className="font-semibold text-lg text-gray-700">Authorised Person Details</h4>

        {/* Authorized Person First Name */}
        <div className="mt-4">
          <label htmlFor="firstName" className="block text-sm font-medium text-gray-500">
            First Name
          </label>
          <input
            type="text"
            name="firstName"
            value={formData.authorizedPerson?.firstName || ""}
            onChange={handleAuthorizedPersonChange}
            placeholder="Authorised Person First Name"
            id="firstName"
            className="mt-2 block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 placeholder:text-gray-400 outline-1 outline-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-turquoise sm:text-sm"
          />
        </div>

        {/* Authorized Person Last Name */}
        <div className="mt-4">
          <label htmlFor="lastName" className="block text-sm font-medium text-gray-500">
            Last Name
          </label>
          <input
            type="text"
            name="lastName"
            value={formData.authorizedPerson?.lastName || ""}
            onChange={handleAuthorizedPersonChange}
            placeholder="Authorized Person Last Name"
            id="lastName"
            className="mt-2 block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 placeholder:text-gray-400 outline-1 outline-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-turquoise sm:text-sm"
          />
        </div>

        {/* Authorized Person Email */}
        <div className="mt-4">
          <label htmlFor="email" className="block text-sm font-medium text-gray-500">
            Email
          </label>
          <input
            type="email"
            name="email"
            value={formData.authorizedPerson?.email || ""}
            onChange={handleAuthorizedPersonChange}
            placeholder="Authorized Person Email"
            id="email"
            className="mt-2 block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 placeholder:text-gray-400 outline-1 outline-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-turquoise sm:text-sm"
          />
        </div>

        {/* Authorized Person Phone Number */}
<div className="mt-8 mb-16">
  <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-500">
    Authorized Person Phone Number
  </label>
  <div className="mt-2">
    <div className="flex items-center rounded-md bg-white border border-gray-300 focus-within:border-primary-turquoise focus-within:ring-1 focus-within:ring-primary-turquoise">
      {/* Country Code Selector */}
      <div className="flex-shrink-0">
        <select
          id="countryCode"
          name="countryCode"
          value={formData.authorizedPerson?.countryCode || "+64"}
          onChange={handleAuthorizedPersonChange}
          aria-label="Country code"
          className="w-20 rounded-l-md py-1.5 pl-3 pr-2 text-base text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-primary-turquoise sm:text-sm"
        >+
          <option value="+64">+64</option>
          </select>
      </div>

      {/* Phone Number Input */}
      <input
        id="phoneNumber"
        name="phoneNumber"
        type="tel"
        value={formData.authorizedPerson?.phoneNumber || ""}
        onChange={handleAuthorizedPersonChange}
        onBlur={handlePhoneBlur}  // Phone validation function
        placeholder="Enter phone number"
        className="w-full rounded-r-md py-1.5 pr-7 pl-3 text-base text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-primary-turquoise sm:text-sm"
      />
    </div>

    {/* Validation Error Message */}
    {!isValidPhone && (
      <p className="text-sm text-red-500 mt-2">Please enter a valid phone number.</p>
    )}
  </div>
</div>
</div>
    )}
  </div>
)}

{/* Step 4: Terms and Conditions */}
{step === 4 && (
  <div className="max-w-3xl mx-auto bg-white shadow-xl rounded-lg overflow-hidden border border-gray-200">
    
    {/* Header */}
    <h2 className="bg-gradient-to-r from-primary-turquoise to-accent-blue p-5 text-white text-xl font-bold text-center uppercase tracking-wide">
      Terms & Conditions
    </h2>

    {/* Scrollable Content */}
    <div className="h-[400px] overflow-y-auto p-6 bg-gray-50 text-gray-800 font-serif text-lg leading-relaxed scrollbar-thin scrollbar-thumb-gray-500 scrollbar-track-gray-200 rounded-md">
      <pre className="whitespace-pre-wrap text-sm font-sans">{termsContent}</pre>
    </div>

    {/* Footer */}
    <div className="p-4 text-sm text-gray-600 text-center border-t">
      By using our services, you agree to these terms.
    </div>

    {/* Accept Checkbox */}
    <div className="flex items-center gap-3 mt-4 px-6 py-4 bg-gray-100 rounded-b-lg">
      <input
        type="checkbox"
        id="acceptTerms"
        checked={accepted}
        onChange={handleCheckboxChange}
        className="h-5 w-5 border-gray-300 rounded text-blue-600 focus:ring focus:ring-blue-300 transition duration-200 cursor-pointer"
      />
      <label htmlFor="acceptTerms" className="text-gray-700 text-[15px] select-none cursor-pointer">
        I have read and accept the <strong className="text-secondary-darkgray">Terms and Conditions</strong>.
      </label>
    </div>
  </div>
)}

{/* Step 5: Mobile Authorisation */}
{step === 5 && (
  <div className="max-w-md mx-auto text-center bg-white px-4 sm:px-8 py-10 rounded-xl shadow">
    <header className="mb-8">
      <h1 className="text-2xl font-bold mb-2 text-slate-900">Mobile Authorisation</h1>
      <p className="text-[14px] text-slate-500">
        {otpSent ? "Enter the OTP sent to your phone" : "Your phone number to receive an One Time Password (OTP)"}
      </p>
    </header>

    {!otpSent ? (
      <div>
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-full p-3 border rounded bg-slate-100 text-lg text-center font-medium text-slate-900">
          {`${formData.countryCode || "+64"} ${formData.phoneNumber || ""}`}
          </div>
        </div>
        <div className="max-w-[260px] mx-auto">
          <button
            type="button"
            className="w-full inline-flex justify-center whitespace-nowrap rounded-lg bg-indigo-500 px-3.5 py-2.5 text-sm font-medium text-white shadow-sm shadow-indigo-950/10 hover:bg-indigo-600 focus:outline-none focus:ring focus:ring-indigo-300 transition-colors duration-150"
            onClick={handleSendOtp}
          >
            Send OTP
          </button>
        </div>
      </div>
    ) : (
      <div>
        <div className="flex items-center justify-center gap-3 mb-4">
          {[...Array(6)].map((_, index) => (
            <input
              key={index}
              ref={(el) => (otpInputRefs.current[index] = el)}
              type="text"
              className="w-14 h-14 text-center text-2xl font-extrabold text-slate-900 bg-slate-100 border border-transparent hover:border-slate-200 appearance-none rounded p-4 outline-none focus:bg-white focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
              maxLength="1"
              value={otpCode[index] || ""}
              onChange={(e) => {
                const value = e.target.value;
                if (!/^[0-9]?$/.test(value)) return; // Only allow digits

                const newOtpCode = otpCode.split("");
                newOtpCode[index] = value;
                setOtpCode(newOtpCode.join(""));

                if (value && index < 5) {
                  otpInputRefs.current[index + 1]?.focus(); // Move to next input
                }
              }}
              onKeyDown={(e) => {
                if (e.key === "Backspace" && index > 0 && !otpCode[index]) {
                  otpInputRefs.current[index - 1]?.focus(); // Move to previous input on backspace
                }
              }}
            />
          ))}
        </div>
        <div className="max-w-[260px] mx-auto mt-4">
          <button
            type="button"
            className="w-full inline-flex justify-center whitespace-nowrap rounded-lg bg-indigo-500 px-3.5 py-2.5 text-sm font-medium text-white shadow-sm shadow-indigo-950/10 hover:bg-indigo-600 focus:outline-none focus:ring focus:ring-indigo-300 transition-colors duration-150"
            onClick={handleVerifyOtp}
          >
            Verify OTP
          </button>
        </div>
      </div>
    )}

    {message && <p className="mt-4 text-sm text-slate-500">{message}</p>}
  </div>
)}
            {/* Navigation buttons */}
            <div className="mt-8 flex justify-between">
              {step > 1 && (
                <button
                  type="button"
                  onClick={handlePrevious}
                  className="p-3 text-white font-bold rounded bg-primary-turquoise hover:bg-secondary-darkgray"
                >
                  Previous
                </button>
              )}
             {step > 1 && step < 4 &&(
               <button
               type="button"
               onClick={handleNext}
               className={`p-3 ${isNextButtonDisabled() ? 'bg-red-300' : 'bg-primary-turquoise hover:bg-green-500'} text-white font-bold rounded`}
               disabled={isNextButtonDisabled()}
             >
               Next
             </button>
             )}
    {/* Submit Button */}
  {step == 4 &&(
      <button
        onClick={handleSubmit}
        disabled={!accepted}
        className={`px-6 py-2 text-white font-semibold rounded-md ${
          accepted ? 'bg-primary-turquoise hover:bg-green-500' : 'bg-red-300 cursor-not-allowed'
        }`}
      >
        Proceed to Authorisation
      </button>
)}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
