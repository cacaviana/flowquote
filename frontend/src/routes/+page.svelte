<script lang="ts">
  import { goto } from '$app/navigation';
  import { FlowsService } from '$lib/services/flows.service';
  import type { Flow } from '$lib/dto/flows/types';
  import { onMount } from 'svelte';

  const service = new FlowsService();
  let flows = $state<Flow[]>([]);
  let loading = $state(true);

  onMount(async () => {
    try {
      flows = await service.list();
    } catch (e) {
      // silently fail — just show no demo button
    } finally {
      loading = false;
    }
  });

  const firstPublished = $derived(flows.find(f => f.status === 'published'));
  const firstFlow = $derived(flows[0]);
  const demoSlug = $derived(firstPublished?.slug || firstFlow?.slug);
</script>

<div class="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
  <div class="text-center max-w-lg">
    <h1 class="text-4xl font-bold text-gray-900 mb-2">FlowQuote</h1>
    <p class="text-gray-600 mb-8">Construtor Visual de Orçamentos com IA</p>

    <div class="flex gap-4 justify-center">
      <button
        onclick={() => goto('/admin/flows')}
        class="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors cursor-pointer"
      >
        Painel Admin
      </button>
      {#if !loading && demoSlug}
        <button
          onclick={() => goto(`/q/${demoSlug}`)}
          class="bg-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-purple-700 transition-colors cursor-pointer"
        >
          Ver Questionário Demo
        </button>
      {/if}
    </div>
  </div>
</div>
