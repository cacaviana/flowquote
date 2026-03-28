import { json, error } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8001';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();

	try {
		const res = await fetch(`${BACKEND_URL}/api/submissions`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body)
		});

		if (!res.ok) {
			const errBody = await res.text();
			throw error(res.status, `Erreur backend: ${errBody}`);
		}

		const result = await res.json();
		return json({
			quote_text: result.quote_text ?? null,
			quote_data: result.quote_data ?? null
		});
	} catch (e: any) {
		console.error('[generate-quote] Error:', e.message);
		throw error(500, `Erreur lors de la génération du devis: ${e.message}`);
	}
};
