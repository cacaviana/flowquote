<script lang="ts">
  import { goto } from '$app/navigation';

  let lang = $state<'pt' | 'fr' | 'en' | 'es'>('pt');

  const t: Record<string, Record<string, string>> = {
    back: { pt: 'Voltar', fr: 'Retour', en: 'Back', es: 'Volver' },
    title: { pt: 'Treinamento: Agendamentos', fr: 'Formation: Rendez-vous', en: 'Training: Scheduling', es: 'Capacitación: Agendamientos' },
    subtitle: { pt: 'Aprenda a criar fluxos de agendamento com calendário integrado', fr: 'Apprenez à créer des flux de prise de rendez-vous avec calendrier intégré', en: 'Learn to create scheduling flows with integrated calendar', es: 'Aprenda a crear flujos de agendamiento con calendario integrado' },

    // 1. MISSION
    s1title: { pt: 'A Missão do Agendamento', fr: 'La Mission de la Prise de RDV', en: 'The Scheduling Mission', es: 'La Misión del Agendamiento' },
    s1p1: {
      pt: 'O módulo de Agendamento do FlowQuote permite que seus leads respondam perguntas de qualificação e, ao final, escolham um dia e horário disponível diretamente no seu Google Calendar — tudo automático, sem troca de mensagens.',
      fr: 'Le module de prise de rendez-vous de FlowQuote permet à vos leads de répondre aux questions de qualification et, à la fin, de choisir un jour et une heure disponibles directement sur votre Google Calendar — tout automatiquement, sans échanges de messages.',
      en: 'FlowQuote\'s Scheduling module lets your leads answer qualifying questions and, at the end, choose an available day and time directly on your Google Calendar — all automatic, no back-and-forth messaging.',
      es: 'El módulo de Agendamiento de FlowQuote permite que sus leads respondan preguntas de calificación y, al final, elijan un día y horario disponible directamente en su Google Calendar — todo automático, sin intercambio de mensajes.'
    },
    s1p2: {
      pt: 'Perfeito para escolas, consultorias, clínicas, ou qualquer negócio que precise agendar reuniões com leads qualificados.',
      fr: 'Parfait pour les écoles, cabinets de conseil, cliniques, ou toute entreprise qui a besoin de planifier des réunions avec des leads qualifiés.',
      en: 'Perfect for schools, consulting firms, clinics, or any business that needs to schedule meetings with qualified leads.',
      es: 'Perfecto para escuelas, consultorías, clínicas, o cualquier negocio que necesite agendar reuniones con leads calificados.'
    },

    // 2. PROBLEM
    s2title: { pt: 'Qual Problema Resolve?', fr: 'Quel Problème Résout-il ?', en: 'What Problem Does It Solve?', es: '¿Qué Problema Resuelve?' },
    s2before: { pt: 'ANTES', fr: 'AVANT', en: 'BEFORE', es: 'ANTES' },
    s2after: { pt: 'DEPOIS', fr: 'APRÈS', en: 'AFTER', es: 'DESPUÉS' },
    s2b1: { pt: 'Lead manda mensagem no Instagram → você responde horas depois → lead já perdeu interesse', fr: 'Le lead envoie un message sur Instagram → vous répondez des heures après → le lead a déjà perdu l\'intérêt', en: 'Lead sends a DM on Instagram → you reply hours later → lead already lost interest', es: 'El lead manda mensaje en Instagram → usted responde horas después → el lead ya perdió interés' },
    s2b2: { pt: 'Fica fazendo perguntas manualmente no chat para entender se o lead é qualificado', fr: 'Vous posez manuellement des questions dans le chat pour savoir si le lead est qualifié', en: 'You manually ask questions in chat to figure out if the lead is qualified', es: 'Se queda haciendo preguntas manualmente en el chat para entender si el lead es calificado' },
    s2b3: { pt: '"Quando você pode?" → "Terça?" → "Não, quarta" → 10 mensagens para agendar', fr: '"Quand pouvez-vous ?" → "Mardi ?" → "Non, mercredi" → 10 messages pour planifier', en: '"When can you?" → "Tuesday?" → "No, Wednesday" → 10 messages to schedule', es: '"¿Cuándo puede?" → "¿Martes?" → "No, miércoles" → 10 mensajes para agendar' },
    s2a1: { pt: 'Lead clica no link → responde perguntas → escolhe dia e hora no calendário → agendado!', fr: 'Le lead clique sur le lien → répond aux questions → choisit jour et heure sur le calendrier → planifié !', en: 'Lead clicks the link → answers questions → picks day and time on calendar → booked!', es: 'El lead hace clic en el enlace → responde preguntas → elige día y hora en el calendario → ¡agendado!' },
    s2a2: { pt: 'Perguntas qualificam automaticamente — você só fala com leads bons', fr: 'Les questions qualifient automatiquement — vous ne parlez qu\'avec les bons leads', en: 'Questions qualify automatically — you only talk to good leads', es: 'Las preguntas califican automáticamente — usted solo habla con leads buenos' },
    s2a3: { pt: 'Evento aparece no Google Calendar automaticamente — com todos os dados do lead', fr: 'L\'événement apparaît dans Google Calendar automatiquement — avec toutes les données du lead', en: 'Event appears in Google Calendar automatically — with all lead data', es: 'El evento aparece en Google Calendar automáticamente — con todos los datos del lead' },

    // 3. FEATURES
    s3title: { pt: 'Funcionalidades', fr: 'Fonctionnalités', en: 'Features', es: 'Funcionalidades' },
    s3f1t: { pt: 'Perguntas Qualificativas', fr: 'Questions de Qualification', en: 'Qualifying Questions', es: 'Preguntas Calificativas' },
    s3f1d: { pt: 'Filtre seus leads com perguntas inteligentes antes de agendar. Saiba área de atuação, faixa salarial, objetivo — tudo que importa.', fr: 'Filtrez vos leads avec des questions intelligentes avant de planifier. Découvrez domaine d\'activité, tranche salariale, objectif — tout ce qui compte.', en: 'Filter your leads with smart questions before scheduling. Know their field, salary range, objective — everything that matters.', es: 'Filtre sus leads con preguntas inteligentes antes de agendar. Sepa área de actuación, rango salarial, objetivo — todo lo que importa.' },
    s3f2t: { pt: 'Calendário Visual', fr: 'Calendrier Visuel', en: 'Visual Calendar', es: 'Calendario Visual' },
    s3f2d: { pt: 'O lead vê um calendário bonito com os dias disponíveis. Dias sem horário ficam desabilitados. Navega entre meses facilmente.', fr: 'Le lead voit un beau calendrier avec les jours disponibles. Les jours sans horaire sont désactivés. Navigation facile entre les mois.', en: 'The lead sees a beautiful calendar with available days. Days without slots are disabled. Easy month navigation.', es: 'El lead ve un calendario bonito con los días disponibles. Días sin horario quedan deshabilitados. Navega entre meses fácilmente.' },
    s3f3t: { pt: 'Horários em Tempo Real', fr: 'Créneaux en Temps Réel', en: 'Real-Time Slots', es: 'Horarios en Tiempo Real' },
    s3f3d: { pt: 'Os horários vêm direto do Google Calendar. Se alguém já agendou às 10:00, esse horário desaparece automaticamente.', fr: 'Les créneaux viennent directement de Google Calendar. Si quelqu\'un a déjà réservé à 10h00, ce créneau disparaît automatiquement.', en: 'Time slots come straight from Google Calendar. If someone already booked 10:00 AM, that slot disappears automatically.', es: 'Los horarios vienen directo de Google Calendar. Si alguien ya agendó a las 10:00, ese horario desaparece automáticamente.' },
    s3f4t: { pt: 'Evento no Google Calendar', fr: 'Événement dans Google Calendar', en: 'Google Calendar Event', es: 'Evento en Google Calendar' },
    s3f4d: { pt: 'Ao confirmar, um evento é criado automaticamente no seu Google Calendar com o nome, email e telefone do lead.', fr: 'À la confirmation, un événement est créé automatiquement dans votre Google Calendar avec le nom, email et téléphone du lead.', en: 'On confirmation, an event is automatically created in your Google Calendar with the lead\'s name, email and phone.', es: 'Al confirmar, un evento se crea automáticamente en su Google Calendar con el nombre, email y teléfono del lead.' },

    // 4. QUICKSTART
    s4title: { pt: 'Quickstart: Seu Primeiro Agendamento', fr: 'Démarrage Rapide: Votre Premier RDV', en: 'Quickstart: Your First Booking', es: 'Inicio Rápido: Su Primer Agendamiento' },
    s4step1t: { pt: 'Clique em "Modo Agendamento"', fr: 'Cliquez sur "Mode Rendez-vous"', en: 'Click "Scheduling Mode"', es: 'Haga clic en "Modo Agendamiento"' },
    s4step1d: { pt: 'Na página inicial do FlowQuote, clique no botão verde "Modo Agendamento". Um fluxo será criado automaticamente com perguntas de exemplo.', fr: 'Sur la page d\'accueil de FlowQuote, cliquez sur le bouton vert "Mode Rendez-vous". Un flux sera créé automatiquement avec des questions d\'exemple.', en: 'On the FlowQuote home page, click the green "Scheduling Mode" button. A flow will be automatically created with sample questions.', es: 'En la página inicial de FlowQuote, haga clic en el botón verde "Modo Agendamiento". Un flujo será creado automáticamente con preguntas de ejemplo.' },
    s4step2t: { pt: 'Personalize as perguntas', fr: 'Personnalisez les questions', en: 'Customize the questions', es: 'Personalice las preguntas' },
    s4step2d: { pt: 'No editor visual, altere as perguntas conforme seu negócio. Adicione, remova ou reordene as perguntas qualificativas.', fr: 'Dans l\'éditeur visuel, modifiez les questions selon votre activité. Ajoutez, supprimez ou réorganisez les questions de qualification.', en: 'In the visual editor, modify the questions for your business. Add, remove or reorder the qualifying questions.', es: 'En el editor visual, modifique las preguntas según su negocio. Agregue, elimine o reordene las preguntas calificativas.' },
    s4step3t: { pt: 'Verifique o nó final', fr: 'Vérifiez le nœud final', en: 'Check the end node', es: 'Verifique el nodo final' },
    s4step3d: { pt: 'O nó final deve estar configurado como "Agendamento (Calendário)". Isso ativa o calendário ao fim do questionário.', fr: 'Le nœud final doit être configuré comme "Rendez-vous (Calendrier)". Cela active le calendrier à la fin du questionnaire.', en: 'The end node must be set to "Scheduling (Calendar)". This activates the calendar at the end of the questionnaire.', es: 'El nodo final debe estar configurado como "Agendamiento (Calendario)". Esto activa el calendario al fin del cuestionario.' },
    s4step4t: { pt: 'Publique e compartilhe o link', fr: 'Publiez et partagez le lien', en: 'Publish and share the link', es: 'Publique y comparta el enlace' },
    s4step4d: { pt: 'Salve e publique o fluxo. Copie o link público (/q/seu-slug) e compartilhe no Instagram, WhatsApp, ou onde preferir.', fr: 'Enregistrez et publiez le flux. Copiez le lien public (/q/votre-slug) et partagez sur Instagram, WhatsApp, ou là où vous préférez.', en: 'Save and publish the flow. Copy the public link (/q/your-slug) and share on Instagram, WhatsApp, or wherever you prefer.', es: 'Guarde y publique el flujo. Copie el enlace público (/q/su-slug) y comparta en Instagram, WhatsApp, o donde prefiera.' },

    // 5. HOW IT WORKS FOR THE LEAD
    s5title: { pt: 'Como o Lead Vê', fr: 'Ce Que le Lead Voit', en: 'What the Lead Sees', es: 'Cómo Ve el Lead' },
    s5step1: { pt: 'Preenche nome, email e telefone', fr: 'Remplit nom, email et téléphone', en: 'Fills in name, email and phone', es: 'Completa nombre, email y teléfono' },
    s5step2: { pt: 'Responde perguntas qualificativas', fr: 'Répond aux questions de qualification', en: 'Answers qualifying questions', es: 'Responde preguntas calificativas' },
    s5step3: { pt: 'Escolhe o DIA no calendário', fr: 'Choisit le JOUR sur le calendrier', en: 'Picks the DAY on the calendar', es: 'Elige el DÍA en el calendario' },
    s5step4: { pt: 'Escolhe o HORÁRIO disponível', fr: 'Choisit l\'HEURE disponible', en: 'Picks the available TIME', es: 'Elige el HORARIO disponible' },
    s5step5: { pt: 'Confirma o agendamento', fr: 'Confirme le rendez-vous', en: 'Confirms the booking', es: 'Confirma el agendamiento' },
    s5step6: { pt: 'Evento criado no Google Calendar!', fr: 'Événement créé dans Google Calendar !', en: 'Event created in Google Calendar!', es: '¡Evento creado en Google Calendar!' },

    // 6. DASHBOARD
    s6title: { pt: 'Painel de Agendamentos', fr: 'Panneau de Rendez-vous', en: 'Scheduling Dashboard', es: 'Panel de Agendamientos' },
    s6p1: {
      pt: 'No painel de agendamentos (/admin/scheduling) você tem duas abas:',
      fr: 'Dans le panneau de rendez-vous (/admin/scheduling) vous avez deux onglets :',
      en: 'In the scheduling dashboard (/admin/scheduling) you have two tabs:',
      es: 'En el panel de agendamientos (/admin/scheduling) tiene dos pestañas:'
    },
    s6tab1t: { pt: 'Fluxos', fr: 'Flux', en: 'Flows', es: 'Flujos' },
    s6tab1d: { pt: 'Todos os seus fluxos de agendamento — crie novos, edite, publique e compartilhe.', fr: 'Tous vos flux de rendez-vous — créez, éditez, publiez et partagez.', en: 'All your scheduling flows — create new ones, edit, publish and share.', es: 'Todos sus flujos de agendamiento — cree nuevos, edite, publique y comparta.' },
    s6tab2t: { pt: 'Reservas', fr: 'Réservations', en: 'Bookings', es: 'Reservas' },
    s6tab2d: { pt: 'Veja todas as reservas feitas pelos leads — nome, contato, data, hora e status de cada agendamento.', fr: 'Voir toutes les réservations faites par les leads — nom, contact, date, heure et statut de chaque rendez-vous.', en: 'See all bookings made by leads — name, contact, date, time and status of each appointment.', es: 'Vea todas las reservas hechas por los leads — nombre, contacto, fecha, hora y estado de cada agendamiento.' },

    cta: { pt: 'Ir para Agendamentos', fr: 'Aller aux Rendez-vous', en: 'Go to Scheduling', es: 'Ir a Agendamientos' },
  };

  function _(key: string): string { return t[key]?.[lang] || t[key]?.['pt'] || key; }
