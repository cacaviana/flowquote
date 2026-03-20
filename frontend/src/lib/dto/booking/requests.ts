export class CreateBookingRequest {
  readonly flow_id: string;
  readonly flow_slug: string;
  readonly client_name: string;
  readonly client_email: string;
  readonly client_phone: string;
  readonly booking_date: string;
  readonly booking_time: string;
  readonly answers: Record<string, unknown>[];

  constructor(data: {
    flow_id: string;
    flow_slug: string;
    client_name: string;
    client_email: string;
    client_phone?: string;
    booking_date: string;
    booking_time: string;
    answers?: Record<string, unknown>[];
  }) {
    this.flow_id = data.flow_id;
    this.flow_slug = data.flow_slug;
    this.client_name = data.client_name;
    this.client_email = data.client_email;
    this.client_phone = data.client_phone ?? '';
    this.booking_date = data.booking_date;
    this.booking_time = data.booking_time;
    this.answers = data.answers ?? [];
  }

  isValid(): boolean {
    return (
      this.flow_id.trim() !== '' &&
      this.client_name.trim() !== '' &&
      this.client_email.includes('@') &&
      this.booking_date !== '' &&
      this.booking_time !== ''
    );
  }

  toPayload(): Record<string, unknown> {
    return {
      flow_id: this.flow_id,
      flow_slug: this.flow_slug,
      client_name: this.client_name,
      client_email: this.client_email,
      client_phone: this.client_phone || null,
      booking_date: this.booking_date,
      booking_time: this.booking_time,
      answers: this.answers,
    };
  }
}
