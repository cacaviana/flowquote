<script lang="ts">
  import { goto } from '$app/navigation';
</script>

<div class="min-h-screen bg-gray-50">
  <header class="bg-white border-b px-6 py-4 flex items-center gap-3">
    <button onclick={() => goto('/admin/flows')} class="text-gray-400 hover:text-gray-700 cursor-pointer p-1" title="Retour">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/></svg>
    </button>
    <div>
      <h1 class="text-xl font-bold text-gray-900">📘 Référence des flux</h1>
      <p class="text-sm text-gray-500">Tout ce qu'un flux FlowQuote peut faire — étapes, connexions et règles</p>
    </div>
  </header>

  <main class="max-w-4xl mx-auto p-6 space-y-6 text-gray-800">

    <section class="bg-white rounded-xl border p-5">
      <h2 class="text-lg font-bold mb-2">1. Anatomie d'un flux</h2>
      <p class="text-sm">Un flux est un parcours d'<b>étapes</b> (nœuds) reliées par des <b>flèches</b> (connexions).
      Votre client le parcourt du <b>Départ</b> jusqu'à une <b>Fin</b>, en répondant aux questions.
      Un flux est d'abord un <b>brouillon</b> ; il n'est visible par vos clients qu'une fois <b>publié</b>.</p>
    </section>

    <section class="bg-white rounded-xl border p-5">
      <h2 class="text-lg font-bold mb-3">2. Les 4 types d'étapes</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm border-collapse">
          <thead><tr class="bg-gray-100 text-left"><th class="p-2 border">Étape</th><th class="p-2 border">Rôle</th><th class="p-2 border">Contenu possible</th></tr></thead>
          <tbody>
            <tr><td class="p-2 border font-medium">🟢 Départ</td><td class="p-2 border">Accueille le client (obligatoire, un seul)</td><td class="p-2 border">Message de bienvenue + coordonnées à collecter (nom, courriel, téléphone…)</td></tr>
            <tr><td class="p-2 border font-medium">❓ Question</td><td class="p-2 border">Collecte une réponse</td><td class="p-2 border">Titre, type de réponse, options, image, infobulle, obligatoire ou non</td></tr>
            <tr><td class="p-2 border font-medium">💬 Message</td><td class="p-2 border">Information sans réponse</td><td class="p-2 border">Texte, image, mention « transmis à un spécialiste »</td></tr>
            <tr><td class="p-2 border font-medium">🏁 Fin</td><td class="p-2 border">Termine le parcours (au moins une ; plusieurs possibles)</td><td class="p-2 border">Voir §4 — devis, spécialiste, remerciement ou rendez-vous</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="bg-white rounded-xl border p-5">
      <h2 class="text-lg font-bold mb-3">3. Les 8 types de question</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm border-collapse">
          <thead><tr class="bg-gray-100 text-left"><th class="p-2 border">Type</th><th class="p-2 border">Le client…</th><th class="p-2 border">Crée des branches ?</th></tr></thead>
          <tbody>
            <tr><td class="p-2 border">Choix unique</td><td class="p-2 border">choisit UNE option</td><td class="p-2 border font-medium text-green-700">OUI — une flèche par option</td></tr>
            <tr><td class="p-2 border">Oui / Non</td><td class="p-2 border">répond oui ou non</td><td class="p-2 border font-medium text-green-700">OUI — deux flèches</td></tr>
            <tr><td class="p-2 border">Choix multiples</td><td class="p-2 border">coche plusieurs options</td><td class="p-2 border">non — une seule suite</td></tr>
            <tr><td class="p-2 border">Liste déroulante</td><td class="p-2 border">choisit dans une liste</td><td class="p-2 border">non</td></tr>
            <tr><td class="p-2 border">Nombre</td><td class="p-2 border">saisit un nombre <span class="text-gray-500">(peut devenir une QUANTITÉ d'un produit du catalogue)</span></td><td class="p-2 border">non</td></tr>
            <tr><td class="p-2 border">Texte</td><td class="p-2 border">écrit librement</td><td class="p-2 border">non</td></tr>
            <tr><td class="p-2 border">Date</td><td class="p-2 border">choisit une date</td><td class="p-2 border">non</td></tr>
            <tr><td class="p-2 border">Photo</td><td class="p-2 border">envoie une photo</td><td class="p-2 border">non</td></tr>
          </tbody>
        </table>
      </div>
      <p class="text-sm mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">💡 <b>Lien avec le catalogue :</b> une option peut être associée à un <b>produit exact</b> de votre table de prix (CSV) — le devis est alors calculé de façon déterministe, sans invention de l'IA.</p>
    </section>

    <section class="bg-white rounded-xl border p-5">
      <h2 class="text-lg font-bold mb-3">4. Les 4 types de fin</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm border-collapse">
          <thead><tr class="bg-gray-100 text-left"><th class="p-2 border">Fin</th><th class="p-2 border">Ce qui se passe</th><th class="p-2 border">Génère un devis ?</th></tr></thead>
          <tbody>
            <tr><td class="p-2 border font-medium">💰 Devis</td><td class="p-2 border">l'IA calcule un devis à partir de votre table de prix et des réponses (PDF, texte ou les deux)</td><td class="p-2 border font-medium text-green-700">OUI</td></tr>
            <tr><td class="p-2 border">👤 Spécialiste</td><td class="p-2 border">la demande est transmise à un humain</td><td class="p-2 border">non</td></tr>
            <tr><td class="p-2 border">🙏 Remerciement</td><td class="p-2 border">simple merci (collecte de contact)</td><td class="p-2 border">non</td></tr>
            <tr><td class="p-2 border">📅 Rendez-vous</td><td class="p-2 border">le client réserve un créneau</td><td class="p-2 border">non</td></tr>
          </tbody>
        </table>
      </div>
      <p class="text-sm mt-3">Un même flux peut avoir <b>plusieurs fins</b> : par ex. la branche « je veux un devis » se termine en 💰, la branche « projet commercial » en 👤.</p>
    </section>

    <section class="bg-white rounded-xl border p-5">
      <h2 class="text-lg font-bold mb-3">5. Règles de connexion</h2>
      <ul class="text-sm list-disc ml-5 space-y-1">
        <li>Le <b>Départ</b> a exactement <b>une</b> flèche de sortie</li>
        <li>Une question <b>Choix unique</b> ou <b>Oui/Non</b> a <b>une flèche par option</b> — chaque réponse mène à sa propre suite</li>
        <li>Les autres questions et les messages ont exactement <b>une</b> suite</li>
        <li>Une <b>Fin</b> n'a jamais de suite ; rien ne pointe vers le <b>Départ</b></li>
        <li>Pas de boucles ; pas d'étapes orphelines ; chaque chemin doit atteindre une Fin</li>
      </ul>
    </section>

    <section class="bg-white rounded-xl border p-5">
      <h2 class="text-lg font-bold mb-2">6. Images et génération par IA</h2>
      <p class="text-sm">L'IA <b>ne choisit jamais vos images</b>. Quand vous générez un flux avec l'IA, elle crée la structure et les textes ; les images restent à ajouter <b>par vous</b> dans l'éditeur — c'est votre marque, votre choix. De même, l'IA produit toujours un <b>brouillon</b> : c'est vous qui publiez.</p>
    </section>

    <div class="text-center pb-6">
      <a href="/admin/flows/new-ia" class="inline-block px-5 py-2.5 rounded-lg text-white text-sm font-medium bg-blue-600 hover:bg-blue-700">✨ Créer mon flux avec l'IA</a>
    </div>
  </main>
</div>