</script>

<div class="min-h-screen bg-gradient-to-b from-white to-green-50">
  <!-- Header -->
  <header class="bg-white border-b sticky top-0 z-10">
    <div class="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
      <button onclick={() => goto('/admin/scheduling')} class="flex items-center gap-2 text-gray-500 hover:text-gray-800 cursor-pointer transition-colors text-sm">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" /></svg>
        {_('back')}
      </button>
      <div class="flex items-center gap-1.5 bg-gray-100 rounded-lg p-1">
        {#each (['pt', 'fr', 'en', 'es'] as const) as l}
          <button
            onclick={() => lang = l}
            class="px-3 py-1.5 rounded-md text-xs font-bold uppercase transition-all cursor-pointer
            {lang === l ? 'bg-white text-green-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}"
          >{l}</button>
        {/each}
      </div>
    </div>
  </header>

  <main class="max-w-4xl mx-auto px-6 py-12">

    <!-- Hero -->
    <div class="text-center mb-16">
      <div class="inline-flex items-center gap-2 bg-green-100 text-green-700 rounded-full px-4 py-1.5 text-xs font-semibold mb-4">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" /></svg>
        TRAINING
      </div>
      <h1 class="text-4xl font-black text-gray-900 mb-3">{_('title')}</h1>
      <p class="text-lg text-gray-500 max-w-2xl mx-auto">{_('subtitle')}</p>
    </div>

    <!-- 1. MISSION -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-green-600 text-white flex items-center justify-center font-black text-lg">1</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s1title')}</h2>
      </div>
      <div class="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
        <p class="text-gray-700 leading-relaxed mb-4">{_('s1p1')}</p>
        <p class="text-gray-600 leading-relaxed">{_('s1p2')}</p>
        <!-- Visual flow -->
        <div class="mt-8 flex items-center justify-center gap-2 flex-wrap">
          {#each [
            { label: 'LEAD', color: 'gray', icon: '&#128100;' },
            { label: 'PERGUNTAS', color: 'blue', icon: '&#10067;' },
            { label: 'CALENDÁRIO', color: 'green', icon: '&#128197;' },
            { label: 'HORÁRIO', color: 'emerald', icon: '&#128344;' },
            { label: 'GOOGLE CAL', color: 'purple', icon: '&#10003;' }
          ] as step, i}
            {#if i > 0}
              <svg class="w-5 h-5 text-gray-300 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
            {/if}
            <div class="bg-{step.color}-100 border-2 border-{step.color}-300 rounded-xl px-3 py-2.5 text-center min-w-[80px]">
              <div class="text-lg mb-0.5">{@html step.icon}</div>
              <span class="text-[10px] font-bold text-{step.color}-700 uppercase">{step.label}</span>
            </div>
          {/each}
        </div>
      </div>
    </section>

    <!-- 2. PROBLEM -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-green-600 text-white flex items-center justify-center font-black text-lg">2</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s2title')}</h2>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-red-50 border-2 border-red-200 rounded-2xl p-6">
          <div class="flex items-center gap-2 mb-4">
            <svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span class="font-bold text-red-700">{_('s2before')}</span>
          </div>
          <ul class="space-y-3">
            <li class="flex gap-2 text-sm text-red-700"><span class="text-red-400">&#10007;</span>{_('s2b1')}</li>
            <li class="flex gap-2 text-sm text-red-700"><span class="text-red-400">&#10007;</span>{_('s2b2')}</li>
            <li class="flex gap-2 text-sm text-red-700"><span class="text-red-400">&#10007;</span>{_('s2b3')}</li>
          </ul>
        </div>
        <div class="bg-green-50 border-2 border-green-200 rounded-2xl p-6">
          <div class="flex items-center gap-2 mb-4">
            <svg class="w-6 h-6 text-green-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span class="font-bold text-green-700">{_('s2after')}</span>
          </div>
          <ul class="space-y-3">
            <li class="flex gap-2 text-sm text-green-700"><span class="text-green-500">&#10003;</span>{_('s2a1')}</li>
            <li class="flex gap-2 text-sm text-green-700"><span class="text-green-500">&#10003;</span>{_('s2a2')}</li>
            <li class="flex gap-2 text-sm text-green-700"><span class="text-green-500">&#10003;</span>{_('s2a3')}</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 3. FEATURES -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-green-600 text-white flex items-center justify-center font-black text-lg">3</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s3title')}</h2>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {#each [
          { icon: '&#128269;', tk: 's3f1t', dk: 's3f1d' },
          { icon: '&#128197;', tk: 's3f2t', dk: 's3f2d' },
          { icon: '&#9201;', tk: 's3f3t', dk: 's3f3d' },
          { icon: '&#10004;', tk: 's3f4t', dk: 's3f4d' }
        ] as feat}
          <div class="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div class="text-2xl mb-3">{@html feat.icon}</div>
            <h3 class="font-bold text-gray-900 mb-2">{_(feat.tk)}</h3>
            <p class="text-sm text-gray-600 leading-relaxed">{_(feat.dk)}</p>
          </div>
        {/each}
      </div>
    </section>

    <!-- 4. QUICKSTART -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-green-600 text-white flex items-center justify-center font-black text-lg">4</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s4title')}</h2>
      </div>
      <div class="space-y-4">
        {#each [
          { step: 1, tk: 's4step1t', dk: 's4step1d' },
          { step: 2, tk: 's4step2t', dk: 's4step2d' },
          { step: 3, tk: 's4step3t', dk: 's4step3d' },
          { step: 4, tk: 's4step4t', dk: 's4step4d' }
        ] as s}
          <div class="bg-white rounded-2xl border border-gray-200 p-6 flex gap-5 items-start hover:shadow-md transition-shadow">
            <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
              <span class="text-lg font-black text-green-600">{s.step}</span>
            </div>
            <div>
              <h3 class="font-bold text-gray-900 mb-1">{_(s.tk)}</h3>
              <p class="text-sm text-gray-600 leading-relaxed">{_(s.dk)}</p>
            </div>
          </div>
        {/each}
      </div>
    </section>

    <!-- 5. LEAD VIEW -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-green-600 text-white flex items-center justify-center font-black text-lg">5</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s5title')}</h2>
      </div>
      <!-- Visual timeline -->
      <div class="bg-white rounded-2xl border border-gray-200 p-8">
        <div class="space-y-0">
          {#each [
            { tk: 's5step1', icon: '&#128100;', color: 'gray' },
            { tk: 's5step2', icon: '&#10067;', color: 'blue' },
            { tk: 's5step3', icon: '&#128197;', color: 'green' },
            { tk: 's5step4', icon: '&#128344;', color: 'emerald' },
            { tk: 's5step5', icon: '&#9989;', color: 'purple' },
            { tk: 's5step6', icon: '&#127881;', color: 'green' }
          ] as step, i}
            <div class="flex items-center gap-4">
              <div class="flex flex-col items-center">
                <div class="w-10 h-10 rounded-full bg-{step.color}-100 border-2 border-{step.color}-300 flex items-center justify-center text-lg">{@html step.icon}</div>
                {#if i < 5}
                  <div class="w-0.5 h-8 bg-gray-200"></div>
                {/if}
              </div>
              <p class="text-sm font-medium text-gray-700 {i === 5 ? 'text-green-700 font-bold' : ''}">{_(step.tk)}</p>
            </div>
          {/each}
        </div>
      </div>
    </section>

    <!-- 6. DASHBOARD -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-green-600 text-white flex items-center justify-center font-black text-lg">6</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s6title')}</h2>
      </div>
      <p class="text-gray-600 mb-6">{_('s6p1')}</p>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-white rounded-2xl border border-gray-200 p-6">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-3 h-3 rounded-full bg-green-500"></div>
            <h3 class="font-bold text-gray-900">{_('s6tab1t')}</h3>
          </div>
          <p class="text-sm text-gray-600">{_('s6tab1d')}</p>
        </div>
        <div class="bg-white rounded-2xl border border-gray-200 p-6">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-3 h-3 rounded-full bg-blue-500"></div>
            <h3 class="font-bold text-gray-900">{_('s6tab2t')}</h3>
          </div>
          <p class="text-sm text-gray-600">{_('s6tab2d')}</p>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <div class="text-center pb-12">
      <button
        onclick={() => goto('/admin/scheduling')}
        class="bg-green-600 text-white px-10 py-4 rounded-xl text-lg font-bold hover:bg-green-700 cursor-pointer transition-all shadow-lg shadow-green-600/25 active:scale-95"
      >
        {_('cta')} &rarr;
      </button>
    </div>
  </main>
</div>
