import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const BACKEND = 'http://localhost:8001';

export const GET: RequestHandler = async ({ url }) => {
  const date = url.searchParams.get('date') ?? '';
  const res = await fetch(`${BACKEND}/api/bookings/slots?date=${date}`);
  return json(await res.json());
};
