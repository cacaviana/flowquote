import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const BACKEND = 'http://localhost:8001';

export const GET: RequestHandler = async ({ url }) => {
  const res = await fetch(`${BACKEND}/api/bookings${url.search}`);
  return json(await res.json());
};

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();
  const res = await fetch(`${BACKEND}/api/bookings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return json(data, { status: res.status });
};
