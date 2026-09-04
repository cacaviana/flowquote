<script lang="ts">
  import { goto } from '$app/navigation';
  import { authFetch } from '$lib/services/session';

  let description = $state('');
  let loading = $state(false);
  let erreur = $state('');
  let resultat = $state<{ flowId: string; name: string; etapes: number; avisos: string[] } | null>(null);

  const MIN = 120;
  const restant = $derived(Math.max(0, MIN - description.length));

  const EXEMPLE = `Je suis électricien. Je veux un flux de devis pour installation de bornes de recharge.
Demander d'abord si c'est résidentiel ou commercial. Si commercial, envoyer vers un spécialiste.
Si résidentiel : demander le modèle de borne (Flo Maison, Tesla Wall, Grizzl-E), la distance
entre le panneau et le stationnement (en mètres), et si le panneau électrique a de la place.
S'il n'y a pas de place, expliquer qu'une mise à niveau est nécessaire. Terminer avec un devis.`;

  async function gerar() {
    if (description.length < MIN || loading) return;
    loading = true;
    erreur = '';
    try {
      const res = await authFetch('/api/flows/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description })
      });
      if (res.status === 429) throw new Error('Quota quotidien de générations atteint (10/jour). Réessayez demain.');
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d?.message ?? d?.detail ?? "L'IA n'a pas réussi à générer un flux valide. Précisez votre description.");
      }
      const data = await res.json();
      // Sauvegarde en BROUILLON via l'API standard
      const save = await authFetch('/api/flows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...data.flow, status: 'draft' })
      });
      if (!save.ok) throw new Error('Flux généré mais échec de la sauvegarde. Réessayez.');
      const saved = await save.json();
      resultat = {
        flowId: saved._id ?? saved.id,
        name: data.flow.name,
        etapes: (data.flow.nodes ?? []).length,
        avisos: data.avisos ?? []
      };
    } catch (e: any) {
      erreur = e?.message ?? 'Erreur inattendue';
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen bg-gray-50">
  <header class="bg-white border-b px-6 py-4 flex justify-between items-center">
    <div class="flex items-center gap-3">
      <button onclick={() => goto('/admin/flows')} class="text-gray-400 hover:text-gray-700 cursor-pointer p-1" title="Retour">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/></svg>
      </button>
      <div>
        <h1 class="text-xl font-bold text-gray-900">✨ Créer un flux avec l'IA</h1>
        <p class="text-sm text-gray-500">Décrivez votre flux par écrit — l'IA génère un brouillon, vous le peaufinez dans l'éditeur</p>
      </div>
    </div>
    <a href="/admin/flows/reference" class="text-sm text-blue-600 hover:underline">📘 Référence des flux</a>
  </header>

  <main class="max-w-3xl mx-auto p-6 space-y-4">
    {#if !resultat}
      <div class="bg-white rounded-xl border p-5 space-y-3">
        <label class="block text-sm font-medium text-gray-700" for="desc">
          Décrivez votre flux (produits, questions, branchements, et comment ça se termine)
        </label>
        <textarea id="desc" bind:value={description} rows="10"
          class="w-full border rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
          placeholder={EXEMPLE}></textarea>
        <div class="flex items-center justify-between">
          <p class="text-xs text-gray-400">
            {#if restant > 0}Encore {restant} caractères — plus vous détaillez, meilleur est le brouillon{:else}✓ Description suffisante{/if}
          </p>
          <button onclick={gerar} disabled={restant > 0 || loading}
            class="px-4 py-2 rounded-lg text-white text-sm font-medium bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed">
            {loading ? 'Génération en cours… (~20 s)' : 'Générer le brouillon'}
          </button>
        </div>
        {#if erreur}
          <p class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{erreur}</p>
        {/if}
      </div>

      <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-900 space-y-1">
        <p class="font-medium">Comment ça marche</p>
        <ul class="list-disc ml-5 space-y-0.5">
          <li>L'IA crée un <b>brouillon</b> — rien n'est publié sans votre validation</li>
          <li>Les <b>images</b> ne sont jamais choisies par l'IA : vous les ajoutez dans l'éditeur</li>
          <li>La <b>table de prix</b> (CSV) s'ajoute ensuite dans l'éditeur pour les flux de devis</li>
          <li>Limite : 10 générations par jour</li>
        </ul>
      </div>
    {:else}
      <div class="bg-white rounded-xl border p-6 space-y-4">
        <div class="flex items-center gap-3">
          <span class="text-3xl">✅</span>
          <div>
            <h2 class="text-lg font-bold text-gray-900">Brouillon créé : {resultat.name}</h2>
            <p class="text-sm text-gray-500">{resultat.etapes} étapes générées — statut : brouillon</p>
          </div>
        </div>
        {#if resultat.avisos.length}
          <div class="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <p class="text-sm font-medium text-amber-800 mb-1">À faire dans l'éditeur :</p>
            <ul class="list-disc ml-5 text-sm text-amber-700 space-y-0.5">
              {#each resultat.avisos as a}<li>{a}</li>{/each}
            </ul>
          </div>
        {/if}
        <div class="flex gap-3">
          <button onclick={() => goto(`/admin/flows/${resultat!.flowId}/edit`)}
            class="px-4 py-2 rounded-lg text-white text-sm font-medium bg-blue-600 hover:bg-blue-700">
            Ouvrir dans l'éditeur
          </button>
          <button onclick={() => { resultat = null; description = ''; }}
            class="px-4 py-2 rounded-lg text-sm font-medium border text-gray-700 hover:bg-gray-50">
            Créer un autre flux
          </button>
        </div>
      </div>
    {/if}
  </main>
</div>
