"use strict";
// A1 (beginner) vocabulary by topic. Each word is "French|English".
// "(m)" / "(f)" marks gender where the article doesn't show it (l', les).
const A1_TOPICS = [
  { id: "greet", icon: "👋", name: "Greetings", words: [
    "bonjour|hello", "bonsoir|good evening", "salut|hi / bye", "au revoir|goodbye", "bonne nuit|good night",
    "à bientôt|see you soon", "merci|thank you", "de rien|you're welcome", "s'il vous plaît|please",
    "oui|yes", "non|no", "pardon|sorry", "excusez-moi|excuse me", "d'accord|okay", "bienvenue|welcome",
    "Comment ça va ?|How are you?", "Ça va bien.|I'm fine."] },
  { id: "num", icon: "🔢", name: "Numbers", words: [
    "un|one", "deux|two", "trois|three", "quatre|four", "cinq|five", "six|six", "sept|seven", "huit|eight",
    "neuf|nine", "dix|ten", "onze|eleven", "douze|twelve", "quinze|fifteen", "vingt|twenty", "trente|thirty",
    "cinquante|fifty", "cent|one hundred", "mille|one thousand"] },
  { id: "color", icon: "🎨", name: "Colours", words: [
    "rouge|red", "bleu|blue", "vert|green", "jaune|yellow", "noir|black", "blanc|white", "orange|orange",
    "rose|pink", "gris|grey", "marron|brown", "violet|purple"] },
  { id: "family", icon: "👨‍👩‍👧", name: "Family", words: [
    "la famille|family", "la mère|mother", "le père|father", "les parents (m)|parents", "le frère|brother",
    "la sœur|sister", "le fils|son", "la fille|daughter / girl", "le mari|husband", "la femme|wife / woman",
    "l'enfant (m/f)|child", "le bébé|baby", "le grand-père|grandfather", "la grand-mère|grandmother",
    "l'ami (m)|friend", "le garçon|boy"] },
  { id: "food", icon: "🥖", name: "Food & drink", words: [
    "le pain|bread", "l'eau (f)|water", "le lait|milk", "le café|coffee", "le thé|tea", "le vin|wine",
    "le jus|juice", "la viande|meat", "le poulet|chicken", "le poisson|fish", "le fromage|cheese",
    "l'œuf (m)|egg", "la pomme|apple", "la banane|banana", "les légumes (m)|vegetables", "le riz|rice",
    "le sucre|sugar", "le sel|salt", "la soupe|soup", "le gâteau|cake", "le petit-déjeuner|breakfast",
    "le déjeuner|lunch", "le dîner|dinner"] },
  { id: "days", icon: "📅", name: "Days & time", words: [
    "lundi|Monday", "mardi|Tuesday", "mercredi|Wednesday", "jeudi|Thursday", "vendredi|Friday",
    "samedi|Saturday", "dimanche|Sunday", "aujourd'hui|today", "demain|tomorrow", "hier|yesterday",
    "le matin|morning", "l'après-midi (m)|afternoon", "le soir|evening", "la nuit|night", "le jour|day",
    "la semaine|week", "le mois|month", "l'an (m)|year", "l'heure (f)|hour", "maintenant|now"] },
  { id: "months", icon: "🗓️", name: "Months & seasons", words: [
    "janvier|January", "février|February", "mars|March", "avril|April", "mai|May", "juin|June",
    "juillet|July", "août|August", "septembre|September", "octobre|October", "novembre|November",
    "décembre|December", "le printemps|spring", "l'été (m)|summer", "l'automne (m)|autumn", "l'hiver (m)|winter"] },
  { id: "body", icon: "🧍", name: "Body", words: [
    "la tête|head", "les yeux (m)|eyes", "le nez|nose", "la bouche|mouth", "l'oreille (f)|ear",
    "les cheveux (m)|hair", "la main|hand", "le bras|arm", "la jambe|leg", "le pied|foot", "le dos|back",
    "le ventre|stomach / belly", "la dent|tooth"] },
  { id: "home", icon: "🏠", name: "Home", words: [
    "la maison|house", "l'appartement (m)|apartment", "la chambre|bedroom", "la cuisine|kitchen",
    "le salon|living room", "la salle de bains|bathroom", "la porte|door", "la fenêtre|window",
    "la table|table", "la chaise|chair", "le lit|bed", "la clé|key", "le jardin|garden"] },
  { id: "clothes", icon: "👕", name: "Clothes", words: [
    "le pantalon|trousers", "la chemise|shirt", "le t-shirt|T-shirt", "la robe|dress", "la jupe|skirt",
    "le pull|jumper / sweater", "la veste|jacket", "le manteau|coat", "les chaussures (f)|shoes",
    "les chaussettes (f)|socks", "le chapeau|hat", "le sac|bag"] },
  { id: "weather", icon: "⛅", name: "Weather", words: [
    "Il fait beau.|The weather is nice.", "Il fait chaud.|It's hot.", "Il fait froid.|It's cold.",
    "Il pleut.|It's raining.", "Il neige.|It's snowing.", "le soleil|sun", "la pluie|rain", "le vent|wind",
    "le nuage|cloud", "la neige|snow", "le temps|weather / time"] },
  { id: "places", icon: "🏙️", name: "Town & places", words: [
    "la ville|town / city", "la rue|street", "l'école (f)|school", "la gare|train station", "la banque|bank",
    "le magasin|shop", "le supermarché|supermarket", "la boulangerie|bakery", "le restaurant|restaurant",
    "l'hôpital (m)|hospital", "la pharmacie|pharmacy", "la poste|post office", "le parc|park",
    "la plage|beach", "le musée|museum", "l'hôtel (m)|hotel"] },
  { id: "transport", icon: "🚆", name: "Transport", words: [
    "la voiture|car", "le bus|bus", "le train|train", "l'avion (m)|plane", "le vélo|bike", "le métro|underground / subway",
    "le bateau|boat", "le taxi|taxi", "à pied|on foot", "le billet|ticket"] },
  { id: "animals", icon: "🐶", name: "Animals", words: [
    "le chien|dog", "le chat|cat", "l'oiseau (m)|bird", "le cheval|horse", "la vache|cow", "le cochon|pig",
    "le mouton|sheep", "le lapin|rabbit", "la souris|mouse", "le poisson rouge|goldfish"] },
  { id: "school", icon: "✏️", name: "Classroom", words: [
    "le livre|book", "le cahier|notebook", "le stylo|pen", "le crayon|pencil", "le professeur|teacher",
    "l'étudiant (m)|student", "la classe|class", "la question|question", "la réponse|answer",
    "le mot|word", "la page|page", "l'ordinateur (m)|computer"] },
  { id: "verbs", icon: "🏃", name: "Common verbs", words: [
    "être|to be", "avoir|to have", "aller|to go", "faire|to do / make", "venir|to come", "manger|to eat",
    "boire|to drink", "parler|to speak", "habiter|to live (in)", "aimer|to like / love", "voir|to see",
    "dormir|to sleep", "travailler|to work", "lire|to read", "écrire|to write", "acheter|to buy",
    "vouloir|to want", "pouvoir|to be able to", "comprendre|to understand", "apprendre|to learn"] },
  { id: "adj", icon: "✨", name: "Describing words", words: [
    "grand|big / tall", "petit|small", "bon|good", "mauvais|bad", "beau|beautiful", "jeune|young",
    "vieux|old", "nouveau|new", "facile|easy", "difficile|difficult", "cher|expensive", "chaud|hot",
    "froid|cold", "content|happy / pleased", "triste|sad", "fatigué|tired"] },
  { id: "small", icon: "❓", name: "Question & little words", words: [
    "qui|who", "quoi|what", "où|where", "quand|when", "comment|how", "pourquoi|why", "combien|how much / many",
    "et|and", "mais|but", "ou|or", "avec|with", "très|very", "aussi|also / too", "beaucoup|a lot"] },
];
