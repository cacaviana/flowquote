<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  // Rota de entrada /admin (usada pelo card do portal Petra Suite).
  // O guard SSO roda no +layout do admin; aqui so encaminha para o painel.
  onMount(() => {
    goto('/admin/flows', { replaceState: true });
  });
</script>

<div class="min-h-screen flex items-center justify-center bg-slate-50">
  <div class="text-slate-400 text-sm">Redirecionando...</div>
</div>
