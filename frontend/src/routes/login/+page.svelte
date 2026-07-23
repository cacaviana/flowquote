<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getSession, setSession } from '$lib/services/session';
  import { tryAdoptSsoSession } from '$lib/services/sso';

  // SSO Petra Suite: quem chega no /login ja logado na suite entra direto.
  onMount(() => {
    if (getSession()) {
      goto('/admin');
      return;
    }
    const sso = tryAdoptSsoSession();
    if (sso && sso !== 'denied') goto('/admin');
    // Sem cookie (ou plano sem Quanto): permanece na tela de login.
  });

  let email = $state('');
  let password = $state('');
  let error = $state('');
  let loading = $state(false);

  async function handleLogin(e: Event) {
    e.preventDefault();
    error = '';
    loading = true;

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        error = typeof data.detail === 'string' ? data.detail : 'Email ou senha inválidos';
        loading = false;
        return;
      }

      const data = await res.json();

      // Resposta da Petra Suite: access_token, refresh_token,
      // user {id,name,email}, tenant {id,slug,is_master}, products [{slug,...}]
      const products: string[] = (data.products || []).map((p: any) =>
        typeof p === 'string' ? p : p.slug
      );
      const isMaster = data.tenant?.is_master === true;

      if (products.length > 0 && !products.includes('quanto') && !isMaster) {
        error = 'Seu tenant não assina o produto Quanto. Fale com o administrador.';
        loading = false;
        return;
      }

      setSession({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        user: data.user ?? null,
        tenant: data.tenant ?? null,
        products
      });
      goto('/admin/flows');
    } catch (e) {
      error = 'Erro ao conectar com o servidor';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Quanto — Petra Suite</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-100 flex items-center justify-center p-4">
  <div class="w-full max-w-sm">
    <div class="bg-white rounded-2xl shadow-xl p-8">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-14 h-14 bg-indigo-600 rounded-xl flex items-center justify-center mx-auto mb-3">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        </div>
        <h1 class="text-xl font-bold text-gray-900">Quanto — Petra Suite</h1>
        <p class="text-sm text-gray-500 mt-1">Acesso administrativo</p>
      </div>

      <!-- Form -->
      <form onsubmit={handleLogin} class="space-y-4">
        {#if error}
          <div data-testid="login-error" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        {/if}

        <div>
          <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            id="email"
            data-testid="login-email"
            type="email"
            bind:value={email}
            required
            class="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="voce@empresa.com"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Senha</label>
          <input
            id="password"
            data-testid="login-password"
            type="password"
            bind:value={password}
            required
            class="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="********"
          />
        </div>

        <button
          type="submit"
          data-testid="login-submit"
          disabled={loading}
          class="w-full bg-indigo-600 text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 cursor-pointer transition-colors"
        >
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>

      <p class="text-center text-xs text-gray-400 mt-6">Identidade central Petra Suite</p>
    </div>
  </div>
</div>
