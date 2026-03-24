<script lang="ts">
  import { goto } from '$app/navigation';

  let lang = $state<'pt' | 'fr' | 'en' | 'es'>('pt');

  const t: Record<string, Record<string, string>> = {
    // ── NAV ──
    back: { pt: 'Voltar', fr: 'Retour', en: 'Back', es: 'Volver' },
    langLabel: { pt: 'Idioma', fr: 'Langue', en: 'Language', es: 'Idioma' },
    title: { pt: 'Treinamento: Orçamentos', fr: 'Formation: Devis', en: 'Training: Quotes', es: 'Capacitación: Presupuestos' },
    subtitle: { pt: 'Aprenda a criar orçamentos inteligentes com IA', fr: 'Apprenez à créer des devis intelligents avec IA', en: 'Learn to create intelligent quotes with AI', es: 'Aprenda a crear presupuestos inteligentes con IA' },

    // ── 1. MISSION ──
    s1title: { pt: 'A Missão do FlowQuote', fr: 'La Mission de FlowQuote', en: 'The FlowQuote Mission', es: 'La Misión de FlowQuote' },
    s1p1: {
      pt: 'O FlowQuote é um construtor visual de orçamentos com Inteligência Artificial. Ele permite que qualquer pessoa — mesmo sem conhecimento técnico — crie questionários inteligentes que geram orçamentos automáticos para seus clientes.',
      fr: 'FlowQuote est un constructeur visuel de devis avec Intelligence Artificielle. Il permet à toute personne — même sans connaissance technique — de créer des questionnaires intelligents qui génèrent des devis automatiques pour ses clients.',
      en: 'FlowQuote is a visual quote builder with Artificial Intelligence. It allows anyone — even without technical knowledge — to create smart questionnaires that automatically generate quotes for their clients.',
      es: 'FlowQuote es un constructor visual de presupuestos con Inteligencia Artificial. Permite que cualquier persona — incluso sin conocimiento técnico — cree cuestionarios inteligentes que generan presupuestos automáticos para sus clientes.'
    },
    s1p2: {
      pt: 'Imagine que você é um eletricista, um encanador, ou dono de uma escola. Seu cliente acessa um link, responde algumas perguntas, e recebe um orçamento profissional — tudo automático!',
      fr: 'Imaginez que vous êtes un électricien, un plombier, ou propriétaire d\'une école. Votre client accède à un lien, répond à quelques questions, et reçoit un devis professionnel — tout automatiquement !',
      en: 'Imagine you\'re an electrician, a plumber, or a school owner. Your client clicks a link, answers a few questions, and receives a professional quote — all automatic!',
      es: 'Imagina que eres electricista, plomero, o dueño de una escuela. Tu cliente accede a un enlace, responde algunas preguntas, y recibe un presupuesto profesional — ¡todo automático!'
    },

    // ── 2. PROBLEM ──
    s2title: { pt: 'Qual Problema Resolve?', fr: 'Quel Problème Résout-il ?', en: 'What Problem Does It Solve?', es: '¿Qué Problema Resuelve?' },
    s2before: { pt: 'ANTES do FlowQuote', fr: 'AVANT FlowQuote', en: 'BEFORE FlowQuote', es: 'ANTES de FlowQuote' },
    s2after: { pt: 'DEPOIS do FlowQuote', fr: 'APRÈS FlowQuote', en: 'AFTER FlowQuote', es: 'DESPUÉS de FlowQuote' },
    s2b1: { pt: 'Cliente liga, manda mensagem... e espera horas/dias por um orçamento', fr: 'Le client appelle, envoie un message... et attend des heures/jours pour un devis', en: 'Client calls, sends a message... and waits hours/days for a quote', es: 'El cliente llama, envía mensaje... y espera horas/días por un presupuesto' },
    s2b2: { pt: 'Você calcula manualmente, erra preços, esquece itens', fr: 'Vous calculez manuellement, erreurs de prix, oubli d\'articles', en: 'You calculate manually, get prices wrong, forget items', es: 'Calculas manualmente, te equivocas en precios, olvidas ítems' },
    s2b3: { pt: 'Perde vendas porque demorou para responder', fr: 'Perd des ventes car trop lent à répondre', en: 'Lose sales because you took too long to respond', es: 'Pierdes ventas porque tardaste en responder' },
    s2a1: { pt: 'Cliente acessa o link → responde perguntas → recebe orçamento na hora', fr: 'Le client accède au lien → répond aux questions → reçoit le devis instantanément', en: 'Client clicks the link → answers questions → gets a quote instantly', es: 'El cliente accede al enlace → responde preguntas → recibe presupuesto al instante' },
    s2a2: { pt: 'A IA calcula com base na sua tabela de preços — sem erros', fr: 'L\'IA calcule en fonction de votre liste de prix — sans erreurs', en: 'AI calculates based on your price list — no errors', es: 'La IA calcula con base en tu lista de precios — sin errores' },
    s2a3: { pt: 'Atendimento 24/7, mesmo quando você está dormindo', fr: 'Service 24/7, même quand vous dormez', en: '24/7 service, even when you\'re sleeping', es: 'Atención 24/7, incluso cuando estás durmiendo' },

    // ── 3. FEATURES ──
    s3title: { pt: 'Visão Geral das Funcionalidades', fr: 'Aperçu des Fonctionnalités', en: 'Features Overview', es: 'Visión General de Funcionalidades' },
    s3f1t: { pt: 'Editor Visual (Drag & Drop)', fr: 'Éditeur Visuel (Glisser & Déposer)', en: 'Visual Editor (Drag & Drop)', es: 'Editor Visual (Arrastrar y Soltar)' },
    s3f1d: { pt: 'Monte seu questionário arrastando blocos: Início, Pergunta, Mensagem e Fim. Conecte-os com setas para criar o caminho do cliente.', fr: 'Construisez votre questionnaire en glissant des blocs : Début, Question, Message et Fin. Connectez-les avec des flèches.', en: 'Build your questionnaire by dragging blocks: Start, Question, Message and End. Connect them with arrows to create the client path.', es: 'Monte su cuestionario arrastrando bloques: Inicio, Pregunta, Mensaje y Fin. Conéctelos con flechas para crear el camino del cliente.' },
    s3f2t: { pt: '9 Tipos de Pergunta', fr: '9 Types de Questions', en: '9 Question Types', es: '9 Tipos de Pregunta' },
    s3f2d: { pt: 'Escolha única, Sim/Não, Número, Texto, Múltipla escolha, Data, Dropdown, Avaliação e Foto.', fr: 'Choix unique, Oui/Non, Nombre, Texte, Choix multiple, Date, Liste déroulante, Évaluation et Photo.', en: 'Single choice, Yes/No, Number, Text, Multiple choice, Date, Dropdown, Rating and Photo.', es: 'Opción única, Sí/No, Número, Texto, Opción múltiple, Fecha, Desplegable, Evaluación y Foto.' },
    s3f3t: { pt: 'Tabela CSV de Preços', fr: 'Tableau CSV de Prix', en: 'CSV Price Table', es: 'Tabla CSV de Precios' },
    s3f3d: { pt: 'Carregue sua tabela de preços em CSV. A IA usa APENAS esses preços — nunca inventa valores.', fr: 'Chargez votre liste de prix en CSV. L\'IA utilise UNIQUEMENT ces prix — ne jamais inventer des valeurs.', en: 'Upload your price list as CSV. AI uses ONLY those prices — never makes up values.', es: 'Cargue su tabla de precios en CSV. La IA usa SOLO esos precios — nunca inventa valores.' },
    s3f4t: { pt: 'IA Gera o Orçamento', fr: 'L\'IA Génère le Devis', en: 'AI Generates the Quote', es: 'La IA Genera el Presupuesto' },
    s3f4d: { pt: 'Com base nas respostas do cliente e na tabela de preços, a IA calcula e gera um orçamento profissional com itens, preços, impostos e recomendações.', fr: 'Sur la base des réponses du client et de la liste de prix, l\'IA calcule et génère un devis professionnel avec articles, prix, taxes et recommandations.', en: 'Based on client answers and the price list, AI calculates and generates a professional quote with items, prices, taxes and recommendations.', es: 'Con base en las respuestas del cliente y la tabla de precios, la IA calcula y genera un presupuesto profesional con ítems, precios, impuestos y recomendaciones.' },

    // ── 4. QUICKSTART ──
    s4title: { pt: 'Quickstart: Seu Primeiro Orçamento', fr: 'Démarrage Rapide: Votre Premier Devis', en: 'Quickstart: Your First Quote', es: 'Inicio Rápido: Su Primer Presupuesto' },
    s4step1t: { pt: 'Crie um novo fluxo', fr: 'Créez un nouveau flux', en: 'Create a new flow', es: 'Cree un nuevo flujo' },
    s4step1d: { pt: 'Clique em "+ Novo Fluxo" no painel admin. Dê um nome (ex: "Orçamento Elétrico") e comece a editar.', fr: 'Cliquez sur "+ Nouveau Flux" dans le panneau admin. Donnez un nom (ex: "Devis Électrique") et commencez à éditer.', en: 'Click "+ New Flow" in the admin panel. Give it a name (e.g., "Electrical Quote") and start editing.', es: 'Haga clic en "+ Nuevo Flujo" en el panel admin. Dé un nombre (ej: "Presupuesto Eléctrico") y comience a editar.' },
    s4step2t: { pt: 'Adicione perguntas', fr: 'Ajoutez des questions', en: 'Add questions', es: 'Agregue preguntas' },
    s4step2d: { pt: 'Arraste blocos de "Pergunta" para a área de trabalho. Configure o tipo (escolha única, sim/não, etc.) e as opções.', fr: 'Glissez des blocs "Question" vers l\'espace de travail. Configurez le type (choix unique, oui/non, etc.) et les options.', en: 'Drag "Question" blocks to the workspace. Configure the type (single choice, yes/no, etc.) and options.', es: 'Arrastre bloques de "Pregunta" al área de trabajo. Configure el tipo (opción única, sí/no, etc.) y las opciones.' },
    s4step3t: { pt: 'Carregue a tabela de preços (CSV)', fr: 'Chargez la liste de prix (CSV)', en: 'Upload the price list (CSV)', es: 'Cargue la tabla de precios (CSV)' },
    s4step3d: { pt: 'No nó final (Fim), carregue um arquivo CSV com seus produtos e preços. Formato: nome do produto, preço unitário.', fr: 'Dans le nœud final (Fin), chargez un fichier CSV avec vos produits et prix. Format : nom du produit, prix unitaire.', en: 'In the end node (End), upload a CSV file with your products and prices. Format: product name, unit price.', es: 'En el nodo final (Fin), cargue un archivo CSV con sus productos y precios. Formato: nombre del producto, precio unitario.' },
    s4step4t: { pt: 'Vincule perguntas a produtos', fr: 'Liez les questions aux produits', en: 'Link questions to products', es: 'Vincule preguntas a productos' },
    s4step4d: { pt: 'Em cada opção de pergunta, vincule ao produto do CSV correspondente. Isso é ESSENCIAL para a IA calcular corretamente.', fr: 'Dans chaque option de question, liez au produit du CSV correspondant. C\'est ESSENTIEL pour que l\'IA calcule correctement.', en: 'In each question option, link to the corresponding CSV product. This is ESSENTIAL for the AI to calculate correctly.', es: 'En cada opción de pregunta, vincule al producto del CSV correspondiente. Esto es ESENCIAL para que la IA calcule correctamente.' },
    s4step5t: { pt: 'Publique e compartilhe', fr: 'Publiez et partagez', en: 'Publish and share', es: 'Publique y comparta' },
    s4step5d: { pt: 'Salve, publique o fluxo e compartilhe o link com seus clientes. Eles acessam, respondem e recebem o orçamento!', fr: 'Enregistrez, publiez le flux et partagez le lien avec vos clients. Ils accèdent, répondent et reçoivent le devis !', en: 'Save, publish the flow and share the link with your clients. They access it, answer, and receive the quote!', es: 'Guarde, publique el flujo y comparta el enlace con sus clientes. ¡Ellos acceden, responden y reciben el presupuesto!' },

    // ── 5. QUESTIONS ──
    s5title: { pt: 'Perguntas de Contexto vs Perguntas de Orçamento', fr: 'Questions de Contexte vs Questions de Devis', en: 'Context Questions vs Quote Questions', es: 'Preguntas de Contexto vs Preguntas de Presupuesto' },
    s5intro: {
      pt: 'Nem toda pergunta gera um item no orçamento. Existem dois tipos:',
      fr: 'Toutes les questions ne génèrent pas un article dans le devis. Il en existe deux types :',
      en: 'Not every question generates an item in the quote. There are two types:',
      es: 'No toda pregunta genera un ítem en el presupuesto. Existen dos tipos:'
    },
    s5ctx: { pt: 'Perguntas de CONTEXTO', fr: 'Questions de CONTEXTE', en: 'CONTEXT Questions', es: 'Preguntas de CONTEXTO' },
    s5ctxDesc: {
      pt: 'Servem para a IA entender a situação do cliente. NÃO precisam de produto vinculado.',
      fr: 'Servent à l\'IA pour comprendre la situation du client. N\'ont PAS besoin de produit lié.',
      en: 'Help the AI understand the client\'s situation. Do NOT need a linked product.',
      es: 'Sirven para que la IA entienda la situación del cliente. NO necesitan producto vinculado.'
    },
    s5ctxEx1: { pt: '"Quantos cômodos tem sua casa?"', fr: '"Combien de pièces a votre maison ?"', en: '"How many rooms does your house have?"', es: '"¿Cuántas habitaciones tiene su casa?"' },
    s5ctxEx2: { pt: '"Qual o tipo do seu painel elétrico? (100A / 200A)"', fr: '"Quel type de panneau électrique ? (100A / 200A)"', en: '"What type is your electrical panel? (100A / 200A)"', es: '"¿Qué tipo es su panel eléctrico? (100A / 200A)"' },
    s5ctxEx3: { pt: '"Há acesso fácil ao local de instalação?"', fr: '"Y a-t-il un accès facile au site d\'installation ?"', en: '"Is there easy access to the installation site?"', es: '"¿Hay acceso fácil al lugar de instalación?"' },
    s5quote: { pt: 'Perguntas de ORÇAMENTO', fr: 'Questions de DEVIS', en: 'QUOTE Questions', es: 'Preguntas de PRESUPUESTO' },
    s5quoteDesc: {
      pt: 'Cada opção TEM um produto vinculado do CSV. A resposta do cliente determina qual produto entra no orçamento.',
      fr: 'Chaque option A un produit lié du CSV. La réponse du client détermine quel produit entre dans le devis.',
      en: 'Each option HAS a linked product from CSV. The client\'s answer determines which product goes in the quote.',
      es: 'Cada opción TIENE un producto vinculado del CSV. La respuesta del cliente determina qué producto entra en el presupuesto.'
    },
    s5quoteEx1: { pt: '"Qual tipo de tomada?" → Tomada 110V (R$25) / Tomada 220V (R$35)', fr: '"Quel type de prise ?" → Prise 110V (25$) / Prise 220V (35$)', en: '"What type of outlet?" → 110V Outlet ($25) / 220V Outlet ($35)', es: '"¿Qué tipo de toma?" → Toma 110V ($25) / Toma 220V ($35)' },
    s5quoteEx2: { pt: '"Quantos metros de fio?" → Resposta numérica vinculada ao produto "Fio elétrico (por metro)"', fr: '"Combien de mètres de câble ?" → Réponse numérique liée au produit "Câble électrique (par mètre)"', en: '"How many meters of wire?" → Numeric answer linked to product "Electric wire (per meter)"', es: '"¿Cuántos metros de cable?" → Respuesta numérica vinculada al producto "Cable eléctrico (por metro)"' },

    // ── 6. IMPORTANT ──
    s6title: { pt: 'IMPORTANTE: Regras da IA', fr: 'IMPORTANT : Règles de l\'IA', en: 'IMPORTANT: AI Rules', es: 'IMPORTANTE: Reglas de la IA' },
    s6rule1t: { pt: 'A IA SÓ calcula se o produto estiver no CSV', fr: 'L\'IA calcule UNIQUEMENT si le produit est dans le CSV', en: 'AI ONLY calculates if the product is in the CSV', es: 'La IA SOLO calcula si el producto está en el CSV' },
    s6rule1d: {
      pt: 'Se você não carregou um CSV com preços, ou se o produto não existe na tabela, a IA não terá preço para usar. Resultado: o item aparecerá como "A consultar" ou será ignorado.',
      fr: 'Si vous n\'avez pas chargé un CSV avec les prix, ou si le produit n\'existe pas dans la table, l\'IA n\'aura pas de prix. Résultat : l\'article apparaîtra comme "À consulter" ou sera ignoré.',
      en: 'If you haven\'t uploaded a CSV with prices, or if the product doesn\'t exist in the table, the AI won\'t have a price to use. Result: the item will appear as "To be quoted" or be ignored.',
      es: 'Si no cargó un CSV con precios, o si el producto no existe en la tabla, la IA no tendrá precio para usar. Resultado: el ítem aparecerá como "A consultar" o será ignorado.'
    },
    s6rule2t: { pt: 'A IA SÓ inclui se a pergunta estiver vinculada ao produto', fr: 'L\'IA inclut UNIQUEMENT si la question est liée au produit', en: 'AI ONLY includes if the question is linked to the product', es: 'La IA SOLO incluye si la pregunta está vinculada al producto' },
    s6rule2d: {
      pt: 'Mesmo que o produto exista no CSV, se a opção da pergunta não estiver vinculada a ele, a IA não saberá que o cliente escolheu aquele produto. Vincule SEMPRE!',
      fr: 'Même si le produit existe dans le CSV, si l\'option de la question n\'est pas liée à lui, l\'IA ne saura pas que le client a choisi ce produit. Liez TOUJOURS !',
      en: 'Even if the product exists in the CSV, if the question option is not linked to it, the AI won\'t know the client chose that product. ALWAYS link!',
      es: 'Aunque el producto exista en el CSV, si la opción de la pregunta no está vinculada a él, la IA no sabrá que el cliente eligió ese producto. ¡Vincule SIEMPRE!'
    },
    s6summary: {
      pt: 'CSV carregado + Pergunta vinculada ao produto = Orçamento perfeito',
      fr: 'CSV chargé + Question liée au produit = Devis parfait',
      en: 'CSV uploaded + Question linked to product = Perfect quote',
      es: 'CSV cargado + Pregunta vinculada al producto = Presupuesto perfecto'
    },

    // ── CTA ──
    cta: { pt: 'Criar Meu Primeiro Orçamento', fr: 'Créer Mon Premier Devis', en: 'Create My First Quote', es: 'Crear Mi Primer Presupuesto' },
  };

  function _(key: string): string { return t[key]?.[lang] || t[key]?.['pt'] || key; }
