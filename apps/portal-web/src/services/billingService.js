export async function getSummary() {
  await new Promise(resolve => setTimeout(resolve, 150));
  return {
    currentBalance: 0,
    totalPaid: 0,
    averageBill: 0,
    highestBill: 0
  };
}

export async function getHistory(period = '6months') {
  await new Promise(resolve => setTimeout(resolve, 150));
  return [];
}

export async function getSchedule() {
  await new Promise(resolve => setTimeout(resolve, 150));
  return {
    cycle: '15th of each month',
    nextBillDate: new Date().toISOString(),
    autopay: true
  };
}

