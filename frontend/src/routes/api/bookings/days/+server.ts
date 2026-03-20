import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const BACKEND = 'http://localhost:8001';

export const GET: RequestHandler = async () => {
  const res = await fetch(`${BACKEND}/api/bookings/days`);
  return json(await res.json());
};
