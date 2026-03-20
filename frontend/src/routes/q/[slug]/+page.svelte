<script lang="ts">
  import { page } from '$app/state';
  import { onMount } from 'svelte';
  import { FlowsService } from '$lib/services/flows.service';
  import { SubmissionsService } from '$lib/services/submissions.service';
  import { BookingService } from '$lib/services/booking.service';
  import type { Flow, FlowNode, FlowEdge } from '$lib/dto/flows/types';

  const flowService = new FlowsService();
  const submissionService = new SubmissionsService();
  const bookingService = new BookingService();

  let flow = $state<Flow | null>(null);
  let loading = $state(true);
  let error = $state('');

  // Fases do fluxo
  let phase = $state<'intro' | 'questions' | 'booking' | 'end'>('intro');
  let animating = $state(false);
  let animDir = $state<'forward' | 'back'>('forward');

  // Dados do cliente
  let clientData = $state({ name: '', email: '', phone: '', address: '' });

  // Navegação
  let currentNodeId = $state<string | null>(null);
  let answers = $state<{ node_id: string; question: string; value: string }[]>([]);
  let endNode = $state<FlowNode | null>(null);
  let submitting = $state(false);
  let inputValue = $state('');

  // Quote result
  let quoteData = $state<{
    items: { description: string; unit_price: number; quantity: number; subtotal: number }[];
    subtotal: number; taxes_tps: number; taxes_tvq: number; total: number;
    recommendations: string; notes: string;
  } | null>(null);
  let resultText = $state('');
  let resultType = $state<'quote' | 'fallback' | 'error' | ''>('');

  // Booking
  let availableDays = $state<string[]>([]);
  let selectedDay = $state('');
  let availableSlots = $state<string[]>([]);
  let selectedSlot = $state('');
  let loadingSlots = $state(false);
  let bookingResult = $state<{ id: string; booking_date: string; booking_time: string } | null>(null);
  let bookingError = $state('');

  let currentNode = $derived(flow?.nodes.find(n => n.id === currentNodeId) || null);
  let totalQuestions = $derived(flow?.nodes.filter(n => n.type === 'question').length || 0);
  let answeredCount = $derived(answers.length);
  let progressPercent = $derived(totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0);

  onMount(async () => {
    try {
      const slug = page.params.slug;
      if (slug) flow = await flowService.getBySlug(slug);
      if (!flow) error = 'Questionnaire non trouvé';
    } catch (e: unknown) {
      error = (e as Error).message;
    } finally {
      loading = false;
    }
  });

  function startQuestions() {
    if (!clientData.name.trim() || !clientData.email.trim()) return;
    phase = 'questions';
    const startNode = flow!.nodes.find(n => n.type === 'start');
    if (!startNode) return;
    const edge = flow!.edges.find(e => e.source === startNode.id);
    if (edge) { currentNodeId = edge.target; processCurrentNode(); }
  }

  function processCurrentNode() {
    if (!currentNode) return;
    if (currentNode.type === 'message') {
      setTimeout(() => {
        const edge = flow!.edges.find(e => e.source === currentNodeId);
        if (edge) { currentNodeId = edge.target; processCurrentNode(); }
      }, 2000);
    } else if (currentNode.type === 'end') {
      endNode = currentNode;
      if (currentNode.data.endType === 'booking') {
        phase = 'booking';
        loadBookingDays();
      } else {
        phase = 'end';
        submitToBackend();
      }
    }
  }

  async function loadBookingDays() {
    const result = await bookingService.getAvailableDays();
    availableDays = result.days;
    if (availableDays.length > 0) {
      selectedDay = availableDays[0];
      await loadSlots(selectedDay);
    }
  }

  async function loadSlots(date: string) {
    loadingSlots = true;
    selectedSlot = '';
    const result = await bookingService.getSlots(date);
    availableSlots = result.available;
    loadingSlots = false;
  }

  async function selectDay(d: string) {
    selectedDay = d;
    await loadSlots(d);
  }

  async function confirmBooking() {
    if (!selectedDay || !selectedSlot || !flow || !endNode) return;
    submitting = true;
    bookingError = '';
    try {
      const result = await bookingService.book({
        flow_id: flow._id || '',
        flow_slug: flow.slug,
        client_name: clientData.name,
        client_email: clientData.email,
        client_phone: clientData.phone || undefined,
        booking_date: selectedDay,
        booking_time: selectedSlot,
        answers: answers as unknown as Record<string, unknown>[],
      });
      bookingResult = result as { id: string; booking_date: string; booking_time: string };
    } catch (e: unknown) {
      bookingError = (e as Error).message;
    } finally {
      submitting = false;
    }
  }

  async function submitToBackend() {
    if (!flow || !endNode) return;
    submitting = true;
    try {
      const payload = {
        flow_id: flow._id || '', flow_slug: flow.slug,
        client_name: clientData.name, client_email: clientData.email,
        client_phone: clientData.phone || undefined,
        client_address: clientData.address || undefined,
        answers, end_node_id: endNode.id,
      };
      if (endNode.data.endType === 'quote') {
        const res = await fetch('/api/generate-quote', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const r = await res.json();
          quoteData = r.quote_data || null;
          resultText = r.quote_text || '';
          resultType = quoteData ? 'quote' : 'fallback';
        } else {
          const r = await submissionService.submit(payload);
          resultText = r.quote_text || 'Votre demande a été enregistrée. Un spécialiste vous contactera.';
          resultType = 'fallback';
        }
      } else {
        const r = await submissionService.submit(payload);
        resultText = r.quote_text || 'Votre demande a été enregistrée. Merci!';
        resultType = 'fallback';
      }
    } catch {
      resultText = 'Erreur lors de l\'envoi. Veuillez réessayer.';
      resultType = 'error';
    } finally {
      submitting = false;
    }
  }

  async function selectAnswer(value: string | number, handleId?: string) {
    if (!currentNode) return;
    animDir = 'forward';
    animating = true;
    await tick();
    answers = [...answers, { node_id: currentNode.id, question: currentNode.data.title, value: String(value) }];
    let nextEdge: FlowEdge | undefined;
    if (handleId) nextEdge = flow!.edges.find(e => e.source === currentNodeId && e.sourceHandle === handleId);
    if (!nextEdge) nextEdge = flow!.edges.find(e => e.source === currentNodeId && !e.sourceHandle);
    if (!nextEdge) nextEdge = flow!.edges.find(e => e.source === currentNodeId);
    if (nextEdge) { currentNodeId = nextEdge.target; processCurrentNode(); }
    setTimeout(() => { animating = false; }, 300);
  }

  async function goBack() {
    animDir = 'back';
    animating = true;
    await tick();
    if (answers.length === 0) { phase = 'intro'; animating = false; return; }
    const last = answers[answers.length - 1];
    answers = answers.slice(0, -1);
    currentNodeId = last.node_id;
    phase = 'questions';
    endNode = null;
    setTimeout(() => { animating = false; }, 300);
  }

  function formatCurrency(val: number): string {
    return val.toLocaleString('fr-CA', { style: 'currency', currency: 'CAD' });
  }

  function formatDay(d: string) {
    const dt = new Date(d + 'T12:00:00');
    return dt.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: 'short' });
  }

  function formatDayShort(d: string) {
    return new Date(d + 'T12:00:00').toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  }

  import { tick } from 'svelte';
