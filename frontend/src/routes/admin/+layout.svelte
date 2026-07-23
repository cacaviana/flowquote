<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getSession, clearSession, type PetraSession } from '$lib/services/session';

  let { children } = $props();
  let session = $state<PetraSession | null>(null);
  let checked = $state(false);

  onMount(() => {
    session = getSession();
    if (!session) {
      goto('/login');
      return;
    }
    checked = true;
  });

  function logout() {
    clearSession();
    goto('/login');
  }
</script>

{#if checked && session}
  <div class="min-h-screen flex flex-col">
    <div class="bg-slate-900 text-slate-200 text-xs px-4 py-1.5 flex items-center justify-between">
      <span class="font-semibold">Quanto — Petra Suite</span>
      <span class="flex items-center gap-3">
        <span data-testid="session-user">{session.user?.email ?? ''}{session.tenant?.slug ? ` · ${session.tenant.slug}` : ''}</span>
        <button
          data-testid="logout-button"
          onclick={logout}
          class="border border-slate-500 rounded px-2 py-0.5 hover:bg-slate-700 cursor-pointer transition-colors"
        >
          Sair
        </button>
      </span>
    </div>
    <div class="flex-1">
      {@render children()}
    </div>
  </div>
{/if}
