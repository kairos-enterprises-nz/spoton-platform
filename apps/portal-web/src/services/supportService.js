export async function getTickets() {
  await new Promise(resolve => setTimeout(resolve, 120));
  return [];
}

export async function createTicket(payload) {
  await new Promise(resolve => setTimeout(resolve, 120));
  return { id: 'TMP-0001', ...payload };
}