</script>

<svelte:head>
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
  <style>
    @media print {
      body * { visibility: hidden; }
      .quote-print, .quote-print * { visibility: visible; }
      .quote-print { position: absolute; left: 0; top: 0; width: 100%; }
      .no-print { display: none !important; }
    }
  </style>
</svelte:head>

<!-- TELA FULL-SCREEN TYPEFORM -->
<div class="min-h-screen bg-white flex flex-col" style="font-family: -apple-system, 'Helvetica Neue', sans-serif;">

  {#if loading}
    <div class="flex-1 flex items-center justify-center">
      <div class="w-8 h-8 border-2 border-gray-900 border-t-transparent rounded-full animate-spin"></div>
    </div>

  {:else if error}
    <div class="flex-1 flex items-center justify-center p-8 text-center">
      <p class="text-gray-500">{error}</p>
    </div>

  {:else if phase === 'intro'}
    <!-- TELA INICIAL -->
    <div class="flex-1 flex flex-col justify-center px-8 py-12 max-w-lg mx-auto w-full">
      <div class="mb-10">
        <h1 class="text-3xl font-bold text-gray-900 leading-tight mb-3">{flow?.name}</h1>
        <p class="text-gray-500 text-lg">Preencha em menos de 2 minutos</p>
      </div>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nome completo *</label>
          <input
            type="text"
            bind:value={clientData.name}
            placeholder="Seu nome"
            class="w-full border-0 border-b-2 border-gray-200 focus:border-gray-900 outline-none py-3 text-lg text-gray-900 bg-transparent transition-colors placeholder-gray-300"
          />
        </div>
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">E-mail *</label>
          <input
            type="email"
            bind:value={clientData.email}
            placeholder="seu@email.com"
            class="w-full border-0 border-b-2 border-gray-200 focus:border-gray-900 outline-none py-3 text-lg text-gray-900 bg-transparent transition-colors placeholder-gray-300"
          />
        </div>
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Telefone</label>
          <input
            type="tel"
            bind:value={clientData.phone}
            placeholder="(00) 00000-0000"
            class="w-full border-0 border-b-2 border-gray-200 focus:border-gray-900 outline-none py-3 text-lg text-gray-900 bg-transparent transition-colors placeholder-gray-300"
          />
        </div>
      </div>

      <button
        onclick={startQuestions}
        disabled={!clientData.name.trim() || !clientData.email.trim()}
        class="mt-10 w-full bg-gray-900 text-white py-4 rounded-2xl text-base font-semibold hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
      >
        Começar →
      </button>

      <p class="text-center text-xs text-gray-400 mt-4">Seus dados são protegidos e não serão compartilhados</p>
    </div>

  {:else if phase === 'questions' && currentNode}
    <!-- PROGRESS BAR -->
    <div class="h-1 bg-gray-100 fixed top-0 left-0 right-0 z-10">
      <div
        class="h-full bg-gray-900 transition-all duration-500 ease-out"
        style="width: {progressPercent}%"
      ></div>
    </div>

    <!-- QUESTÃO TYPEFORM -->
    <div class="flex-1 flex flex-col justify-center px-8 py-16 max-w-lg mx-auto w-full"
      style="opacity: {animating ? 0 : 1}; transform: translateY({animating ? (animDir === 'forward' ? '20px' : '-20px') : '0'}); transition: opacity 0.25s, transform 0.25s;">

      {#if currentNode.type === 'message'}
        <div class="text-center">
          <div class="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-5">
            <svg class="w-7 h-7 text-gray-500" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
          </div>
          <h2 class="text-2xl font-bold text-gray-900 mb-3">{currentNode.data.title}</h2>
          {#if currentNode.data.message}
            <p class="text-gray-500 text-lg">{currentNode.data.message}</p>
          {/if}
          <div class="mt-6 flex justify-center">
            <div class="w-6 h-6 border-2 border-gray-300 border-t-gray-700 rounded-full animate-spin"></div>
          </div>
        </div>

      {:else}
        <!-- Número da pergunta -->
        <p class="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-widest">
          {answeredCount + 1} / {totalQuestions}
        </p>
        <h2 class="text-2xl font-bold text-gray-900 mb-2 leading-tight">{currentNode.data.title}</h2>
        {#if currentNode.data.tooltip}
          <p class="text-gray-400 text-base mb-8">{currentNode.data.tooltip}</p>
        {:else}
          <div class="mb-8"></div>
        {/if}

        {#if currentNode.data.questionType === 'single_choice' && currentNode.data.options}
          <div class="space-y-3">
            {#each currentNode.data.options as opt, i}
              <button
                onclick={() => selectAnswer(opt.value, opt.id)}
                class="w-full text-left flex items-center gap-4 border-2 border-gray-200 hover:border-gray-900 rounded-2xl px-5 py-4 transition-all cursor-pointer group"
              >
                <span class="w-7 h-7 flex items-center justify-center rounded-lg border-2 border-gray-200 group-hover:border-gray-900 text-xs font-bold text-gray-400 group-hover:text-gray-900 transition-colors shrink-0">
                  {String.fromCharCode(65 + i)}
                </span>
                <span class="text-base font-medium text-gray-800">{opt.label}</span>
              </button>
            {/each}
          </div>

        {:else if currentNode.data.questionType === 'yes_no'}
          <div class="flex gap-3">
            <button
              onclick={() => selectAnswer('Sim', 'yes')}
              class="flex-1 border-2 border-gray-200 hover:border-gray-900 hover:bg-gray-900 hover:text-white rounded-2xl py-5 text-center text-base font-semibold text-gray-800 transition-all cursor-pointer"
            >
              Sim
            </button>
            <button
              onclick={() => selectAnswer('Não', 'no')}
              class="flex-1 border-2 border-gray-200 hover:border-gray-200 hover:bg-gray-100 rounded-2xl py-5 text-center text-base font-semibold text-gray-800 transition-all cursor-pointer"
            >
              Não
            </button>
          </div>

        {:else if currentNode.data.questionType === 'number'}
          <div class="space-y-4">
            <input
              type="number"
              bind:value={inputValue}
              placeholder="Digite um número"
              class="w-full border-0 border-b-2 border-gray-200 focus:border-gray-900 outline-none py-3 text-2xl text-gray-900 bg-transparent transition-colors"
              onkeydown={(e) => { if (e.key === 'Enter' && inputValue) { selectAnswer(inputValue); inputValue = ''; } }}
            />
            <button
              onclick={() => { selectAnswer(inputValue); inputValue = ''; }}
              disabled={!inputValue}
              class="bg-gray-900 text-white px-8 py-3.5 rounded-xl font-semibold text-sm hover:bg-gray-800 disabled:opacity-30 cursor-pointer transition-colors"
            >
              OK ↵
            </button>
          </div>

        {:else}
          <div class="space-y-4">
            <input
              type="text"
              bind:value={inputValue}
              placeholder="Sua resposta"
              class="w-full border-0 border-b-2 border-gray-200 focus:border-gray-900 outline-none py-3 text-2xl text-gray-900 bg-transparent transition-colors placeholder-gray-300"
              onkeydown={(e) => { if (e.key === 'Enter' && inputValue.trim()) { selectAnswer(inputValue); inputValue = ''; } }}
            />
            <button
              onclick={() => { selectAnswer(inputValue); inputValue = ''; }}
              disabled={!inputValue.trim()}
              class="bg-gray-900 text-white px-8 py-3.5 rounded-xl font-semibold text-sm hover:bg-gray-800 disabled:opacity-30 cursor-pointer transition-colors"
            >
              OK ↵
            </button>
          </div>
        {/if}
      {/if}
    </div>

    <!-- BOTÃO VOLTAR -->
    <div class="px-8 pb-8 max-w-lg mx-auto w-full no-print">
      <button
        onclick={goBack}
        class="text-sm text-gray-400 hover:text-gray-700 cursor-pointer transition-colors flex items-center gap-1.5"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        Voltar
      </button>
    </div>

  {:else if phase === 'booking'}
    <!-- TELA DE AGENDAMENTO -->
    {#if bookingResult}
      <!-- CONFIRMAÇÃO -->
      <div class="flex-1 flex flex-col items-center justify-center px-8 py-16 text-center max-w-lg mx-auto w-full">
        <div class="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>
        <h2 class="text-3xl font-bold text-gray-900 mb-3">Agendado!</h2>
        <p class="text-gray-500 text-lg mb-6">
          {clientData.name}, sua reunião está confirmada para
        </p>
        <div class="bg-gray-50 rounded-2xl p-6 w-full">
          <p class="text-3xl font-bold text-gray-900">{formatDay(bookingResult.booking_date)}</p>
          <p class="text-2xl font-semibold text-gray-600 mt-1">às {bookingResult.booking_time}</p>
        </div>
        <p class="text-sm text-gray-400 mt-6">Você receberá uma confirmação em {clientData.email}</p>
      </div>

    {:else}
      <div class="h-1 bg-gray-100 fixed top-0 left-0 right-0 z-10">
        <div class="h-full bg-gray-900" style="width: 100%"></div>
      </div>

      <div class="flex-1 px-8 py-16 max-w-lg mx-auto w-full">
        <p class="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-widest">Última etapa</p>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Escolha um horário</h2>
        <p class="text-gray-400 text-base mb-8">Selecione o dia e horário para conversar com nosso especialista</p>

        <!-- Seletor de dias (scroll horizontal) -->
        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Dia</p>
        <div class="flex gap-2 overflow-x-auto pb-2 -mx-2 px-2 mb-8">
          {#each availableDays as day}
            <button
              onclick={() => selectDay(day)}
              class="shrink-0 flex flex-col items-center justify-center px-4 py-3 rounded-2xl border-2 transition-all cursor-pointer min-w-16
                {selectedDay === day ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-200 text-gray-700 hover:border-gray-400'}"
            >
              <span class="text-xs font-medium opacity-70 uppercase">
                {new Date(day + 'T12:00:00').toLocaleDateString('pt-BR', { weekday: 'short' })}
              </span>
              <span class="text-xl font-bold">{new Date(day + 'T12:00:00').getDate()}</span>
              <span class="text-xs opacity-70">
                {new Date(day + 'T12:00:00').toLocaleDateString('pt-BR', { month: 'short' })}
              </span>
            </button>
          {/each}
        </div>

        <!-- Slots de horário -->
        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Horário</p>
        {#if loadingSlots}
          <div class="flex items-center gap-2 text-gray-400 text-sm py-4">
            <div class="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin"></div>
            Carregando horários...
          </div>
        {:else if availableSlots.length === 0}
          <p class="text-gray-400 text-base py-4">Nenhum horário disponível neste dia. Tente outra data.</p>
        {:else}
          <div class="grid grid-cols-3 gap-2 mb-8">
            {#each availableSlots as slot}
              <button
                onclick={() => selectedSlot = slot}
                class="py-3.5 rounded-xl border-2 text-sm font-semibold transition-all cursor-pointer
                  {selectedSlot === slot ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-200 text-gray-700 hover:border-gray-400'}"
              >
                {slot}
              </button>
            {/each}
          </div>
        {/if}

        {#if bookingError}
          <div class="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3 mb-4">
            {bookingError}
          </div>
        {/if}

        <button
          onclick={confirmBooking}
          disabled={!selectedDay || !selectedSlot || submitting}
          class="w-full bg-gray-900 text-white py-4 rounded-2xl text-base font-semibold hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
        >
          {submitting ? 'Confirmando...' : 'Confirmar agendamento'}
        </button>
      </div>

      <div class="px-8 pb-8 max-w-lg mx-auto w-full">
        <button onclick={goBack} class="text-sm text-gray-400 hover:text-gray-700 cursor-pointer transition-colors flex items-center gap-1.5">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Voltar
        </button>
      </div>
    {/if}

  {:else if phase === 'end' && endNode}
    <!-- FASE FINAL -->
    {#if submitting}
      <div class="flex-1 flex flex-col items-center justify-center px-8 text-center">
        <div class="w-12 h-12 border-2 border-gray-900 border-t-transparent rounded-full animate-spin mb-6"></div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Gerando seu orçamento...</h3>
        <p class="text-gray-400">Nossa IA está analisando suas respostas</p>
      </div>

    {:else if endNode.data.endType === 'specialist'}
      <div class="flex-1 flex flex-col items-center justify-center px-8 py-16 text-center max-w-lg mx-auto w-full">
        <div class="w-20 h-20 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
          </svg>
        </div>
        <h2 class="text-3xl font-bold text-gray-900 mb-3">{endNode.data.title}</h2>
        <p class="text-gray-500 text-lg mb-6">{endNode.data.message}</p>
        <div class="bg-green-50 border border-green-200 rounded-2xl p-4 text-sm text-green-700 w-full">
          Seus dados foram registrados. Entraremos em contato em até 24h.
        </div>
      </div>

    {:else if endNode.data.endType === 'quote' && quoteData}
      <!-- DEVIS PROFISSIONAL -->
      <div class="quote-print max-w-lg mx-auto w-full">
        <div class="bg-gray-900 text-white px-6 py-6">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-xl font-bold">Devis estimatif</h3>
              <p class="text-gray-400 text-sm mt-0.5">Total Electrique</p>
            </div>
            <div class="w-10 h-10 bg-white/10 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p class="font-semibold">{clientData.name}</p>
          {#if clientData.address}<p class="text-gray-400 text-sm">{clientData.address}</p>{/if}
        </div>

        <div class="px-6 py-4">
          <table class="w-full text-sm" data-testid="quote-items-table">
            <thead>
              <tr class="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100">
                <th class="text-left py-2 font-medium">Produto / Serviço</th>
                <th class="text-center py-2 font-medium w-10">Qtd</th>
                <th class="text-right py-2 font-medium">Preço</th>
              </tr>
            </thead>
            <tbody>
              {#each quoteData.items as item}
                <tr class="border-b border-gray-50">
                  <td class="py-3 text-gray-800 font-medium pr-2">{item.description}</td>
                  <td class="py-3 text-center text-gray-500">{item.quantity}</td>
                  <td class="py-3 text-right font-semibold tabular-nums {item.subtotal === 0 ? 'text-amber-500 italic text-xs' : 'text-gray-900'}">
                    {item.subtotal === 0 ? 'A consulter' : formatCurrency(item.subtotal)}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <div class="px-6 pb-4">
          <div class="bg-gray-50 rounded-2xl p-4 space-y-1.5">
            <div class="flex justify-between text-sm text-gray-600"><span>Sous-total</span><span class="tabular-nums">{formatCurrency(quoteData.subtotal)}</span></div>
            <div class="flex justify-between text-sm text-gray-400"><span>TPS (5%)</span><span class="tabular-nums">{formatCurrency(quoteData.taxes_tps)}</span></div>
            <div class="flex justify-between text-sm text-gray-400"><span>TVQ (9,975%)</span><span class="tabular-nums">{formatCurrency(quoteData.taxes_tvq)}</span></div>
            <div class="border-t border-gray-200 pt-2 flex justify-between text-base font-bold"><span>Total</span><span class="tabular-nums text-gray-900">{formatCurrency(quoteData.total)}</span></div>
          </div>
        </div>

        {#if quoteData.recommendations}
          <div class="px-6 pb-4">
            <div class="bg-blue-50 rounded-2xl p-4">
              <p class="text-xs font-bold text-blue-700 uppercase tracking-wide mb-1">Recommandations</p>
              <p class="text-xs text-blue-800 leading-relaxed">{quoteData.recommendations}</p>
            </div>
          </div>
        {/if}

        {#if quoteData.notes}
          <div class="px-6 pb-4">
            <div class="bg-amber-50 rounded-2xl p-4">
              <p class="text-xs font-bold text-amber-700 uppercase tracking-wide mb-1">Notes</p>
              <p class="text-xs text-amber-800 leading-relaxed">{quoteData.notes}</p>
            </div>
          </div>
        {/if}

        <div class="px-6 pb-4">
          <div class="grid grid-cols-2 gap-1 text-xs text-gray-400">
            <span>✓ Validité 30 jours</span><span>✓ Inspection gratuite</span>
            <span>✓ Garantie 2 ans</span><span>✓ Permis inclus</span>
          </div>
        </div>

        <div class="px-6 pb-8 no-print">
          <button
            onclick={() => window.print()}
            class="w-full bg-gray-900 text-white py-4 rounded-2xl text-sm font-semibold hover:bg-gray-800 cursor-pointer transition-colors"
          >
            Imprimir / PDF
          </button>
        </div>
      </div>

    {:else}
      <div class="flex-1 flex flex-col items-center justify-center px-8 py-16 text-center max-w-lg mx-auto w-full">
        <div class="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>
        <h2 class="text-3xl font-bold text-gray-900 mb-3">{endNode.data.title}</h2>
        <p class="text-gray-500 text-lg">Obrigado pelas suas respostas!</p>
        {#if resultText}<p class="text-sm text-gray-400 mt-4">{resultText}</p>{/if}
      </div>
    {/if}
  {/if}
</div>
