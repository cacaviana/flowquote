import { BookingRepository } from '$lib/data/repositories/booking.repository';
import { CreateBookingRequest } from '$lib/dto/booking/requests';
import type { SlotsResponse, DaysResponse, BookingSummary } from '$lib/dto/booking/responses';

export class BookingService {
  private repo = new BookingRepository();

  async getAvailableDays(): Promise<DaysResponse> {
    return await this.repo.getAvailableDays();
  }

  async getSlots(date: string): Promise<SlotsResponse> {
    return await this.repo.getSlots(date);
  }

  async book(data: {
    flow_id: string;
    flow_slug: string;
    client_name: string;
    client_email: string;
    client_phone?: string;
    booking_date: string;
    booking_time: string;
    answers?: Record<string, unknown>[];
  }) {
    const dto = new CreateBookingRequest(data);
    if (!dto.isValid()) throw new Error('Preencha todos os campos obrigatorios');
    return await this.repo.create(dto);
  }

  async listAll(): Promise<{ bookings: BookingSummary[]; total: number }> {
    return await this.repo.listAll();
  }

  async listByFlow(flowId: string): Promise<{ bookings: BookingSummary[]; total: number }> {
    return await this.repo.listByFlow(flowId);
  }

  async remove(id: string): Promise<void> {
    return await this.repo.remove(id);
  }
}
