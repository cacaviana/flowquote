<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getSession, clearSession, type PetraSession } from '$lib/services/session';
  import { clearSsoCookie, tryAdoptSsoSession } from '$lib/services/sso';

  let { children } = $props();
  let session = $state<PetraSession | null>(null);
  let checked = $state(false);
  let ssoDenied = $state(false);

  onMount(() => {
    session = getSession();
    if (!session) {
      // SSO Petra Suite: sem sessao local, tenta o cookie petra_sso do portal.
      const sso = tryAdoptSsoSession();
      if (sso === 'denied') {
        ssoDenied = true;
        return;
      }
      session = sso;
    }
    if (!session) {
      goto('/login');
      return;
    }
    checked = true;
  });

  function logout() {
    clearSession();
    clearSsoCookie();
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
{:else if ssoDenied}
  <div class="min-h-screen flex items-center justify-center bg-slate-50">
    <div class="text-center space-y-3">
      <p data-testid="msg-sso-negado" class="text-slate-700 text-sm font-medium">
        Seu plano não inclui o Quanto
      </p>
      <a href="/login" class="text-indigo-600 text-sm underline">Entrar com outra conta</a>
    </div>
  </div>
{/if}
