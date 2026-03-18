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
  let resultText = $state('');
  let submitting = $state(false);
  let inputValue = $state('');

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
    try {
      const result = await submissionService.submit({
        flow_id: flow._id || '',
        flow_slug: flow.slug,
        client_name: clientData.name,
        client_email: clientData.email,
        client_phone: clientData.phone || undefined,
        client_address: clientData.address || undefined,
        answers,
        end_node_id: endNode.id
      });
      if (result.quote_text) {
        resultText = result.quote_text;
      } else {
        resultText = 'Votre demande a ete enregistree. Merci!';
      }
    } catch (e: any) {
      resultText = 'Erreur lors de l\'envoi. Veuillez reessayer.';
    } finally {
      submitting = false;
    }
  }

  function selectAnswer(value: string, handleId?: string) {
    if (!currentNode) return;
    answers = [...answers, {
      node_id: currentNode.id,
      question: currentNode.data.title,
      value
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
</script>

<div class="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center p-4">
  <div class="bg-white rounded-2xl shadow-lg border border-gray-200 max-w-md w-full overflow-hidden">

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
      <div class="p-8">
        {#if submitting}
          <div class="text-center py-8">
            <div class="w-10 h-10 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p class="text-sm text-gray-600 font-medium">Generation de votre devis en cours...</p>
            <p class="text-xs text-gray-400 mt-1">Cela peut prendre quelques secondes</p>
          </div>

        {:else if endNode.data.endType === 'specialist'}
          <div class="text-center">
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

        {:else if endNode.data.endType === 'quote'}
          <div class="text-center mb-5">
            <div class="w-14 h-14 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-3">
              <svg class="w-7 h-7 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
              </svg>
            </div>
            <h3 class="text-lg font-bold text-gray-900">Votre devis est pret!</h3>
          </div>
          <pre class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs whitespace-pre-wrap font-mono text-gray-700 max-h-80 overflow-y-auto">{resultText}</pre>

        {:else}
          <div class="text-center">
            <div class="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
              <svg class="w-7 h-7 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
              </svg>
            </div>
            <h3 class="text-lg font-bold text-gray-900 mb-2">{endNode.data.title}</h3>
            <p class="text-sm text-gray-600">Merci pour vos reponses!</p>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
