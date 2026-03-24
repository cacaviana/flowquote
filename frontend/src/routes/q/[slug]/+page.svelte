<script lang="ts">
  import { page } from '$app/state';
  import { onMount, tick } from 'svelte';
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

  let phase = $state<'intro' | 'questions' | 'booking' | 'end'>('intro');

  // Dados do cliente
  let clientData = $state({ name: '', email: '', phone: '', address: '' });

  // Navegação
  let currentNodeId = $state<string | null>(null);
  let answers = $state<{ node_id: string; question: string; value: string }[]>([]);
  let endNode = $state<FlowNode | null>(null);
  let submitting = $state(false);
  let inputValue = $state('');

  // Chat
  type ChatMsg = { from: 'bot' | 'user'; text: string; opts?: { label: string; value: string; id?: string }[]; type?: string };
  let chatHistory = $state<ChatMsg[]>([]);
  let waitingForInput = $state(false);
  let chatContainer: HTMLElement;

  // Quote result
  let quoteData = $state<{
    items: { description: string; unit_price: number; quantity: number; subtotal: number }[];
    subtotal: number; taxes_tps: number; taxes_tvq: number; total: number;
    recommendations: string; notes: string;
  } | null>(null);
  let resultText = $state('');

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

  async function scrollToBottom() {
    await tick();
    if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  async function pushBotMsg(text: string, opts?: ChatMsg['opts'], type?: string) {
    chatHistory = [...chatHistory, { from: 'bot', text, opts, type }];
    waitingForInput = true;
    await scrollToBottom();
  }

  async function pushUserMsg(text: string) {
    waitingForInput = false;
    chatHistory = [...chatHistory.map(m => ({ ...m, opts: undefined })), { from: 'user', text }];
    await scrollToBottom();
  }

  function startQuestions() {
    if (!clientData.name.trim() || !clientData.email.trim()) return;
    phase = 'questions';
    chatHistory = [];
    // Mensagem de boas-vindas
    pushBotMsg(`Olá, ${clientData.name.split(' ')[0]}! 👋 Vou te fazer algumas perguntas rápidas.`);
    setTimeout(() => {
      const startNode = flow!.nodes.find(n => n.type === 'start');
      if (!startNode) return;
      const edge = flow!.edges.find(e => e.source === startNode.id);
      if (edge) { currentNodeId = edge.target; processCurrentNode(); }
    }, 800);
  }

  async function processCurrentNode() {
    if (!currentNode) return;
    if (currentNode.type === 'message') {
      await pushBotMsg(currentNode.data.title || currentNode.data.message || '');
      setTimeout(() => {
        const edge = flow!.edges.find(e => e.source === currentNodeId);
        if (edge) { currentNodeId = edge.target; processCurrentNode(); }
      }, 1800);
    } else if (currentNode.type === 'question') {
      const qt = currentNode.data.questionType;
      const hasOpts = qt === 'yes_no' || ((qt === 'single_choice' || qt === 'multiple_choice' || qt === 'dropdown') && currentNode.data.options?.length);
      const opts = qt === 'yes_no'
        ? [{ label: 'Sim', value: 'Sim', id: 'yes' }, { label: 'Não', value: 'Não', id: 'no' }]
        : hasOpts && currentNode.data.options
          ? currentNode.data.options.map((o: { label: string; value: string; id: string }) => ({ label: o.label, value: o.value, id: o.id }))
          : undefined;
      await pushBotMsg(currentNode.data.title, opts, currentNode.data.questionType);
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

  async function selectAnswer(value: string, handleId?: string) {
    if (!currentNode) return;
    const label = currentNode.data.options?.find((o: {value:string;label:string}) => o.value === value)?.label || value;
    await pushUserMsg(label);
    answers = [...answers, { node_id: currentNode.id, question: currentNode.data.title, value }];

    let nextEdge: FlowEdge | undefined;
    if (handleId) nextEdge = flow!.edges.find(e => e.source === currentNodeId && e.sourceHandle === handleId);
    if (!nextEdge) nextEdge = flow!.edges.find(e => e.source === currentNodeId && !e.sourceHandle);
    if (!nextEdge) nextEdge = flow!.edges.find(e => e.source === currentNodeId);
    if (nextEdge) {
      setTimeout(() => { currentNodeId = nextEdge!.target; processCurrentNode(); }, 400);
    } else {
      // Dead-end: sem edge de saída — finalizar fluxo
      setTimeout(async () => {
        await pushBotMsg('Obrigado pelas respostas! Vamos processar suas informações.');
        phase = 'end';
        submitToBackend();
      }, 400);
    }
  }

  async function submitTextAnswer() {
    const strVal = String(inputValue).trim();
    if (!strVal || !currentNode) return;
    inputValue = '';
    await selectAnswer(strVal);
  }

  async function loadBookingDays() {
    const result = await bookingService.getAvailableDays();
    availableDays = result.days;
    if (availableDays.length > 0) { selectedDay = availableDays[0]; await loadSlots(selectedDay); }
  }

  async function loadSlots(date: string) {
    loadingSlots = true;
    selectedSlot = '';
    const result = await bookingService.getSlots(date);
    availableSlots = result.available;
    loadingSlots = false;
  }

  async function selectDay(d: string) { selectedDay = d; await loadSlots(d); }

  async function confirmBooking() {
    if (!selectedDay || !selectedSlot || !flow || !endNode) return;
    submitting = true;
    bookingError = '';
    try {
      const result = await bookingService.book({
        flow_id: flow._id || '', flow_slug: flow.slug,
        client_name: clientData.name, client_email: clientData.email,
        client_phone: clientData.phone || undefined,
        booking_date: selectedDay, booking_time: selectedSlot,
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
        client_phone: clientData.phone || undefined, client_address: clientData.address || undefined,
        answers, end_node_id: endNode.id,
      };
      if (endNode.data.endType === 'quote') {
        const res = await fetch('/api/generate-quote', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        });
        if (res.ok) {
          const r = await res.json();
          quoteData = r.quote_data || null;
          resultText = r.quote_text || '';
        } else {
          const r = await submissionService.submit(payload);
          resultText = r.quote_text || 'Votre demande a été enregistrée.';
        }
      } else {
        const r = await submissionService.submit(payload);
        resultText = r.quote_text || '';
      }
    } catch {
      resultText = 'Erreur lors de l\'envoi. Veuillez réessayer.';
    } finally {
      submitting = false;
    }
  }

  function formatCurrency(val: number) { return val.toLocaleString('fr-CA', { style: 'currency', currency: 'CAD' }); }
  function formatDay(d: string) { return new Date(d + 'T12:00:00').toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long' }); }
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
    .chat-bubble-bot { animation: slideInLeft 0.25s ease-out; }
    .chat-bubble-user { animation: slideInRight 0.2s ease-out; }
    @keyframes slideInLeft { from { opacity: 0; transform: translateX(-12px); } to { opacity: 1; transform: none; } }
    @keyframes slideInRight { from { opacity: 0; transform: translateX(12px); } to { opacity: 1; transform: none; } }
    .opt-chip { animation: fadeUp 0.2s ease-out; }
    @keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
  </style>
</svelte:head>

<div class="min-h-screen bg-white flex flex-col" style="font-family: -apple-system, 'Helvetica Neue', sans-serif;">

  {#if loading}
    <div class="flex-1 flex items-center justify-center">
      <div class="w-8 h-8 border-2 border-gray-800 border-t-transparent rounded-full animate-spin"></div>
    </div>

  {:else if error}
    <div class="flex-1 flex items-center justify-center p-8 text-center">
      <p class="text-gray-400">{error}</p>
    </div>

  {:else if phase === 'intro'}
    <!-- ── TELA INICIAL ── -->
    <div class="flex-1 flex flex-col justify-center px-6 py-12 max-w-md mx-auto w-full">
      <div class="mb-10">
        <div class="w-12 h-12 rounded-2xl bg-gray-900 flex items-center justify-center mb-5">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 leading-snug mb-2">{flow?.name}</h1>
        <p class="text-gray-400">Responda algumas perguntas rápidas e pronto!</p>
      </div>

      <div class="space-y-5">
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Nome *</label>
          <input type="text" bind:value={clientData.name} placeholder="Seu nome completo"
            class="w-full border-0 border-b-2 border-gray-100 focus:border-gray-900 outline-none py-2.5 text-lg text-gray-900 bg-transparent transition-colors placeholder-gray-200" />
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">E-mail *</label>
          <input type="email" bind:value={clientData.email} placeholder="seu@email.com"
            class="w-full border-0 border-b-2 border-gray-100 focus:border-gray-900 outline-none py-2.5 text-lg text-gray-900 bg-transparent transition-colors placeholder-gray-200" />
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Telefone</label>
          <input type="tel" bind:value={clientData.phone} placeholder="(00) 00000-0000"
            class="w-full border-0 border-b-2 border-gray-100 focus:border-gray-900 outline-none py-2.5 text-lg text-gray-900 bg-transparent transition-colors placeholder-gray-200" />
        </div>
      </div>

      <button onclick={startQuestions} disabled={!clientData.name.trim() || !clientData.email.trim()}
        class="mt-10 w-full bg-gray-900 text-white py-4 rounded-2xl text-base font-semibold hover:bg-gray-800 disabled:opacity-25 cursor-pointer transition-colors">
        Começar conversa →
      </button>
      <p class="text-center text-xs text-gray-300 mt-4">Seus dados são protegidos</p>
    </div>

  {:else if phase === 'questions'}
    <!-- ── CHAT ── -->

    <!-- Header com progress -->
    <div class="sticky top-0 z-10 bg-white border-b border-gray-100">
      <div class="flex items-center gap-3 px-4 py-3">
        <div class="w-9 h-9 rounded-full bg-gray-900 flex items-center justify-center shrink-0">
          <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-semibold text-sm text-gray-900 truncate">{flow?.name}</p>
          <p class="text-xs text-gray-400">{answeredCount} de {totalQuestions} respondidas</p>
        </div>
        <div class="text-xs font-bold text-gray-400">{progressPercent}%</div>
      </div>
      <!-- Progress bar -->
      <div class="h-0.5 bg-gray-100">
        <div class="h-full bg-gray-900 transition-all duration-500" style="width: {progressPercent}%"></div>
      </div>
    </div>

    <!-- Área de mensagens -->
    <div class="flex-1 overflow-y-auto px-4 py-4 space-y-3" bind:this={chatContainer}>
      {#each chatHistory as msg}
        {#if msg.from === 'bot'}
          <div class="flex items-end gap-2 max-w-xs chat-bubble-bot">
            <div class="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center shrink-0 mb-0.5">
              <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" />
              </svg>
            </div>
            <div>
              <div class="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-2.5">
                <p class="text-gray-800 text-sm leading-relaxed">{msg.text}</p>
              </div>
              <!-- Opções como chips (somente na última mensagem do bot) -->
              {#if msg.opts && waitingForInput && chatHistory[chatHistory.length - 1] === msg}
                <div class="flex flex-wrap gap-2 mt-2">
                  {#each msg.opts as opt, i}
                    <button
                      onclick={() => selectAnswer(opt.value, opt.id)}
                      class="opt-chip bg-white border-2 border-gray-200 hover:border-gray-900 hover:bg-gray-900 hover:text-white text-gray-700 rounded-xl px-3.5 py-1.5 text-sm font-medium transition-all cursor-pointer"
                      style="animation-delay: {i * 0.05}s"
                    >
                      {opt.label}
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        {:else}
          <div class="flex justify-end chat-bubble-user">
            <div class="bg-gray-900 text-white rounded-2xl rounded-br-md px-4 py-2.5 max-w-xs">
              <p class="text-sm leading-relaxed">{msg.text}</p>
            </div>
          </div>
        {/if}
      {/each}

      <!-- Digitando... enquanto bot prepara próxima pergunta -->
      {#if !waitingForInput && phase === 'questions'}
        <div class="flex items-end gap-2 max-w-xs">
          <div class="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center shrink-0"></div>
          <div class="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
            <div class="flex gap-1">
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0s"></span>
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0.15s"></span>
              <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0.3s"></span>
            </div>
          </div>
        </div>
      {/if}
    </div>

    <!-- Input bar (para perguntas de texto/número/data/rating/photo) -->
    {#if waitingForInput && currentNode && !(currentNode.data.questionType === 'yes_no' || currentNode.data.questionType === 'single_choice' || currentNode.data.questionType === 'multiple_choice' || currentNode.data.questionType === 'dropdown')}
      <div class="sticky bottom-0 bg-white border-t border-gray-100 px-4 py-3 flex gap-2 no-print">
        <input
          type={currentNode.data.questionType === 'number' ? 'number' : 'text'}
          bind:value={inputValue}
          placeholder="Digite sua resposta..."
          class="flex-1 bg-gray-100 rounded-full px-4 py-2.5 text-sm text-gray-900 outline-none placeholder-gray-400"
          onkeydown={(e) => { if (e.key === 'Enter' && String(inputValue).trim()) submitTextAnswer(); }}
        />
        <button
          onclick={submitTextAnswer}
          disabled={!String(inputValue).trim()}
          class="w-10 h-10 bg-gray-900 rounded-full flex items-center justify-center disabled:opacity-30 cursor-pointer transition-colors hover:bg-gray-700 shrink-0"
        >
          <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
        </button>
      </div>
    {:else}
      <div class="h-4"></div>
    {/if}

  {:else if phase === 'booking'}
    <!-- ── AGENDAMENTO ── -->
    {#if bookingResult}
      <div class="flex-1 flex flex-col items-center justify-center px-8 py-16 text-center max-w-lg mx-auto w-full">
        <div class="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>
        <h2 class="text-3xl font-bold text-gray-900 mb-3">Agendado!</h2>
        <p class="text-gray-500 text-lg mb-6">{clientData.name.split(' ')[0]}, sua reunião está confirmada para</p>
        <div class="bg-gray-50 rounded-2xl p-6 w-full">
          <p class="text-2xl font-bold text-gray-900 capitalize">{formatDay(bookingResult.booking_date)}</p>
          <p class="text-2xl font-semibold text-gray-500 mt-1">às {bookingResult.booking_time}</p>
        </div>
        <p class="text-sm text-gray-400 mt-5">Confirmação enviada para {clientData.email}</p>
      </div>

    {:else}
      <div class="sticky top-0 z-10 bg-white border-b border-gray-100">
        <div class="flex items-center gap-3 px-4 py-3">
          <div class="w-9 h-9 rounded-full bg-gray-900 flex items-center justify-center shrink-0">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 9v7.5" />
            </svg>
          </div>
          <div>
            <p class="font-semibold text-sm text-gray-900">Escolha um horário</p>
            <p class="text-xs text-gray-400">Quase lá!</p>
          </div>
        </div>
        <div class="h-0.5 bg-gray-900"></div>
      </div>

      <div class="flex-1 px-5 py-6 max-w-md mx-auto w-full">
        <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Selecione o dia</p>
        <div class="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1 mb-6">
          {#each availableDays as day}
            <button onclick={() => selectDay(day)}
              class="shrink-0 flex flex-col items-center justify-center px-3.5 py-3 rounded-2xl border-2 transition-all cursor-pointer min-w-14
                {selectedDay === day ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-100 text-gray-700 hover:border-gray-300'}"
            >
              <span class="text-xs font-medium uppercase opacity-70">
                {new Date(day + 'T12:00:00').toLocaleDateString('pt-BR', { weekday: 'short' })}
              </span>
              <span class="text-xl font-bold">{new Date(day + 'T12:00:00').getDate()}</span>
              <span class="text-xs opacity-60">
                {new Date(day + 'T12:00:00').toLocaleDateString('pt-BR', { month: 'short' })}
              </span>
            </button>
          {/each}
        </div>

        <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Horário</p>
        {#if loadingSlots}
          <div class="flex items-center gap-2 text-gray-400 text-sm py-4">
            <div class="w-4 h-4 border-2 border-gray-200 border-t-gray-500 rounded-full animate-spin"></div>
            Carregando...
          </div>
        {:else if availableSlots.length === 0}
          <p class="text-gray-400 text-sm py-4">Nenhum horário disponível. Escolha outro dia.</p>
        {:else}
          <div class="grid grid-cols-3 gap-2 mb-6">
            {#each availableSlots as slot}
              <button onclick={() => selectedSlot = slot}
                class="py-3.5 rounded-xl border-2 text-sm font-semibold transition-all cursor-pointer
                  {selectedSlot === slot ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-100 text-gray-700 hover:border-gray-300'}">
                {slot}
              </button>
            {/each}
          </div>
        {/if}

        {#if bookingError}
          <div class="bg-red-50 text-red-600 text-sm rounded-xl px-4 py-3 mb-4">{bookingError}</div>
        {/if}

        <button onclick={confirmBooking} disabled={!selectedDay || !selectedSlot || submitting}
          class="w-full bg-gray-900 text-white py-4 rounded-2xl text-base font-semibold hover:bg-gray-800 disabled:opacity-25 cursor-pointer transition-colors">
          {submitting ? 'Confirmando...' : 'Confirmar reunião →'}
        </button>
      </div>
    {/if}

  {:else if phase === 'end' && endNode}
    <!-- ── RESULTADO FINAL ── -->
    {#if submitting}
      <div class="flex-1 flex flex-col items-center justify-center px-8 text-center">
        <div class="w-12 h-12 border-2 border-gray-900 border-t-transparent rounded-full animate-spin mb-6"></div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Gerando seu orçamento...</h3>
        <p class="text-gray-400 text-sm">Nossa IA está analisando suas respostas</p>
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
          Entraremos em contato em até 24h.
        </div>
      </div>

    {:else if endNode.data.endType === 'quote' && quoteData}
      <div class="quote-print max-w-lg mx-auto w-full">
        <div class="bg-gray-900 text-white px-6 py-6">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-xl font-bold">Devis estimatif</h3>
              <p class="text-gray-400 text-sm">Total Electrique</p>
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
                <th class="text-left py-2 font-medium">Produto</th>
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
            <div class="border-t border-gray-200 pt-2 flex justify-between text-base font-bold"><span>Total</span><span class="tabular-nums">{formatCurrency(quoteData.total)}</span></div>
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

        <div class="px-6 pb-8 no-print">
          <button onclick={() => window.print()}
            class="w-full bg-gray-900 text-white py-4 rounded-2xl text-sm font-semibold cursor-pointer hover:bg-gray-800 transition-colors">
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
        <p class="text-gray-500 text-lg">Obrigado!</p>
      </div>
    {/if}
  {/if}
</div>
