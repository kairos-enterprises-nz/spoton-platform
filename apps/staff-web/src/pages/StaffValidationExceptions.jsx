import { useState, useEffect } from 'react';
import staffApi from '../services/staffApi';

const StaffValidationExceptions = () => {
    const [exceptions, setExceptions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const getExceptions = async () => {
        try {
            setLoading(true);
            const data = await staffApi.getValidationExceptions();
            setExceptions(data);
        } catch (err) {
            setError('Failed to load validation exceptions.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        getExceptions();
    }, []);

    const handleOverride = async (exceptionId) => {
        try {
            await staffApi.overrideValidationException(exceptionId);
            alert(`Exception ${exceptionId} overridden successfully!`);
            // Refresh the list
            getExceptions();
        } catch (err) {
            alert(`Failed to override exception ${exceptionId}.`);
            console.error(err);
        }
    };

    if (loading) return <div className="p-4">Loading...</div>;
    if (error) return <div className="p-4 text-red-500">{error}</div>;

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="p-6">
                <h1 className="text-2xl font-bold mb-4">Validation Exceptions</h1>
                <div className="bg-white shadow rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Meter ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rule Failed</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {exceptions.map(ex => (
                                <tr key={ex.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">{ex.meter_id}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{ex.rule_name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{new Date(ex.timestamp).toLocaleString()}</td>
                                    <td className="px-6 py-4">{ex.details}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${ex.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                                            {ex.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {ex.status === 'pending' && (
                                            <button 
                                                onClick={() => handleOverride(ex.id)}
                                                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                                            >
                                                Override
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
        </div>
      </div>
    );
};

export default StaffValidationExceptions; 