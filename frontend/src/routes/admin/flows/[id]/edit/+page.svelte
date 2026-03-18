<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import {
    SvelteFlow,
    Controls,
    MiniMap,
    Background,
    BackgroundVariant,
    type NodeTypes
  } from '@xyflow/svelte';
  import type { Node, Edge, Connection } from '@xyflow/svelte';

  import StartNode from '$lib/components/builder/nodes/StartNode.svelte';
  import QuestionNode from '$lib/components/builder/nodes/QuestionNode.svelte';
  import MessageNode from '$lib/components/builder/nodes/MessageNode.svelte';
  import EndNode from '$lib/components/builder/nodes/EndNode.svelte';
  import NodeToolbar from '$lib/components/builder/panels/NodeToolbar.svelte';
  import NodeEditor from '$lib/components/builder/panels/NodeEditor.svelte';
  import { createFlowBuilderStore } from '$lib/stores/flowBuilder.svelte';
  import { FlowsService } from '$lib/services/flows.service';
  import { SaveFlowRequest } from '$lib/dto/flows/requests';
  import type { NodeType } from '$lib/dto/flows/types';

  const store = createFlowBuilderStore();
  const service = new FlowsService();
  let saving = $state(false);
  let toast = $state('');
  let showDocUpload = $state(false);
  let pricingDoc = $state('');

  const nodeTypes: NodeTypes = {
    start: StartNode as any,
    question: QuestionNode as any,
    message: MessageNode as any,
    end: EndNode as any
  };

  const selectedNode = $derived(
    store.selectedNodeId ? store.nodes.find(n => n.id === store.selectedNodeId) : null
  );

  onMount(async () => {
    const id = page.params.id;
    if (id && id !== 'new') {
      const flow = await service.getById(id);
      if (flow) {
        store.loadFlow(flow);
        return;
      }
    }
    // New flow — add start node
    store.addNode('start', { x: 300, y: 50 });
    store.hasChanges = false;
  });

  function handleAddNode(type: NodeType) {
    // Place new node below the last one
    const maxY = store.nodes.reduce((max, n) => Math.max(max, n.position.y), 0);
    store.addNode(type, { x: 300, y: maxY + 180 });
  }

  function handleConnect(connection: Connection) {
    store.addEdge({
      id: '',
      source: connection.source!,
      target: connection.target!,
      sourceHandle: connection.sourceHandle || undefined,
      animated: true
    } as Edge);
  }

  function handleNodeClick({ node: clickedNode }: { node: Node }) {
    store.selectedNodeId = clickedNode.id;
  }

  function handlePaneClick() {
    store.selectedNodeId = null;
  }

  async function handleSave() {
    saving = true;
    toast = '';
    try {
      const flowData = store.getFlowData();
      const dto = new SaveFlowRequest({
        _id: store.flowId,
        name: store.flowName,
        nodes: flowData.nodes,
        edges: flowData.edges,
        status: 'draft'
      });
      const saved = await service.save(dto);
      if (saved?._id && !store.flowId) {
        store.flowId = saved._id;
      }
      store.hasChanges = false;
      toast = 'Salvo!';
      setTimeout(() => toast = '', 2500);
    } catch (e: any) {
      toast = 'Erro: ' + e.message;
    } finally {
      saving = false;
    }
  }
</script>

