<script lang="ts">
  import { goto } from '$app/navigation';
  import { FlowsService } from '$lib/services/flows.service';
  import type { Flow } from '$lib/dto/flows/types';
  import { onMount } from 'svelte';

  const service = new FlowsService();
  let flows = $state<Flow[]>([]);
  let loading = $state(true);

  onMount(async () => {
    flows = await service.list();
    loading = false;
  });

  function createNew() {
    goto('/admin/flows/new/edit');
  }

  const statusColors: Record<string, string> = {
    draft: 'bg-yellow-100 text-yellow-800',
    published: 'bg-green-100 text-green-800',
    archived: 'bg-gray-100 text-gray-600'
  };

  const statusLabels: Record<string, string> = {
    draft: 'Rascunho',
    published: 'Publicado',
    archived: 'Arquivado'
  };
</script>

<div class="min-h-screen bg-gray-50">
  <header class="bg-white border-b px-6 py-4 flex justify-between items-center">
    <div class="flex items-center gap-3">
      <button onclick={() => goto('/')} class="text-gray-400 hover:text-gray-700 cursor-pointer transition-colors p-1" title="Voltar ao início">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
        </svg>
      </button>
      <div class="h-5 w-px bg-gray-200"></div>
      <div>
        <h1 class="text-xl font-bold text-gray-900">FlowQuote</h1>
        <p class="text-sm text-gray-500">Meus Fluxos</p>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <button
        onclick={() => goto('/admin/submissions')}
        class="text-sm font-medium text-gray-600 hover:text-purple-600 bg-gray-100 hover:bg-purple-50 rounded-lg px-4 py-2 cursor-pointer transition-colors flex items-center gap-1.5"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
        </svg>
        Demandes
      </button>
      <button
        onclick={createNew}
        class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 cursor-pointer"
      >
      + Novo Fluxo
    </button>
    </div>
  </header>

  <main class="max-w-5xl mx-auto p-6">
    {#if loading}
      <div class="text-center py-12 text-gray-500">Carregando...</div>
    {:else if flows.length === 0}
      <div class="text-center py-12">
        <p class="text-gray-500 mb-4">Nenhum fluxo criado ainda</p>
        <button
          onclick={createNew}
          class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 cursor-pointer"
        >
          Criar primeiro fluxo
        </button>
      </div>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {#each flows as flow}
          <div class="bg-white rounded-lg border hover:shadow-md transition-shadow">
            <!-- Card header clicável para editar -->
            <button
              onclick={() => goto(`/admin/flows/${flow._id}/edit`)}
              class="w-full text-left p-5 pb-3 cursor-pointer"
            >
              <div class="flex justify-between items-start mb-2">
                <h3 class="font-semibold text-gray-900">{flow.name}</h3>
                <span class="text-xs px-2 py-0.5 rounded-full {statusColors[flow.status]}">
                  {statusLabels[flow.status] || flow.status}
                </span>
              </div>
              <p class="text-sm text-gray-500 mb-1">/q/{flow.slug}</p>
              <div class="text-xs text-gray-400">
                {(flow as any).node_count ?? flow.nodes?.length ?? 0} nós &middot; v{flow.version}
              </div>
            </button>

            <!-- Ações do card -->
            <div class="border-t px-5 py-3 flex gap-2">
              <button
                onclick={() => goto(`/admin/flows/${flow._id}/edit`)}
                class="flex-1 text-xs font-medium text-gray-600 hover:text-blue-600 bg-gray-50 hover:bg-blue-50 rounded-md py-2 cursor-pointer transition-colors flex items-center justify-center gap-1"
                title="Editar fluxo"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                </svg>
                Editar
              </button>
              <button
                onclick={() => goto(`/admin/flows/${flow._id}/preview`)}
                class="flex-1 text-xs font-medium text-gray-600 hover:text-purple-600 bg-gray-50 hover:bg-purple-50 rounded-md py-2 cursor-pointer transition-colors flex items-center justify-center gap-1"
                title="Visualizar questionário"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Preview
              </button>
              <a
                href="/q/{flow.slug}"
                target="_blank"
                class="flex-1 text-xs font-medium text-gray-600 hover:text-green-600 bg-gray-50 hover:bg-green-50 rounded-md py-2 cursor-pointer transition-colors flex items-center justify-center gap-1"
                title="Abrir link público"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                </svg>
                Link
              </a>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </main>
</div>