</script>

<div class="min-h-screen bg-gradient-to-b from-white to-blue-50">
  <!-- Header -->
  <header class="bg-white border-b sticky top-0 z-10">
    <div class="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
      <button onclick={() => goto('/admin/flows')} class="flex items-center gap-2 text-gray-500 hover:text-gray-800 cursor-pointer transition-colors text-sm">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" /></svg>
        {_('back')}
      </button>
      <!-- Language selector -->
      <div class="flex items-center gap-1.5 bg-gray-100 rounded-lg p-1">
        {#each (['pt', 'fr', 'en', 'es'] as const) as l}
          <button
            onclick={() => lang = l}
            class="px-3 py-1.5 rounded-md text-xs font-bold uppercase transition-all cursor-pointer
            {lang === l ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}"
          >{l}</button>
        {/each}
      </div>
    </div>
  </header>

  <main class="max-w-4xl mx-auto px-6 py-12">

    <!-- Hero -->
    <div class="text-center mb-16">
      <div class="inline-flex items-center gap-2 bg-blue-100 text-blue-700 rounded-full px-4 py-1.5 text-xs font-semibold mb-4">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.438 60.438 0 00-.491 6.347A48.62 48.62 0 0112 20.904a48.62 48.62 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.636 50.636 0 00-2.658-.813A59.906 59.906 0 0112 3.493a59.903 59.903 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" /></svg>
        TRAINING
      </div>
      <h1 class="text-4xl font-black text-gray-900 mb-3">{_('title')}</h1>
      <p class="text-lg text-gray-500 max-w-2xl mx-auto">{_('subtitle')}</p>
    </div>

    <!-- ═══════════════════ 1. MISSION ═══════════════════ -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-lg">1</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s1title')}</h2>
      </div>
      <div class="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
        <p class="text-gray-700 leading-relaxed mb-4">{_('s1p1')}</p>
        <p class="text-gray-600 leading-relaxed">{_('s1p2')}</p>
        <!-- Visual: Flow diagram -->
        <div class="mt-8 flex items-center justify-center gap-3 flex-wrap">
          <div class="flex items-center gap-3">
            <div class="bg-green-100 border-2 border-green-400 rounded-xl px-4 py-3 text-center">
              <div class="w-6 h-6 rounded-full bg-green-500 mx-auto mb-1"></div>
              <span class="text-xs font-bold text-green-800">START</span>
            </div>
            <svg class="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
          </div>
          <div class="flex items-center gap-3">
            <div class="bg-blue-100 border-2 border-blue-400 rounded-xl px-4 py-3 text-center">
              <div class="w-6 h-6 rounded-full bg-blue-500 mx-auto mb-1"></div>
              <span class="text-xs font-bold text-blue-800">QUESTION</span>
            </div>
            <svg class="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
          </div>
          <div class="flex items-center gap-3">
            <div class="bg-blue-100 border-2 border-blue-400 rounded-xl px-4 py-3 text-center">
              <div class="w-6 h-6 rounded-full bg-blue-500 mx-auto mb-1"></div>
              <span class="text-xs font-bold text-blue-800">QUESTION</span>
            </div>
            <svg class="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
          </div>
          <div class="bg-purple-100 border-2 border-purple-400 rounded-xl px-4 py-3 text-center">
            <div class="w-6 h-6 rounded-full bg-purple-500 mx-auto mb-1"></div>
            <span class="text-xs font-bold text-purple-800">QUOTE (IA)</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════ 2. PROBLEM ═══════════════════ -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-lg">2</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s2title')}</h2>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Before -->
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
        <!-- After -->
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

    <!-- ═══════════════════ 3. FEATURES ═══════════════════ -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-lg">3</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s3title')}</h2>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {#each [
          { icon: '&#9998;', color: 'blue', tk: 's3f1t', dk: 's3f1d' },
          { icon: '&#10067;', color: 'purple', tk: 's3f2t', dk: 's3f2d' },
          { icon: '&#128200;', color: 'green', tk: 's3f3t', dk: 's3f3d' },
          { icon: '&#9889;', color: 'amber', tk: 's3f4t', dk: 's3f4d' }
        ] as feat}
          <div class="bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div class="text-2xl mb-3">{@html feat.icon}</div>
            <h3 class="font-bold text-gray-900 mb-2">{_(feat.tk)}</h3>
            <p class="text-sm text-gray-600 leading-relaxed">{_(feat.dk)}</p>
          </div>
        {/each}
      </div>
    </section>

    <!-- ═══════════════════ 4. QUICKSTART ═══════════════════ -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-lg">4</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s4title')}</h2>
      </div>
      <div class="space-y-4">
        {#each [
          { step: 1, tk: 's4step1t', dk: 's4step1d', color: 'green' },
          { step: 2, tk: 's4step2t', dk: 's4step2d', color: 'blue' },
          { step: 3, tk: 's4step3t', dk: 's4step3d', color: 'amber' },
          { step: 4, tk: 's4step4t', dk: 's4step4d', color: 'purple' },
          { step: 5, tk: 's4step5t', dk: 's4step5d', color: 'emerald' }
        ] as s}
          <div class="bg-white rounded-2xl border border-gray-200 p-6 flex gap-5 items-start hover:shadow-md transition-shadow">
            <div class="w-12 h-12 rounded-full bg-{s.color}-100 flex items-center justify-center flex-shrink-0">
              <span class="text-lg font-black text-{s.color}-600">{s.step}</span>
            </div>
            <div>
              <h3 class="font-bold text-gray-900 mb-1">{_(s.tk)}</h3>
              <p class="text-sm text-gray-600 leading-relaxed">{_(s.dk)}</p>
            </div>
          </div>
        {/each}
      </div>
    </section>

    <!-- ═══════════════════ 5. CONTEXT vs QUOTE ═══════════════════ -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-lg">5</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s5title')}</h2>
      </div>
      <p class="text-gray-600 mb-6">{_('s5intro')}</p>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Context -->
        <div class="rounded-2xl border-2 border-gray-300 border-dashed p-6 bg-gray-50">
          <div class="flex items-center gap-2 mb-4">
            <svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" /></svg>
            <h3 class="text-lg font-bold text-gray-700">{_('s5ctx')}</h3>
          </div>
          <p class="text-sm text-gray-600 mb-4">{_('s5ctxDesc')}</p>
          <div class="space-y-2">
            {#each ['s5ctxEx1', 's5ctxEx2', 's5ctxEx3'] as ex}
              <div class="bg-white rounded-lg px-4 py-2.5 text-sm text-gray-700 border border-gray-200 italic">{_(ex)}</div>
            {/each}
          </div>
          <!-- Visual: No product link -->
          <div class="mt-4 flex items-center gap-2 text-xs text-gray-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.181 8.68a4.503 4.503 0 011.903 6.405m-9.768-2.782L3.56 14.06a4.5 4.5 0 006.364 6.364l3.12-3.12" /><path stroke-linecap="round" stroke-linejoin="round" d="M17.94 10.94l1.756-1.756a4.5 4.5 0 00-6.364-6.364l-3.12 3.12" /></svg>
            {lang === 'pt' ? 'Sem vinculo ao CSV' : lang === 'fr' ? 'Pas de lien au CSV' : lang === 'en' ? 'No link to CSV' : 'Sin vinculo al CSV'}
          </div>
        </div>

        <!-- Quote -->
        <div class="rounded-2xl border-2 border-blue-400 p-6 bg-blue-50">
          <div class="flex items-center gap-2 mb-4">
            <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <h3 class="text-lg font-bold text-blue-700">{_('s5quote')}</h3>
          </div>
          <p class="text-sm text-blue-700 mb-4">{_('s5quoteDesc')}</p>
          <div class="space-y-2">
            {#each ['s5quoteEx1', 's5quoteEx2'] as ex}
              <div class="bg-white rounded-lg px-4 py-2.5 text-sm text-blue-800 border border-blue-200">{_(ex)}</div>
            {/each}
          </div>
          <!-- Visual: Product linked -->
          <div class="mt-4 flex items-center gap-2 text-xs text-blue-500 font-semibold">
            <svg class="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" /></svg>
            {lang === 'pt' ? 'Vinculado ao produto do CSV' : lang === 'fr' ? 'Lié au produit du CSV' : lang === 'en' ? 'Linked to CSV product' : 'Vinculado al producto del CSV'}
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════ 6. IMPORTANT ═══════════════════ -->
    <section class="mb-16">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-red-600 text-white flex items-center justify-center font-black text-lg">!</div>
        <h2 class="text-2xl font-bold text-gray-900">{_('s6title')}</h2>
      </div>

      <div class="bg-red-50 border-2 border-red-200 rounded-2xl p-8 space-y-6">
        <!-- Rule 1 -->
        <div class="flex gap-4 items-start">
          <div class="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
            <span class="text-lg font-black text-red-600">1</span>
          </div>
          <div>
            <h3 class="font-bold text-red-800 mb-1">{_('s6rule1t')}</h3>
            <p class="text-sm text-red-700 leading-relaxed">{_('s6rule1d')}</p>
          </div>
        </div>
        <!-- Rule 2 -->
        <div class="flex gap-4 items-start">
          <div class="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
            <span class="text-lg font-black text-red-600">2</span>
          </div>
          <div>
            <h3 class="font-bold text-red-800 mb-1">{_('s6rule2t')}</h3>
            <p class="text-sm text-red-700 leading-relaxed">{_('s6rule2d')}</p>
          </div>
        </div>
        <!-- Formula -->
        <div class="bg-white rounded-xl p-5 text-center border border-red-200">
          <p class="text-lg font-black text-gray-900">{_('s6summary')}</p>
          <div class="flex items-center justify-center gap-3 mt-3 text-sm">
            <span class="bg-green-100 text-green-700 px-3 py-1 rounded-full font-semibold">CSV</span>
            <span class="text-gray-400 font-bold">+</span>
            <span class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-semibold">{lang === 'pt' ? 'Vinculo' : lang === 'fr' ? 'Lien' : lang === 'en' ? 'Link' : 'Vinculo'}</span>
            <span class="text-gray-400 font-bold">=</span>
            <span class="bg-purple-100 text-purple-700 px-3 py-1 rounded-full font-semibold">&#10003;</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════ CTA ═══════════════════ -->
    <div class="text-center pb-12">
      <button
        onclick={() => goto('/admin/flows')}
        class="bg-blue-600 text-white px-10 py-4 rounded-xl text-lg font-bold hover:bg-blue-700 cursor-pointer transition-all shadow-lg shadow-blue-600/25 active:scale-95"
      >
        {_('cta')} &rarr;
      </button>
    </div>
  </main>
</div>
