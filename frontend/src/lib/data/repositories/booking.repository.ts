import type { CreateBookingRequest } from '$lib/dto/booking/requests';
import type { SlotsResponse, DaysResponse, BookingSummary, BookingDetail } from '$lib/dto/booking/responses';

export class BookingRepository {
  async getAvailableDays(): Promise<DaysResponse> {
    const res = await fetch('/api/bookings/days');
    if (!res.ok) throw new Error('Erro ao buscar dias disponiveis');
    return res.json();
  }

  async getSlots(date: string): Promise<SlotsResponse> {
    const res = await fetch(`/api/bookings/slots?date=${date}`);
    if (!res.ok) throw new Error('Erro ao buscar horarios');
    return res.json();
  }

  async create(dto: CreateBookingRequest): Promise<BookingDetail> {
    const res = await fetch('/api/bookings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dto.toPayload()),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail ?? 'Erro ao criar agendamento');
    }
    return res.json();
  }

  async listAll(): Promise<{ bookings: BookingSummary[]; total: number }> {
    const res = await fetch('/api/bookings');
    if (!res.ok) throw new Error('Erro ao listar agendamentos');
    return res.json();
  }

  async listByFlow(flowId: string): Promise<{ bookings: BookingSummary[]; total: number }> {
    const res = await fetch(`/api/bookings/flow/${flowId}`);
    if (!res.ok) throw new Error('Erro ao listar agendamentos');
    return res.json();
  }

  async getById(id: string): Promise<BookingDetail | null> {
    const res = await fetch(`/api/bookings/${id}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error('Erro ao buscar agendamento');
    return res.json();
  }

  async remove(id: string): Promise<void> {
    const res = await fetch(`/api/bookings/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Erro ao remover agendamento');
  }
}
