<script lang="ts">
  import { page } from '$app/state';
  import { onMount } from 'svelte';
  import { FlowsService } from '$lib/services/flows.service';
  import { SubmissionsService } from '$lib/services/submissions.service';
  import type { Flow, FlowNode, FlowEdge } from '$lib/dto/flows/types';

  const flowService = new FlowsService();
  const submissionService = new SubmissionsService();

  let flow = $state<Flow | null>(null);
  let loading = $state(true);
  let error = $state('');

  // Executor state
  let phase = $state<'form' | 'questions' | 'end'>('form');
  let clientData = $state({ name: '', email: '', phone: '', address: '' });
  let currentNodeId = $state<string | null>(null);
  let answers = $state<{ node_id: string; question: string; value: string }[]>([]);
  let endNode = $state<FlowNode | null>(null);
  let submitting = $state(false);
  let inputValue = $state('');

  // Quote result
  let quoteData = $state<{
    items: { description: string; unit_price: number; quantity: number; subtotal: number }[];
    subtotal: number;
    taxes_tps: number;
    taxes_tvq: number;
    total: number;
    recommendations: string;
    notes: string;
  } | null>(null);
  let resultText = $state('');
  let resultType = $state<'quote' | 'fallback' | 'error' | ''>('');

  let currentNode = $derived(flow?.nodes.find(n => n.id === currentNodeId) || null);
  let totalQuestions = $derived(flow?.nodes.filter(n => n.type === 'question').length || 0);
  let answeredCount = $derived(answers.length);
  let progressPercent = $derived(totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0);

  onMount(async () => {
    try {
      const slug = page.params.slug;
      if (slug) {
        flow = await flowService.getBySlug(slug);
      }
      if (!flow) error = 'Questionnaire non trouve';
    } catch (e: any) {
      error = e.message;
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
    if (edge) {
      currentNodeId = edge.target;
      processCurrentNode();
    }
  }

  function processCurrentNode() {
    if (!currentNode) return;
    if (currentNode.type === 'message') {
      setTimeout(() => {
        const edge = flow!.edges.find(e => e.source === currentNodeId);
        if (edge) {
          currentNodeId = edge.target;
          processCurrentNode();
        }
      }, 2500);
    } else if (currentNode.type === 'end') {
      endNode = currentNode;
      phase = 'end';
      submitToBackend();
    }
  }

  async function submitToBackend() {
    if (!flow || !endNode) return;
    submitting = true;
    resultText = '';
    quoteData = null;
    resultType = '';

    try {
      const payload = {
        flow_id: flow._id || '',
        flow_slug: flow.slug,
        client_name: clientData.name,
        client_email: clientData.email,
        client_phone: clientData.phone || undefined,
        client_address: clientData.address || undefined,
        answers,
        end_node_id: endNode.id
      };

      if (endNode.data.endType === 'quote') {
        const res = await fetch('/api/generate-quote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          const result = await res.json();
          quoteData = result.quote_data || null;
          resultText = result.quote_text || '';
          resultType = quoteData ? 'quote' : 'fallback';
        } else {
          const result = await submissionService.submit(payload);
          resultText = result.quote_text || 'Votre demande a ete enregistree. Un specialiste vous contactera.';
          resultType = 'fallback';
        }
      } else {
        const result = await submissionService.submit(payload);
        resultText = result.quote_text || 'Votre demande a ete enregistree. Merci!';
        resultType = 'fallback';
      }
    } catch (e: any) {
      resultText = 'Erreur lors de l\'envoi. Veuillez reessayer.';
      resultType = 'error';
    } finally {
      submitting = false;
    }
  }

  function selectAnswer(value: string | number, handleId?: string) {
    if (!currentNode) return;
    answers = [...answers, {
      node_id: currentNode.id,
      question: currentNode.data.title,
      value: String(value)
    }];
    let nextEdge: FlowEdge | undefined;
    if (handleId) {
      nextEdge = flow!.edges.find(e => e.source === currentNodeId && e.sourceHandle === handleId);
    }
    if (!nextEdge) {
      nextEdge = flow!.edges.find(e => e.source === currentNodeId && !e.sourceHandle);
    }
    if (!nextEdge) {
      nextEdge = flow!.edges.find(e => e.source === currentNodeId);
    }
    if (nextEdge) {
      currentNodeId = nextEdge.target;
      processCurrentNode();
    }
  }

  function goBack() {
    if (answers.length === 0) {
      phase = 'form';
      return;
    }
    const last = answers[answers.length - 1];
    answers = answers.slice(0, -1);
    currentNodeId = last.node_id;
    phase = 'questions';
    endNode = null;
  }

  function formatCurrency(val: number): string {
    return val.toLocaleString('fr-CA', { style: 'currency', currency: 'CAD' });
  }

  function printQuote() {
    window.print();
  }
</script>

<svelte:head>
  <style>
    @media print {
      body * { visibility: hidden; }
      .quote-card, .quote-card * { visibility: visible; }
      .quote-card { position: absolute; left: 0; top: 0; width: 100%; }
      .no-print { display: none !important; }
    }
  </style>
</svelte:head>

<div class="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center p-4">
  <div class="bg-white rounded-2xl shadow-lg border border-gray-200 max-w-lg w-full overflow-hidden">

    {#if loading}
      <div class="p-16 text-center">
        <div class="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p class="text-sm text-gray-500">Chargement...</p>
      </div>

    {:else if error}
      <div class="p-12 text-center text-red-600 text-sm">{error}</div>

    {:else if phase === 'form'}
      <div class="p-8">
        <h2 class="text-xl font-bold text-gray-900 mb-1">{flow?.name}</h2>
        <p class="text-sm text-gray-500 mb-6">Obtenez votre devis en quelques minutes</p>

        <div class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1 uppercase tracking-wide">Nom *</label>
            <input type="text" bind:value={clientData.name} class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1 uppercase tracking-wide">E-mail *</label>
            <input type="email" bind:value={clientData.email} class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1 uppercase tracking-wide">Telephone</label>
            <input type="tel" bind:value={clientData.phone} class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1 uppercase tracking-wide">Adresse</label>
            <input type="text" bind:value={clientData.address} class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow" />
          </div>
          <button
            onclick={startQuestions}
            disabled={!clientData.name.trim() || !clientData.email.trim()}
            class="w-full bg-blue-600 text-white py-3 rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors mt-2"
          >
            Commencer
          </button>
        </div>
      </div>

    {:else if phase === 'questions' && currentNode}
      <!-- Progress -->
      <div class="bg-gray-50 px-6 py-3 flex items-center justify-between border-b border-gray-100">
        <span class="text-xs font-medium text-gray-500">Question {answeredCount + 1} / {totalQuestions}</span>
        <div class="flex items-center gap-2">
          <div class="w-24 bg-gray-200 rounded-full h-1.5">
            <div class="bg-blue-600 h-1.5 rounded-full transition-all duration-300" style="width: {progressPercent}%"></div>
          </div>
          <span class="text-xs text-gray-400">{progressPercent}%</span>
        </div>
      </div>

      <div class="p-8">
        {#if currentNode.type === 'message'}
          <div class="text-center py-4">
            <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
              <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">{currentNode.data.title}</h3>
            <p class="text-sm text-gray-600">{currentNode.data.message}</p>
          </div>
        {:else}
          <h3 class="text-lg font-semibold text-gray-900 mb-1">{currentNode.data.title}</h3>

          {#if currentNode.data.tooltip}
            <p class="text-xs text-gray-400 mb-4">{currentNode.data.tooltip}</p>
          {:else}
            <div class="mb-4"></div>
          {/if}

          {#if currentNode.data.questionType === 'single_choice' && currentNode.data.options}
            <div class="grid grid-cols-2 gap-2">
              {#each currentNode.data.options as opt}
                <button
                  onclick={() => selectAnswer(opt.value, opt.id)}
                  class="border-2 border-gray-200 rounded-xl px-3 py-3.5 text-center text-sm font-medium hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer"
                >
                  {opt.label}
                </button>
              {/each}
            </div>
          {:else if currentNode.data.questionType === 'yes_no'}
            <div class="grid grid-cols-2 gap-3">
              <button
                onclick={() => selectAnswer('Oui', 'yes')}
                class="border-2 border-gray-200 rounded-xl px-4 py-4 text-center font-medium hover:border-green-500 hover:bg-green-50 transition-all cursor-pointer"
              >
                Oui
              </button>
              <button
                onclick={() => selectAnswer('Non', 'no')}
                class="border-2 border-gray-200 rounded-xl px-4 py-4 text-center font-medium hover:border-red-400 hover:bg-red-50 transition-all cursor-pointer"
              >
                Non
              </button>
            </div>
          {:else if currentNode.data.questionType === 'number'}
            <div class="flex gap-2">
              <input
                type="number"
                bind:value={inputValue}
                class="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Entrez un nombre"
              />
              <button
                onclick={() => { selectAnswer(inputValue); inputValue = ''; }}
                disabled={!inputValue}
                class="bg-blue-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 cursor-pointer transition-colors"
              >
                Suivant
              </button>
            </div>
          {:else}
            <div class="flex gap-2">
              <input
                type="text"
                bind:value={inputValue}
                class="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Votre reponse"
              />
              <button
                onclick={() => { selectAnswer(inputValue); inputValue = ''; }}
                disabled={!inputValue.trim()}
                class="bg-blue-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 cursor-pointer transition-colors"
              >
                Suivant
              </button>
            </div>
          {/if}
        {/if}

        <button
          onclick={goBack}
          class="mt-6 text-xs text-gray-400 hover:text-gray-600 cursor-pointer transition-colors flex items-center gap-1"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Retour
        </button>
      </div>

    {:else if phase === 'end' && endNode}

      {#if submitting}
        <div class="p-8">
          <div class="text-center py-8">
            <div class="w-12 h-12 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-5"></div>
            <p class="text-base text-gray-800 font-semibold">Generation de votre devis...</p>
            <p class="text-sm text-gray-400 mt-2">Notre IA analyse vos besoins et calcule le meilleur prix</p>
          </div>
        </div>

      {:else if endNode.data.endType === 'specialist'}
        <div class="p-8 text-center">
          <div class="w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <svg class="w-7 h-7 text-red-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
            </svg>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">{endNode.data.title}</h3>
          <p class="text-sm text-gray-600 mb-4">{endNode.data.message}</p>
          <div class="bg-green-50 border border-green-200 rounded-lg p-3 text-xs text-green-700">
            Vos donnees ont ete enregistrees. Nous vous contacterons sous 24h.
          </div>
        </div>

      {:else if endNode.data.endType === 'quote' && quoteData}
        <!-- DEVIS PROFESSIONNEL -->
        <div class="quote-card">
          <!-- Header -->
          <div class="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-5">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-bold">Devis estimatif</h3>
                <p class="text-blue-200 text-xs mt-0.5">Total Electrique</p>
              </div>
              <div class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div class="mt-3 text-sm">
              <p class="font-medium">{clientData.name}</p>
              {#if clientData.address}
                <p class="text-blue-200 text-xs">{clientData.address}</p>
              {/if}
            </div>
          </div>

          <!-- Items -->
          <div class="px-6 py-4">
            <table class="w-full text-sm" data-testid="quote-items-table">
              <thead>
                <tr class="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100">
                  <th class="text-left py-2 font-medium">Produit / Service</th>
                  <th class="text-center py-2 font-medium w-12">Qte</th>
                  <th class="text-right py-2 font-medium">Prix</th>
                </tr>
              </thead>
              <tbody>
                {#each quoteData.items as item}
                  <tr class="border-b border-gray-50">
                    <td class="py-2.5 text-gray-800 font-medium">{item.description}</td>
                    <td class="py-2.5 text-center text-gray-500">{item.quantity}</td>
                    <td class="py-2.5 text-right font-medium tabular-nums {item.subtotal === 0 ? 'text-amber-600 italic' : 'text-gray-800'}">{item.subtotal === 0 ? 'A consulter' : formatCurrency(item.subtotal)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>

          <!-- Totals -->
          <div class="px-6 pb-4">
            <div class="bg-gray-50 rounded-xl p-4 space-y-1.5">
              <div class="flex justify-between text-sm text-gray-600">
                <span>Sous-total</span>
                <span class="tabular-nums">{formatCurrency(quoteData.subtotal)}</span>
              </div>
              <div class="flex justify-between text-sm text-gray-500">
                <span>TPS (5%)</span>
                <span class="tabular-nums">{formatCurrency(quoteData.taxes_tps)}</span>
              </div>
              <div class="flex justify-between text-sm text-gray-500">
                <span>TVQ (9,975%)</span>
                <span class="tabular-nums">{formatCurrency(quoteData.taxes_tvq)}</span>
              </div>
              <div class="border-t border-gray-200 pt-2 mt-2 flex justify-between text-base font-bold text-gray-900">
                <span>Total</span>
                <span class="tabular-nums text-blue-700">{formatCurrency(quoteData.total)}</span>
              </div>
            </div>
          </div>

          <!-- Recommendations -->
          {#if quoteData.recommendations}
            <div class="px-6 pb-3">
              <div class="bg-blue-50 border border-blue-100 rounded-lg p-3">
                <p class="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-1">Recommandations</p>
                <p class="text-xs text-blue-800 leading-relaxed">{quoteData.recommendations}</p>
              </div>
            </div>
          {/if}

          <!-- Notes -->
          {#if quoteData.notes}
            <div class="px-6 pb-3">
              <div class="bg-amber-50 border border-amber-100 rounded-lg p-3">
                <p class="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">Notes</p>
                <p class="text-xs text-amber-800 leading-relaxed">{quoteData.notes}</p>
              </div>
            </div>
          {/if}

          <!-- Footer -->
          <div class="px-6 pb-4">
            <div class="grid grid-cols-2 gap-2 text-xs text-gray-400">
              <span>Validite: 30 jours</span>
              <span class="text-right">Inspection gratuite</span>
              <span>Garantie 2 ans</span>
              <span class="text-right">Permis inclus</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="px-6 pb-6 flex gap-2 no-print">
            <button
              onclick={printQuote}
              class="flex-1 bg-blue-600 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-blue-700 cursor-pointer transition-colors flex items-center justify-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 011.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18 10.5h.008v.008H18V10.5zm-3 0h.008v.008H15V10.5z" />
              </svg>
              Imprimer / PDF
            </button>
          </div>
        </div>

      {:else if endNode.data.endType === 'quote' && resultText}
        <!-- Fallback: texto simples se quote_data nao veio -->
        <div class="p-8">
          <div class="text-center mb-4">
            <div class="w-14 h-14 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-3">
              <svg class="w-7 h-7 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
              </svg>
            </div>
            <h3 class="text-lg font-bold text-gray-900">Votre devis est pret!</h3>
          </div>
          <pre class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs whitespace-pre-wrap font-mono text-gray-700 max-h-80 overflow-y-auto">{resultText}</pre>
        </div>

      {:else}
        <div class="p-8 text-center">
          <div class="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
            <svg class="w-7 h-7 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
            </svg>
          </div>
          <h3 class="text-lg font-bold text-gray-900 mb-2">{endNode.data.title}</h3>
          <p class="text-sm text-gray-600">Merci pour vos reponses!</p>
          {#if resultText}
            <p class="text-sm text-gray-500 mt-3">{resultText}</p>
          {/if}
        </div>
      {/if}
    {/if}
  </div>
</div>
