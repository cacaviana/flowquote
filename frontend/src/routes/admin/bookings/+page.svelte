<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { BookingService } from '$lib/services/booking.service';
  import type { BookingSummary } from '$lib/dto/booking/responses';

  const service = new BookingService();

  let bookings = $state<BookingSummary[]>([]);
  let loading = $state(true);
  let expanded = $state<string | null>(null);
  let expandedData = $state<Record<string, unknown> | null>(null);

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    confirmed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  };

  const statusLabel: Record<string, string> = {
    pending: 'Pendente',
    confirmed: 'Confirmado',
    cancelled: 'Cancelado',
  };

  onMount(async () => {
    const result = await service.listAll();
    bookings = result.bookings;
    loading = false;
  });

  async function expandBooking(id: string) {
    if (expanded === id) { expanded = null; return; }
    expanded = id;
    const res = await fetch(`/api/bookings/${id}`);
    expandedData = await res.json();
  }

  async function remove(id: string) {
    if (!confirm('Remover este agendamento?')) return;
    await service.remove(id);
    bookings = bookings.filter(b => b.id !== id);
  }

  function formatDate(d: string) {
    const [y, m, day] = d.split('-');
    return `${day}/${m}/${y}`;
  }
</script>

<div class="min-h-screen bg-gray-50">
  <header class="bg-white border-b px-6 py-4 flex items-center gap-3">
    <button
      onclick={() => goto('/admin/flows')}
      class="text-gray-400 hover:text-gray-700 transition-colors p-1 cursor-pointer"
      title="Voltar"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
      </svg>
    </button>
    <div class="h-5 w-px bg-gray-200"></div>
    <div>
      <h1 class="text-xl font-bold text-gray-900">FlowQuote</h1>
      <p class="text-sm text-gray-500">Agendamentos</p>
    </div>
    <div class="ml-auto text-sm text-gray-500">{bookings.length} agendamento(s)</div>
  </header>

  <main class="max-w-4xl mx-auto p-6">
    {#if loading}
      <div class="text-center py-16 text-gray-400">Carregando...</div>
    {:else if bookings.length === 0}
      <div class="text-center py-16 text-gray-400">
        <svg class="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 9v7.5" />
        </svg>
        <p>Nenhum agendamento ainda</p>
      </div>
    {:else}
      <div class="space-y-3">
        {#each bookings as b}
          <div class="bg-white rounded-xl border overflow-hidden">
            <div class="p-4 flex items-center gap-4">
              <!-- Data destaque -->
              <div class="text-center bg-blue-50 rounded-lg px-3 py-2 shrink-0">
                <div class="text-xs text-blue-500 font-medium uppercase">
                  {new Date(b.booking_date + 'T12:00:00').toLocaleDateString('pt-BR', { weekday: 'short' })}
                </div>
                <div class="text-xl font-bold text-blue-700">{b.booking_date.split('-')[2]}</div>
                <div class="text-xs text-blue-500">
                  {new Date(b.booking_date + 'T12:00:00').toLocaleDateString('pt-BR', { month: 'short' })}
                </div>
              </div>

              <!-- Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-semibold text-gray-900 truncate">{b.client_name}</span>
                  <span class="text-xs px-2 py-0.5 rounded-full font-medium {statusColors[b.status] ?? 'bg-gray-100 text-gray-600'}">
                    {statusLabel[b.status] ?? b.status}
                  </span>
                </div>
                <div class="text-sm text-gray-500 truncate">{b.client_email}</div>
                <div class="flex items-center gap-3 mt-1 text-xs text-gray-400">
                  <span>🕐 {b.booking_time}</span>
                  <span>📋 {b.flow_slug}</span>
                  {#if b.has_answers}
                    <span>💬 com respostas</span>
                  {/if}
                </div>
              </div>

              <!-- Ações -->
              <div class="flex items-center gap-2 shrink-0">
                {#if b.has_answers}
                  <button
                    onclick={() => expandBooking(b.id)}
                    class="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded border border-blue-200 hover:bg-blue-50 cursor-pointer transition-colors"
                  >
                    {expanded === b.id ? 'Fechar' : 'Ver respostas'}
                  </button>
                {/if}
                <button
                  onclick={() => remove(b.id)}
                  class="text-gray-300 hover:text-red-400 cursor-pointer transition-colors p-1"
                  title="Remover"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Respostas expandidas -->
            {#if expanded === b.id && expandedData}
              <div class="border-t bg-gray-50 px-4 py-3">
                <p class="text-xs font-semibold text-gray-500 uppercase mb-2">Respostas do formulário</p>
                <div class="space-y-1">
                  {#each (expandedData.answers as {question: string; value: string}[]) ?? [] as a}
                    <div class="text-sm">
                      <span class="text-gray-500">{a.question}:</span>
                      <span class="text-gray-800 font-medium ml-1">{a.value}</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </main>
</div>
