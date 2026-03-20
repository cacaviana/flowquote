export type SlotsResponse = {
  date: string;
  available: string[];
  all_slots: string[];
  taken: string[];
  message?: string;
};

export type DaysResponse = {
  days: string[];
};

export type BookingSummary = {
  id: string;
  flow_id: string;
  flow_slug: string;
  client_name: string;
  client_email: string;
  client_phone: string | null;
  booking_date: string;
  booking_time: string;
  status: 'pending' | 'confirmed' | 'cancelled';
  has_answers: boolean;
  created_at: string;
};

export type BookingDetail = BookingSummary & {
  answers: { node_id: string; question: string; value: string }[];
};

export class BookingResponse {
  readonly id: string;
  readonly client_name: string;
  readonly booking_date: string;
  readonly booking_time: string;
  readonly status: string;

  constructor(raw: Record<string, unknown>) {
    this.id = String(raw.id ?? '');
    this.client_name = String(raw.client_name ?? '');
    this.booking_date = String(raw.booking_date ?? '');
    this.booking_time = String(raw.booking_time ?? '');
    this.status = String(raw.status ?? 'pending');
  }

  formatDate(): string {
    const [y, m, d] = this.booking_date.split('-');
    return `${d}/${m}/${y}`;
  }
}
