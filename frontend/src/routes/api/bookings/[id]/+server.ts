import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const BACKEND = 'http://localhost:8001';

export const GET: RequestHandler = async ({ params }) => {
  const res = await fetch(`${BACKEND}/api/bookings/${params.id}`);
  return json(await res.json(), { status: res.status });
};

export const DELETE: RequestHandler = async ({ params }) => {
  const res = await fetch(`${BACKEND}/api/bookings/${params.id}`, { method: 'DELETE' });
  return new Response(null, { status: res.status });
};
