"use strict";
// Vocab game words by CEFR level. Each line: French | English | French example | English example
const LEVELS = [
{ id: "A1", name: "Beginner", words: `
le pain|bread|Je mange du pain le matin.|I eat bread in the morning.
la maison|house|Ma maison est petite.|My house is small.
le chien|dog|Le chien joue dans le jardin.|The dog is playing in the garden.
l'eau|water|Je bois de l'eau.|I drink water.
la voiture|car|Ma voiture est rouge.|My car is red.
le livre|book|Je lis un livre.|I'm reading a book.
manger|to eat|Nous mangeons à midi.|We eat at noon.
boire|to drink|Il boit un café.|He's drinking a coffee.
parler|to speak|Je parle un peu français.|I speak a little French.
aimer|to like / to love|J'aime la musique.|I like music.
habiter|to live (in)|J'habite à Paris.|I live in Paris.
aller|to go|Je vais à l'école.|I go to school.
grand|big / tall|Mon frère est grand.|My brother is tall.
petit|small|C'est un petit chat.|It's a small cat.
la mère|mother|Ma mère s'appelle Marie.|My mother's name is Marie.
le frère|brother|J'ai un frère.|I have a brother.
aujourd'hui|today|Aujourd'hui, il fait beau.|The weather is nice today.
demain|tomorrow|À demain !|See you tomorrow!
le matin|morning|Je travaille le matin.|I work in the morning.
la semaine|week|Je vais au cinéma cette semaine.|I'm going to the cinema this week.
rouge|red|J'ai une robe rouge.|I have a red dress.
la pomme|apple|Je mange une pomme.|I'm eating an apple.
le fromage|cheese|Les Français aiment le fromage.|French people like cheese.
la gare|train station|La gare est près d'ici.|The station is near here.
l'école|school|Les enfants vont à l'école.|The children go to school.
le lit|bed|Le chat dort sur le lit.|The cat is sleeping on the bed.
la fenêtre|window|Ouvre la fenêtre, s'il te plaît.|Open the window, please.
froid|cold|Il fait froid en hiver.|It's cold in winter.
chaud|hot|Le café est chaud.|The coffee is hot.
le travail|work / job|J'aime mon travail.|I like my job.
l'ami|friend|C'est mon ami Paul.|This is my friend Paul.
la ville|town / city|Lyon est une grande ville.|Lyon is a big city.
la rue|street|J'habite dans cette rue.|I live on this street.
acheter|to buy|J'achète du pain.|I'm buying bread.
dormir|to sleep|Le bébé dort.|The baby is sleeping.
lire|to read|Elle aime lire.|She likes reading.
écrire|to write|J'écris une lettre.|I'm writing a letter.
vouloir|to want|Je veux un thé.|I want a tea.
le soir|evening|Le soir, je regarde la télé.|In the evening, I watch TV.
la chambre|bedroom|Ma chambre est bleue.|My bedroom is blue.
les chaussures|shoes|Mes chaussures sont neuves.|My shoes are new.
la pluie|rain|J'aime le bruit de la pluie.|I like the sound of the rain.
cher|expensive|Ce restaurant est cher.|This restaurant is expensive.
facile|easy|Cet exercice est facile.|This exercise is easy.
heureux|happy|Je suis heureux aujourd'hui.|I'm happy today.
fatigué|tired|Je suis fatigué ce soir.|I'm tired this evening.
où|where|Où est la banque ?|Where is the bank?
pourquoi|why|Pourquoi tu ris ?|Why are you laughing?
beaucoup|a lot / very much|Merci beaucoup !|Thank you very much!
toujours|always|Il est toujours en retard.|He's always late.` },
{ id: "A2", name: "Elementary", words: `
le voyage|trip / journey|Nous préparons un voyage en Italie.|We're planning a trip to Italy.
le billet|ticket|J'ai acheté un billet de train.|I bought a train ticket.
la valise|suitcase|Ma valise est trop lourde.|My suitcase is too heavy.
réserver|to book|J'ai réservé une table pour ce soir.|I booked a table for tonight.
louer|to rent|Ils louent un appartement à Nice.|They're renting a flat in Nice.
le quartier|neighbourhood|Mon quartier est très calme.|My neighbourhood is very quiet.
le voisin|neighbour|Notre voisin est très gentil.|Our neighbour is very kind.
le loyer|rent|Le loyer est cher à Paris.|Rent is expensive in Paris.
le médecin|doctor|Je dois aller chez le médecin.|I need to go to the doctor.
malade|ill / sick|Je suis malade depuis hier.|I've been ill since yesterday.
avoir mal|to hurt / to ache|J'ai mal à la tête.|I have a headache.
le rendez-vous|appointment|J'ai un rendez-vous à dix heures.|I have an appointment at ten.
les vacances|holidays|Nous partons en vacances en août.|We're going on holiday in August.
le salaire|salary|Son salaire a augmenté.|His salary went up.
le collègue|colleague|Mes collègues sont sympas.|My colleagues are nice.
la réunion|meeting|La réunion commence à neuf heures.|The meeting starts at nine.
envoyer|to send|Je t'envoie un message.|I'm sending you a message.
oublier|to forget|J'ai oublié mes clés.|I forgot my keys.
se souvenir|to remember|Tu te souviens de moi ?|Do you remember me?
se réveiller|to wake up|Je me réveille à sept heures.|I wake up at seven.
se dépêcher|to hurry|Dépêche-toi, on est en retard !|Hurry up, we're late!
en retard|late|Le train est en retard.|The train is late.
attendre|to wait (for)|J'attends le bus.|I'm waiting for the bus.
chercher|to look for|Je cherche la gare.|I'm looking for the station.
trouver|to find|Je ne trouve pas mon téléphone.|I can't find my phone.
essayer|to try (on)|Je peux essayer cette veste ?|Can I try on this jacket?
la taille|size|Quelle est votre taille ?|What's your size?
le prix|price|Quel est le prix de ce livre ?|What's the price of this book?
bon marché|cheap|Ces chaussures sont bon marché.|These shoes are cheap.
le plat|dish|Ce plat est délicieux.|This dish is delicious.
l'addition|the bill|L'addition, s'il vous plaît.|The bill, please.
goûter|to taste|Tu veux goûter ma soupe ?|Do you want to taste my soup?
le loisir|hobby / leisure|Mon loisir préféré est la lecture.|My favourite hobby is reading.
le spectacle|show|Le spectacle était magnifique.|The show was wonderful.
la randonnée|hike|On fait une randonnée dimanche.|We're going on a hike on Sunday.
le paysage|scenery / landscape|Le paysage est superbe.|The scenery is superb.
la montagne|mountain(s)|Ils passent l'hiver à la montagne.|They spend the winter in the mountains.
d'habitude|usually|D'habitude, je prends le métro.|I usually take the metro.
parfois|sometimes|Parfois, je cuisine le soir.|Sometimes I cook in the evening.
souvent|often|Je vais souvent au cinéma.|I often go to the cinema.
jamais|never|Je ne bois jamais de café.|I never drink coffee.
déjà|already|J'ai déjà mangé.|I've already eaten.
encore|still / again|Il pleut encore.|It's still raining.
bientôt|soon|Le printemps arrive bientôt.|Spring is coming soon.
pendant|during|J'ai dormi pendant le film.|I slept during the film.
ensuite|then / next|Je me lave, ensuite je m'habille.|I wash, then I get dressed.
sympa|nice / friendly|Ton frère est très sympa.|Your brother is really nice.
inquiet|worried|Ma mère est inquiète.|My mother is worried.
fier|proud|Je suis fier de toi.|I'm proud of you.
le permis de conduire|driving licence|Elle a eu son permis de conduire.|She got her driving licence.` },
{ id: "B1", name: "Intermediate", words: `
l'avenir|future|Je pense souvent à l'avenir.|I often think about the future.
le but|goal / aim|Mon but est de parler couramment.|My goal is to speak fluently.
réussir|to succeed / to pass|Elle a réussi son examen.|She passed her exam.
échouer|to fail|Il a échoué à l'examen.|He failed the exam.
améliorer|to improve|Je veux améliorer mon français.|I want to improve my French.
le conseil|(piece of) advice|Tu peux me donner un conseil ?|Can you give me some advice?
se plaindre|to complain|Il se plaint toujours du bruit.|He always complains about the noise.
le bruit|noise|Il y a trop de bruit ici.|There's too much noise here.
partager|to share|On partage la pizza ?|Shall we share the pizza?
emprunter|to borrow|Je peux emprunter ton stylo ?|Can I borrow your pen?
prêter|to lend|Il m'a prêté sa voiture.|He lent me his car.
rembourser|to pay back / to refund|Je te rembourse demain.|I'll pay you back tomorrow.
le chômage|unemployment|Le chômage a baissé cette année.|Unemployment fell this year.
l'entretien|interview|J'ai un entretien d'embauche lundi.|I have a job interview on Monday.
le métier|profession / trade|Quel métier fais-tu ?|What do you do for a living?
l'entreprise|company|Elle travaille dans une grande entreprise.|She works for a big company.
gagner|to earn / to win|Il gagne bien sa vie.|He earns a good living.
dépenser|to spend (money)|J'ai trop dépensé ce mois-ci.|I spent too much this month.
économiser|to save (money)|J'économise pour un voyage.|I'm saving up for a trip.
l'environnement|environment|Il faut protéger l'environnement.|We must protect the environment.
les déchets|waste / rubbish|Triez vos déchets.|Sort your rubbish.
le réchauffement climatique|global warming|Le réchauffement climatique inquiète les jeunes.|Global warming worries young people.
la santé|health|Le sport est bon pour la santé.|Sport is good for your health.
se détendre|to relax|Je me détends en lisant.|I relax by reading.
le comportement|behaviour|Son comportement m'a surpris.|His behaviour surprised me.
la confiance|trust / confidence|J'ai confiance en toi.|I trust you.
la honte|shame|Il n'y a pas de honte à demander.|There's no shame in asking.
la colère|anger|Il était rouge de colère.|He was red with anger.
déçu|disappointed|Je suis déçu du résultat.|I'm disappointed with the result.
étonné|surprised|J'ai été étonné de le voir.|I was surprised to see him.
avoir l'air|to seem / to look|Tu as l'air fatigué.|You look tired.
se rendre compte|to realise|Je me suis rendu compte de mon erreur.|I realised my mistake.
s'habituer à|to get used to|Je m'habitue à la vie en France.|I'm getting used to life in France.
s'inquiéter|to worry|Ne t'inquiète pas !|Don't worry!
éviter|to avoid|J'évite le sucre.|I avoid sugar.
tenir|to hold|Tiens-moi la main.|Hold my hand.
suffire|to be enough|Ça suffit !|That's enough!
manquer|to miss / to lack|Tu me manques.|I miss you.
le quotidien|daily life|Le sport fait partie de mon quotidien.|Sport is part of my daily life.
la vitesse|speed|Il roule à grande vitesse.|He's driving at high speed.
l'embouteillage|traffic jam|On est coincés dans un embouteillage.|We're stuck in a traffic jam.
le lien|link / bond|Il y a un lien fort entre eux.|There's a strong bond between them.
le sondage|poll / survey|Selon un sondage, les Français lisent moins.|According to a poll, French people read less.
la loi|law|Cette loi a changé l'année dernière.|This law changed last year.
cependant|however|Il est riche ; cependant, il n'est pas heureux.|He's rich; however, he isn't happy.
pourtant|and yet|Il fait beau, pourtant il fait froid.|It's sunny, and yet it's cold.
grâce à|thanks to|J'ai réussi grâce à toi.|I succeeded thanks to you.
à cause de|because of|Le match est annulé à cause de la pluie.|The match is cancelled because of the rain.
d'ailleurs|besides / by the way|D'ailleurs, je l'ai vu hier.|By the way, I saw him yesterday.
au lieu de|instead of|Prends le vélo au lieu de la voiture.|Take the bike instead of the car.` },
{ id: "B2", name: "Upper intermediate", words: `
l'enjeu|stake / what's at stake|L'enjeu de cette élection est énorme.|What's at stake in this election is huge.
le défi|challenge|Apprendre une langue est un vrai défi.|Learning a language is a real challenge.
la croissance|growth|La croissance économique ralentit.|Economic growth is slowing down.
la grève|strike|Les cheminots sont en grève.|The railway workers are on strike.
le fardeau|burden|Les dettes sont un lourd fardeau.|Debts are a heavy burden.
la mise en œuvre|implementation|La mise en œuvre du projet sera longue.|Implementing the project will take a long time.
le bilan|assessment / overall results|Le bilan de l'année est positif.|The year's results are positive.
la démarche|process / approach|C'est une démarche administrative compliquée.|It's a complicated administrative process.
le décalage|gap / mismatch|Il y a un décalage entre ses paroles et ses actes.|There's a gap between his words and his actions.
l'atout|asset / advantage|Parler anglais est un atout.|Speaking English is an asset.
la méfiance|distrust|Il regarde l'inconnu avec méfiance.|He looks at the stranger with distrust.
le soutien|support|Merci pour ton soutien.|Thank you for your support.
le témoignage|testimony / account|Son témoignage a été décisif.|Her testimony was decisive.
la tendance|trend / tendency|C'est la nouvelle tendance.|It's the new trend.
le recul|hindsight / perspective|Avec le recul, j'ai fait le bon choix.|With hindsight, I made the right choice.
la lacune|gap (in knowledge)|J'ai des lacunes en grammaire.|I have gaps in my grammar.
l'essor|boom / rapid growth|Le télétravail connaît un essor important.|Remote working is booming.
le gaspillage|waste (wastefulness)|Il faut lutter contre le gaspillage alimentaire.|We must fight food waste.
le cadre|setting / framework|Le cadre de travail est agréable.|The working environment is pleasant.
la marge de manœuvre|room to manoeuvre|Nous avons peu de marge de manœuvre.|We have little room to manoeuvre.
susciter|to spark / to arouse|Ce film a suscité de vives réactions.|This film sparked strong reactions.
souligner|to stress / to underline|Le ministre a souligné l'urgence de la situation.|The minister stressed the urgency of the situation.
prôner|to advocate|Ce parti prône la décroissance.|This party advocates degrowth.
remettre en question|to call into question|Il remet tout en question.|He questions everything.
aborder|to tackle / to address|Nous allons aborder ce sujet demain.|We'll address this topic tomorrow.
envisager|to consider / to plan|J'envisage de changer de travail.|I'm considering changing jobs.
s'avérer|to turn out (to be)|La solution s'est avérée efficace.|The solution turned out to be effective.
mettre en place|to set up|L'école a mis en place un nouveau système.|The school set up a new system.
compter sur|to rely on|Tu peux compter sur moi.|You can count on me.
s'engager|to commit (oneself)|Elle s'engage pour le climat.|She's committed to the climate cause.
entraîner|to lead to / to cause|Cette décision a entraîné des grèves.|This decision led to strikes.
renoncer à|to give up|Il a renoncé à son projet.|He gave up his plan.
atteindre|to reach / to achieve|Nous avons atteint notre objectif.|We reached our goal.
épuisé|exhausted|Après le marathon, j'étais épuisé.|After the marathon, I was exhausted.
bouleversé|deeply shaken / upset|Elle était bouleversée par la nouvelle.|She was shaken by the news.
redoutable|formidable|C'est un adversaire redoutable.|He's a formidable opponent.
inéluctable|inevitable|Le changement semble inéluctable.|Change seems inevitable.
durable|sustainable / lasting|Il faut une solution durable.|We need a lasting solution.
flou|vague / blurry|Les règles restent floues.|The rules remain vague.
néanmoins|nevertheless|C'est difficile, néanmoins c'est possible.|It's difficult; nevertheless, it's possible.
en revanche|on the other hand|Il est timide ; en revanche, sa sœur est bavarde.|He's shy; on the other hand, his sister is chatty.
d'autant plus que|all the more so as|Je reste ici, d'autant plus qu'il pleut.|I'm staying here, all the more so as it's raining.
quant à|as for|Quant à moi, je préfère rester.|As for me, I'd rather stay.
dès lors|from then on|Dès lors, tout a changé.|From then on, everything changed.
à l'égard de|towards / regarding|Il est sévère à l'égard de ses élèves.|He's strict towards his pupils.
il s'agit de|it's about / it's a matter of|Il s'agit de ta santé.|It's about your health.
avoir beau|to (do something) in vain|J'ai beau essayer, je n'y arrive pas.|However hard I try, I can't do it.
faire la queue|to queue|On a fait la queue pendant une heure.|We queued for an hour.
débarrasser|to clear (away)|Je dois débarrasser la table.|I need to clear the table.
le malentendu|misunderstanding|C'était un simple malentendu.|It was just a misunderstanding.` },
].map((l) => ({ ...l, words: l.words.trim().split("\n").map((line) => {
  const [fr, en, exFr, exEn] = line.split("|");
  return { fr, en, exFr, exEn };
}) }));