<div class="h-screen flex flex-col bg-gray-50">
  <!-- Header -->
  <header class="bg-white border-b border-gray-200 px-4 py-2.5 flex items-center justify-between z-10">
    <div class="flex items-center gap-3">
      <button onclick={() => goto('/admin/flows')} class="text-gray-400 hover:text-gray-700 cursor-pointer transition-colors p-1">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
      </button>
      <div class="h-5 w-px bg-gray-200"></div>
      <input
        type="text"
        bind:value={store.flowName}
        class="text-base font-semibold text-gray-900 bg-transparent border-b-2 border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none px-1 py-0.5 transition-colors"
      />
    </div>
    <div class="flex items-center gap-2">
      {#if toast}
        <span class="text-xs font-medium px-2.5 py-1 rounded-full {toast.startsWith('Erro') ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'} transition-all">
          {toast}
        </span>
      {/if}
      {#if store.hasChanges}
        <span class="w-2 h-2 rounded-full bg-yellow-400" title="Alterações não salvas"></span>
      {/if}
      <button
        onclick={() => showDocUpload = true}
        class="text-xs font-medium text-gray-600 hover:text-orange-600 bg-gray-100 hover:bg-orange-50 rounded-md px-3 py-1.5 cursor-pointer transition-colors flex items-center gap-1"
        title="Enviar tabela de preços"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
        Preços
      </button>
      {#if store.flowId}
        <button
          onclick={() => goto(`/admin/flows/${store.flowId}/preview`)}
          class="text-xs font-medium text-purple-600 hover:text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-md px-3 py-1.5 cursor-pointer transition-colors flex items-center gap-1"
          title="Visualizar questionário"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Preview
        </button>
      {/if}
      <button
        onclick={handleSave}
        disabled={saving}
        class="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 cursor-pointer transition-colors"
      >
        {saving ? 'Salvando...' : 'Salvar'}
      </button>
    </div>
  </header>

  <!-- Toolbar -->
  <div class="px-4 py-2 z-10">
    <NodeToolbar onAddNode={handleAddNode} />
  </div>

  <!-- Canvas + Editor Panel -->
  <div class="flex-1 flex overflow-hidden">
    <div class="flex-1">
      <SvelteFlow
        bind:nodes={store.nodes}
        bind:edges={store.edges}
        {nodeTypes}
        onconnect={handleConnect}
        onnodeclick={handleNodeClick}
        onpaneclick={handlePaneClick}
        fitView
        colorMode="light"
        connectionMode="loose"
      >
        <Controls position="bottom-left" />
        <MiniMap position="bottom-right" />
        <Background variant={BackgroundVariant.Dots} gap={24} size={1} />
      </SvelteFlow>
    </div>

    {#if selectedNode}
      <NodeEditor
        node={selectedNode}
        onUpdate={(data) => store.updateNodeData(selectedNode.id, data)}
        onDelete={() => store.removeNode(selectedNode.id)}
        onClose={() => store.selectedNodeId = null}
      />
    {/if}
  </div>
</div>

<!-- Modal: Upload de documento de preços -->
{#if showDocUpload}
  <div class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-lg w-full">
      <div class="px-6 py-4 border-b flex items-center justify-between">
        <div>
          <h2 class="text-base font-bold text-gray-900">Tabela de Preços</h2>
          <p class="text-xs text-gray-500 mt-0.5">Cole ou digite a tabela de preços que a IA usará para gerar orçamentos</p>
        </div>
        <button onclick={() => showDocUpload = false} class="text-gray-400 hover:text-gray-600 cursor-pointer p-1">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="p-6">
        <textarea
          bind:value={pricingDoc}
          rows="12"
          class="w-full border border-gray-200 rounded-lg px-4 py-3 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
          placeholder="Ex:
Borne 16A Level 1 — $499
Borne 32A Level 2 — $699
Borne 48A Level 2 — $899
Installation murale — $150
Installation poteau — $350
Mise à niveau panneau 200A — $1200
..."
        ></textarea>
        <p class="text-xs text-gray-400 mt-2">Este texto será enviado como contexto para a IA gerar o orçamento personalizado no nó final do tipo "Devis".</p>
      </div>
      <div class="px-6 py-3 border-t flex justify-end gap-2">
        <button
          onclick={() => showDocUpload = false}
          class="text-sm text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
        >
          Cancelar
        </button>
        <button
          onclick={() => {
            // Salvar o pricingDoc nos nós do tipo end que são quote
            const endNodes = store.nodes.filter(n => n.type === 'end' && n.data.endType === 'quote');
            for (const node of endNodes) {
              store.updateNodeData(node.id, { businessContext: pricingDoc });
            }
            showDocUpload = false;
            toast = `Preços aplicados em ${endNodes.length} nó(s) de orçamento`;
            setTimeout(() => toast = '', 3000);
          }}
          disabled={!pricingDoc.trim()}
          class="text-sm font-medium bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-40 cursor-pointer transition-colors"
        >
          Aplicar aos nós de orçamento
        </button>
      </div>
    </div>
  </div>
{/if}
