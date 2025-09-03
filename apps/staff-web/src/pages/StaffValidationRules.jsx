import { useState, useEffect } from 'react';
import staffApi from '../services/staffApi';

const StaffValidationRules = () => {
    const [rules, setRules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const getRules = async () => {
            try {
                const data = await staffApi.getValidationRules();
                setRules(data);
            } catch (err) {
                setError('Failed to load validation rules.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        getRules();
    }, []);

    const handleThresholdChange = (ruleId, thresholdName, value) => {
        setRules(rules.map(rule => 
            rule.id === ruleId 
                ? { ...rule, parameters: { ...rule.parameters, [thresholdName]: value } }
                : rule
        ));
    };

    const handleSave = async (rule) => {
        try {
            await staffApi.updateValidationRule(rule.id, rule);
            alert(`Rule "${rule.name}" updated successfully!`);
        } catch (err) {
            alert(`Failed to update rule "${rule.name}".`);
            console.error(err);
        }
    };

    if (loading) return <div className="p-4">Loading...</div>;
    if (error) return <div className="p-4 text-red-500">{error}</div>;

    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="p-6">
                <h1 className="text-2xl font-bold mb-4">Manage Validation Rules</h1>
                <div className="bg-white shadow rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rule Name</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Thresholds</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {rules.map(rule => (
                                <tr key={rule.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">{rule.name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{rule.description}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {rule.parameters && Object.entries(rule.parameters).map(([key, value]) => (
                                            <div key={key} className="flex items-center mb-2">
                                                <label className="mr-2 text-sm">{key}:</label>
                                                <input 
                                                    type="number"
                                                    value={value}
                                                    onChange={(e) => handleThresholdChange(rule.id, key, e.target.value)}
                                                    className="w-24 border-gray-300 rounded-md shadow-sm"
                                                />
                                            </div>
                                        ))}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${rule.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                            {rule.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <button 
                                            onClick={() => handleSave(rule)}
                                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                        >
                                            Save
                                        </button>
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

export default StaffValidationRules; 