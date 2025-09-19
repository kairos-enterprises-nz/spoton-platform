// src/components/UtilityDetails.js

import React, { useState, useEffect } from 'react';

export default function UtilityDetails() {
  const [utilities, setUtilities] = useState([]);
  const [loading, setLoading] = useState(true);

  // Placeholder utility data with additional info
  const placeholderData = [
    {
      id: 1,
      type: "Power",
      status: "Active",
      usage: 350, // kWh
      billAmount: 80.50, // $
      dueDate: "2025-04-15",
      lastPayment: "2025-03-01",
      provider: "ElectricCo",
    },
    {
      id: 2,
      type: "Gas",
      status: "Active",
      usage: 120, // kWh
      billAmount: 45.75, // $
      dueDate: "2025-04-20",
      lastPayment: "2025-03-10",
      provider: "GasWorks",
    },
    {
      id: 3,
      type: "Internet",
      status: "Active",
      usage: 300, // GB
      billAmount: 65.99, // $
      dueDate: "2025-04-25",
      lastPayment: "2025-03-15",
      provider: "WebNet",
    },
  ];

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      setUtilities(placeholderData);
      setLoading(false);
    }, 1000); // Simulate 1 second delay
  }, []);

  if (loading) {
    return (
      <div className="text-center text-xl">
        Loading Your Utility Details....
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6 bg-white shadow-lg rounded-lg">
      <h2 className="text-3xl font-semibold text-center text-primary-dark mb-6">Utilities</h2>
      {utilities.length > 0 ? (
        <div className="space-y-6">
          {utilities.map((utility) => (
            <div key={utility.id} className="bg-gray-50 p-4 rounded-lg shadow-sm">
              <h3 className="text-2xl font-bold text-primary-dark mb-2">{utility.type}</h3>
              <div className="space-y-2">
                <p className="text-lg"><strong>Status:</strong> {utility.status}</p>
                <p className="text-lg"><strong>Usage:</strong> {utility.usage} {utility.type === "Internet" ? "GB" : "kWh"}</p>
                <p className="text-lg"><strong>Bill Amount:</strong> ${utility.billAmount.toFixed(2)}</p>
                <p className="text-lg"><strong>Due Date:</strong> {utility.dueDate}</p>
                <p className="text-lg"><strong>Last Payment:</strong> {utility.lastPayment}</p>
                <p className="text-lg"><strong>Provider:</strong> {utility.provider}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>No utilities data available.</p>
      )}
    </div>
  );
}
