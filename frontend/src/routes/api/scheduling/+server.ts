import { json } from '@sveltejs/kit';
import { getDb } from '$lib/server/db';
import type { RequestHandler } from './$types';

// Mock available slots (business hours 09:00-18:00, 30min intervals, lunch 12-14)
const ALL_SLOTS = [
	'09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
	'14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30'
];

/** GET /api/scheduling?action=dates&month=3&year=2026  or  ?action=slots&date=2026-03-25 */
export const GET: RequestHandler = async ({ url }) => {
	const action = url.searchParams.get('action');

	if (action === 'dates') {
		const month = parseInt(url.searchParams.get('month') || '0');
		const year = parseInt(url.searchParams.get('year') || '0');
		if (!month || !year) return json({ error: 'month and year required' }, { status: 400 });

		const db = await getDb();
		// Get existing bookings for this month to know which slots are taken
		const startDate = `${year}-${String(month).padStart(2, '0')}-01`;
		const endDate = `${year}-${String(month).padStart(2, '0')}-31`;

		const bookings = await db.collection('scheduling')
			.find({ scheduled_date: { $gte: startDate, $lte: endDate }, status: { $ne: 'cancelled' } })
			.toArray();

		// Count bookings per day
		const bookingsPerDay: Record<string, number> = {};
		for (const b of bookings) {
			const d = b.scheduled_date;
			bookingsPerDay[d] = (bookingsPerDay[d] || 0) + 1;
		}

		const daysInMonth = new Date(year, month, 0).getDate();
		const today = new Date();
		today.setHours(0, 0, 0, 0);

		const dates = [];
		for (let day = 1; day <= daysInMonth; day++) {
			const d = new Date(year, month - 1, day);
			const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
			const isWeekday = d.getDay() > 0 && d.getDay() < 6;
			const isFuture = d >= today;
			const booked = bookingsPerDay[dateStr] || 0;
			const freeSlots = Math.max(0, ALL_SLOTS.length - booked);

			dates.push({
				date: dateStr,
				available: isWeekday && isFuture && freeSlots > 0,
				slots_count: isWeekday && isFuture ? freeSlots : 0
			});
		}

		return json(dates);
	}

	if (action === 'slots') {
		const date = url.searchParams.get('date');
		if (!date) return json({ error: 'date required' }, { status: 400 });

		const db = await getDb();
		const bookings = await db.collection('scheduling')
			.find({ scheduled_date: date, status: { $ne: 'cancelled' } })
			.toArray();

		const bookedTimes = new Set(bookings.map((b: any) => b.scheduled_time));
		const available = ALL_SLOTS.filter(s => !bookedTimes.has(s));

		return json(available);
	}

	// List all (admin)
	const db = await getDb();
	const all = await db.collection('scheduling')
		.find()
		.sort({ created_at: -1 })
		.limit(200)
		.toArray();

	return json(all.map(s => ({ ...s, id: s._id.toString(), _id: undefined })));
};

/** POST /api/scheduling — Create a new scheduling */
export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();
	const db = await getDb();

	const doc = {
		flow_id: body.flow_id || null,
		flow_slug: body.flow_slug || null,
		lead_name: body.lead_name,
		lead_email: body.lead_email,
		lead_phone: body.lead_phone || null,
		lead_address: body.lead_address || null,
		qualifying_answers: body.qualifying_answers || [],
		scheduled_date: body.scheduled_date,
		scheduled_time: body.scheduled_time,
		timezone: 'America/Sao_Paulo',
		duration_minutes: 30,
		gcal_event_id: null,
		gcal_event_link: null,
		webhook_sent: false,
		status: 'confirmed',
		created_at: new Date().toISOString()
	};

	// TODO: Google Calendar integration — create event
	// TODO: Webhook (WhatsApp) — send notification

	const result = await db.collection('scheduling').insertOne(doc);

	return json({
		id: result.insertedId.toString(),
		...doc,
		message: 'Agendamento confirmado! Você receberá uma confirmação em breve.'
	}, { status: 201 });
};
