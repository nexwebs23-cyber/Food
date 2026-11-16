import json, os, hashlib, subprocess, datetime

today_str = datetime.date.today().isoformat()

NEW_15_RECIPES = [
    {
        "id": "lahori-mutton-paya",
        "country": "Pakistan",
        "name": "Lahori Mutton Paya",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "nonveg",
        "time": 180,
        "diff": "Hard",
        "servings": "6 people",
        "alt": "Authentic Lahori Mutton Paya trotters slow cooked in sticky spiced soup with ZaikaWorlds logo",
        "desc": "Traditional slow-simmered trotters cooked overnight with aromatic whole spices, creating a rich, gelatinous, sticky spiced broth.",
        "intro": "Lahori Paya is the quintessential royal breakfast of old Lahore. Tender goat trotters are simmered patiently for hours with onion, garlic, whole cardamom, and cloves, releasing natural collagen into a velvety soup that clings delightfully to hot tandoori naan.",
        "ing": ["Goat trotters (paya) cleaned 6", "Sliced onions 3 large", "Ginger garlic paste fresh 3 tbsp", "Turmeric powder 1 tsp", "Red chili powder 1.5 tbsp", "Coriander powder 2 tbsp", "Whole garam masala 2 tbsp", "Desi ghee 0.5 cup", "Salt 2 tsp", "Julienned ginger, chopped fresh coriander, and lemon wedges for garnish"],
        "steps": [
            "Wash trotters thoroughly with warm water and wheat flour to clean completely.",
            "In a large stockpot, brown sliced onions in desi ghee until light golden.",
            "Add ginger-garlic paste and trotters; sear on medium heat for 10 minutes.",
            "Add turmeric, red chili, coriander powder, whole spices, and salt; stir well.",
            "Pour in 10 cups of water, bring to a rapid boil, cover tightly, and simmer on lowest heat for 3 to 4 hours until the meat is falling off the bone.",
            "Garnish with julienned ginger, fresh cilantro, and lemon juice before serving piping hot."
        ],
        "tip": "Do not rush cooking paya; the signature gelatinous stickiness comes exclusively from low-and-slow simmering of natural collagen.",
        "nutrition": {"calories": 420, "proteinContent": 38.0, "fatContent": 28.0, "carbohydrateContent": 4.5},
        "lang": {
            "ru": {"name": "Lahori Mutton Paya", "catLabel": "Desi Dishes", "diff": "Mushkil", "servings": "6 log", "desc": "Asal Lahori makhsoos mutton paya shorba.", "alt": "Lahori Mutton Paya"},
            "hi": {"name": "लाहौरी मटन पाया", "catLabel": "देसी व्यंजन", "diff": "कठिन", "servings": "6 लोग", "desc": "पारंपरिक धीमी आंच पर पके रसीले मटन पाए।", "alt": "लाहौरी मटन पाया"}
        }
    },
    {
        "id": "chicken-dopiaza",
        "country": "Pakistan",
        "name": "Mughlai Chicken Dopiaza",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "nonveg",
        "time": 45,
        "diff": "Medium",
        "servings": "4 people",
        "alt": "Rich onion-loaded Mughlai Chicken Dopiaza curry with ZaikaWorlds logo",
        "desc": "Classic Mughlai curry prepared with two stages of onions — sweet caramelized onion paste and crisp sautéed onion petal garnishes.",
        "intro": "Dopiaza literally translates to 'two onions'. In this aromatic Mughlai preparation, one batch of onions melts into the spiced tomato gravy while another batch is fried into sweet, crunchy petals stirred in right at the end.",
        "ing": ["Chicken bone-in pieces 750g", "Finely sliced onions for gravy 2", "Large onion cut into squared petals 2", "Yogurt whisked 0.5 cup", "Tomato puree 0.5 cup", "Ginger garlic paste 1.5 tbsp", "Kashmiri red chili powder 1 tbsp", "Garam masala 1 tsp", "Cumin seeds 1 tsp", "Oil or ghee 4 tbsp", "Salt 1.25 tsp"],
        "steps": [
            "Heat 2 tbsp oil in a pan, toss the onion square petals for 2 minutes until translucent with charred edges; remove and keep aside.",
            "In same pan with remaining oil, add cumin seeds and sliced onions; fry until rich golden brown.",
            "Add ginger-garlic paste and chicken; saute for 8 minutes until chicken seals and turns pale.",
            "Lower heat, whisk in yogurt, tomato puree, red chili, and salt; cover and cook for 20 minutes until chicken is tender.",
            "Fold in the reserved crunchy onion petals and garam masala; simmer on low heat for 5 minutes.",
            "Serve hot garnished with chopped coriander."
        ],
        "tip": "Never overcook the second batch of onion petals; they must retain their sweet crunch to contrast with the tender chicken.",
        "nutrition": {"calories": 440, "proteinContent": 36.0, "fatContent": 24.0, "carbohydrateContent": 18.0},
        "lang": {
            "ru": {"name": "Mughlai Chicken Dopiaza", "catLabel": "Desi Dishes", "diff": "Darmiyana", "servings": "4 log", "desc": "Pyaaz ke do andaaz mein paka hua shahi chicken dopiaza.", "alt": "Chicken Dopiaza"},
            "hi": {"name": "चिकन दो प्याज़ा", "catLabel": "देसी व्यंजन", "diff": "मध्यम", "servings": "4 लोग", "desc": "प्याज की दोहरी विधि से बनी स्वादिष्ट चिकन करी।", "alt": "चिकन दो प्याज़ा"}
        }
    },
    {
        "id": "malai-kofta-curry",
        "country": "India",
        "name": "Shahi Malai Kofta Curry",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "veg",
        "time": 50,
        "diff": "Medium",
        "servings": "4 people",
        "alt": "Melt-in-mouth cottage cheese and potato dumplings in cashew tomato cream gravy with ZaikaWorlds logo",
        "desc": "Crispy golden paneer and potato dumplings filled with nuts, served swimming in a velvet-smooth cashew and tomato cream gravy.",
        "intro": "Malai Kofta is the ultimate vegetarian centerpiece for celebratory feasts. Pillowy soft dumplings made from grated paneer and potato are stuffed with cashews and raisins, fried golden, and presented in an ivory-orange spiced cream sauce.",
        "ing": ["Grated fresh paneer 200g", "Boiled mashed potatoes 2 medium", "Cornstarch 2.5 tbsp", "Chopped cashews and raisins for stuffing 2 tbsp", "Tomato puree 1.5 cups", "Cashew nut paste 0.25 cup", "Fresh dairy cream 0.25 cup", "Ginger garlic paste 1 tbsp", "Kasuri methi 1 tbsp", "Cardamom powder 0.5 tsp", "Salt and red chili 1 tsp each", "Oil for frying"],
        "steps": [
            "Combine grated paneer, mashed potatoes, cornstarch, and pinch of salt; knead into a crack-free dough.",
            "Shape into balls, stuff each with cashew bits and raisins, and roll into smooth round koftas.",
            "Deep fry koftas in medium-hot oil until light golden and crisp; drain on paper towels.",
            "For gravy: heat 2 tbsp butter, fry ginger-garlic paste, add tomato puree, and cook until butter leaves the sides.",
            "Stir in cashew paste, spices, and half cup water; simmer for 8 minutes into a silky luxurious sauce.",
            "Finish sauce with fresh cream and crushed kasuri methi.",
            "Arrange koftas in a serving dish and ladle hot gravy on top immediately before eating."
        ],
        "tip": "Never boil koftas directly inside the simmering gravy or they will dissolve; always pour hot gravy over the koftas just before serving.",
        "nutrition": {"calories": 480, "proteinContent": 14.0, "fatContent": 34.0, "carbohydrateContent": 32.0},
        "lang": {
            "ru": {"name": "Shahi Malai Kofta Curry", "catLabel": "Desi Dishes", "diff": "Darmiyana", "servings": "4 log", "desc": "Naram paneer kofta makhani kaju gravy mein.", "alt": "Malai Kofta"},
            "hi": {"name": "शाही मलाई कोफ्ता", "catLabel": "देसी व्यंजन", "diff": "मध्यम", "servings": "4 लोग", "desc": "काजू और मलाई की मखमली ग्रेवी में पनीर कोफ्ते।", "alt": "शाही मलाई कोफ्ता"}
        }
    },
    {
        "id": "peshawari-dum-pukht",
        "country": "Pakistan",
        "name": "Peshawari Mutton Dum Pukht",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "nonveg",
        "time": 120,
        "diff": "Medium",
        "servings": "5 people",
        "alt": "Slow clay-sealed steam cooked mutton and potatoes with ZaikaWorlds logo",
        "desc": "Khyber tribal delicacy of meat, baby potatoes, whole garlic heads, and animal fat slow-cooked in a dough-sealed pot with pure steam.",
        "intro": "Dum Pukht is an ancient cooking technique of Persian heritage perfected in Khyber Pakhtunkhwa. Meat, whole baby potatoes, and unpeeled garlic heads are layered with tail fat, hermetically sealed with dough, and left to steam undisturbed on coals.",
        "ing": ["Mutton pieces with bone and natural fat 1kg", "Small peeled baby potatoes 6", "Whole garlic heads unpeeled 2", "Fresh whole tomatoes 3", "Coarse sea salt 1.5 tsp", "Whole black peppercorns 1 tbsp", "Animal tail fat or desi ghee 4 tbsp", "Wheat dough for sealing pot"],
        "steps": [
            "Layer animal fat or desi ghee at the bottom of a heavy pot.",
            "Arrange mutton pieces neatly over the fat; season evenly with coarse salt and black peppercorns.",
            "Tuck whole baby potatoes, unpeeled garlic heads, and whole tomatoes between and over the meat.",
            "Roll wheat dough into a thick rope and press firmly along the pot rim; press lid down tightly to seal.",
            "Place pot over high heat for 10 minutes to generate internal steam, then reduce flame to lowest setting.",
            "Cook undisturbed for 2 hours on gentle dum.",
            "Cut open the dough seal at the dining table; serve the falling-apart tender meat and potato confit with hot naan."
        ],
        "tip": "Do not add even a single drop of water; the mutton and tomatoes will render plenty of delicious natural broth during the sealed steam braise.",
        "nutrition": {"calories": 520, "proteinContent": 46.0, "fatContent": 35.0, "carbohydrateContent": 14.0},
        "lang": {
            "ru": {"name": "Peshawari Mutton Dum Pukht", "catLabel": "Desi Dishes", "diff": "Darmiyana", "servings": "5 log", "desc": "Bhaap mein aatay se band handi mein paka hua mutton dum pukht.", "alt": "Peshawari Dum Pukht"},
            "hi": {"name": "पेशावरी मटन दम पुख्त", "catLabel": "देसी व्यंजन", "diff": "मध्यम", "servings": "5 लोग", "desc": "आटे से सील मिट्टी के बर्तन में भाप से पका मटन।", "alt": "पेशावरी दम पुख्त"}
        }
    },
    {
        "id": "chicken-jalfrezi",
        "country": "Pakistan",
        "name": "Restaurant Style Chicken Jalfrezi",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "nonveg",
        "time": 35,
        "diff": "Easy",
        "servings": "4 people",
        "alt": "Tangy spicy Chicken Jalfrezi stir-fry with bell peppers, onions and scrambled egg with ZaikaWorlds logo",
        "desc": "Vibrant and tangy stir-fried boneless chicken with crisp bell peppers, onions, tomatoes, and egg in a sweet-spicy tomato sauce.",
        "intro": "Originating from colonial Calcutta and celebrated across Pakistani restaurants, Chicken Jalfrezi is a fast, high-heat stir fry. Juicy strips of boneless chicken are tossed with crunchy bell peppers, onions, and cumin in a tangy, thick tomato sauce.",
        "ing": ["Boneless chicken breast cut into strips 500g", "Green and red bell peppers cut into squares 2", "Onion cut into squares 1 large", "Tomato ketchup 3 tbsp", "Soy sauce 1 tbsp", "Chili garlic sauce 1.5 tbsp", "Ginger garlic paste 1 tbsp", "Cumin powder 1 tsp", "Black pepper freshly crushed 1 tsp", "Oil 3 tbsp", "Fried egg strips or boiled egg quarters for garnish"],
        "steps": [
            "Heat 2 tbsp oil in a wok; fry ginger-garlic paste and boneless chicken strips on high heat for 6 minutes until cooked through.",
            "Add tomato ketchup, soy sauce, chili garlic sauce, cumin powder, and black pepper; toss rapidly on high heat.",
            "Add squared bell peppers, onions, and fresh tomatoes; stir-fry vigorously for 3 minutes keeping vegetables crisp and colorful.",
            "Top with scrambled or sliced egg strips and chopped green chilies.",
            "Serve hot with steamed basmati rice or hot paratha."
        ],
        "tip": "Stir-fry on high flame throughout; the vegetables must remain crisp and vibrant, not soggy or boiled.",
        "nutrition": {"calories": 360, "proteinContent": 34.0, "fatContent": 16.0, "carbohydrateContent": 20.0},
        "lang": {
            "ru": {"name": "Restaurant Style Chicken Jalfrezi", "catLabel": "Desi Dishes", "diff": "Aasan", "servings": "4 log", "desc": "Shimla mirch aur boneless chicken ka chatpata jalfrezi salan.", "alt": "Chicken Jalfrezi"},
            "hi": {"name": "चिकन जलफ्रेजी", "catLabel": "देसी व्यंजन", "diff": "सरल", "servings": "4 लोग", "desc": "शिमला मिर्च और टमाटर के साथ बना मसालेदार चिकन।", "alt": "चिकन जलफ्रेजी"}
        }
    },
    {
        "id": "paneer-butter-masala",
        "country": "India",
        "name": "Restaurant Paneer Butter Masala",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "veg",
        "time": 40,
        "diff": "Easy",
        "servings": "4 people",
        "alt": "Soft paneer cubes in creamy orange-red makhani butter gravy with ZaikaWorlds logo",
        "desc": "Ultra-popular Indian vegetarian curry of soft paneer cubes simmered in a mildly sweet, rich tomato, butter, and cashew gravy.",
        "intro": "Paneer Butter Masala (also known as Paneer Makhani) is universally loved for its rich, velvety sauce. Soft cottage cheese cubes bathe in a sun-ripened tomato-butter gravy scented with green cardamom, kasuri methi, and cream.",
        "ing": ["Fresh paneer cubes 300g", "Ripe red tomatoes chopped 4", "Cashews soaked 15", "Butter (makhan) 3 tbsp", "Ginger garlic paste 1 tbsp", "Heavy dairy cream 3 tbsp", "Kashmiri red chili powder 1.5 tbsp", "Kasuri methi crushed 1 tbsp", "Garam masala 0.5 tsp", "Sugar 1 tsp", "Salt 1 tsp"],
        "steps": [
            "Boil chopped tomatoes and soaked cashews in 1 cup water for 10 minutes until soft; blend into a smooth velvety puree and strain.",
            "Melt 2 tbsp butter in a kadai; add ginger-garlic paste and Kashmiri chili powder; saute for 30 seconds.",
            "Pour in strained tomato-cashew puree; simmer on medium flame for 12 minutes until butter begins to surface.",
            "Add sugar, salt, garam masala, and fresh cream; mix thoroughly.",
            "Gently slide in fresh paneer cubes and simmer for 3 minutes (do not overcook paneer).",
            "Crush kasuri methi between palms and sprinkle on top with a dollop of fresh butter before serving."
        ],
        "tip": "Soak paneer cubes in warm salted water for 10 minutes before adding to the gravy to keep them exceptionally soft and spongy.",
        "nutrition": {"calories": 420, "proteinContent": 16.0, "fatContent": 32.0, "carbohydrateContent": 18.0},
        "lang": {
            "ru": {"name": "Restaurant Paneer Butter Masala", "catLabel": "Desi Dishes", "diff": "Aasan", "servings": "4 log", "desc": "Makhani gravy mein naram paneer butter masala.", "alt": "Paneer Butter Masala"},
            "hi": {"name": "पनीर बटर मसाला", "catLabel": "देसी व्यंजन", "diff": "सरल", "servings": "4 लोग", "desc": "मखमली टमाटर और मक्खन की ग्रेवी में बना पनीर।", "alt": "पनीर बटर मसाला"}
        }
    },
    {
        "id": "lahori-chargha",
        "country": "Pakistan",
        "name": "Crispy Lahori Chargha",
        "cat": "bbq",
        "catLabel": "BBQ",
        "veg": "nonveg",
        "time": 60,
        "diff": "Medium",
        "servings": "4 people",
        "alt": "Whole deep-cut marinated chicken steamed and fried golden crisp with ZaikaWorlds logo",
        "desc": "Iconic Lahori whole chicken deeply scored, marinated in spicy yogurt and lemon, steamed until tender, and deep-fried to a shatteringly crisp skin.",
        "intro": "Lahori Chargha is one of food street Lahore's absolute greatest innovations. A whole skinless chicken is scored deeply, soaked in an intense marinade of yogurt, chaat masala, lemon, and spices, steamed to lock in juiciness, and finally flash-fried until crackling crisp.",
        "ing": ["Whole chicken skinless 1.2kg", "Hung thick yogurt 0.5 cup", "Fresh lemon juice 4 tbsp", "Ginger garlic paste 2 tbsp", "Chaat masala 2 tbsp", "Roasted cumin powder 1.5 tbsp", "Red chili flakes and powder 1.5 tbsp", "Egg beaten 1", "Cornstarch 2 tbsp", "Oil for deep frying"],
        "steps": [
            "Make deep vertical cuts along chicken breasts, thighs, and legs.",
            "Whisk yogurt with lemon juice, ginger-garlic, chaat masala, cumin, chili, beaten egg, cornstarch, and salt into a thick marinade.",
            "Rub marinade thoroughly into all cuts and inside cavity; marinate for at least 3 hours.",
            "Place chicken on a steamer rack inside a large pot, cover tightly, and steam for 30 minutes until fully cooked and tender.",
            "Allow steamed chicken to cool completely so moisture evaporates from the surface.",
            "Lower chicken into a deep wok of hot oil; deep fry for 6 to 8 minutes turning carefully until blistering golden and crispy.",
            "Dust generously with extra chaat masala and serve with mint chutney and hot naan."
        ],
        "tip": "Cooling the steamed chicken before frying is the critical halwai secret; it ensures the outer crust turns ultra-crispy without soaking up excess oil.",
        "nutrition": {"calories": 530, "proteinContent": 52.0, "fatContent": 32.0, "carbohydrateContent": 9.0},
        "lang": {
            "ru": {"name": "Crispy Lahori Chargha", "catLabel": "BBQ", "diff": "Darmiyana", "servings": "4 log", "desc": "Bhaap aur tel mein paka hua crispy Lahori chargha.", "alt": "Lahori Chargha"},
            "hi": {"name": "लाहौरी चरगा", "catLabel": "बारबेक्यू", "diff": "मध्यम", "servings": "4 लोग", "desc": "भाप और तलकर बना कुरकुरा साबुत चिकन।", "alt": "लाहौरी चरगा"}
        }
    },
    {
        "id": "hyderabadi-khatti-dal",
        "country": "India",
        "name": "Hyderabadi Khatti Dal",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "veg",
        "time": 35,
        "diff": "Easy",
        "servings": "4 people",
        "alt": "Sour tangy Hyderabadi Khatti Dal with tamarind and curry leaf tadka with ZaikaWorlds logo",
        "desc": "Zesty, comforting yellow lentils simmered with juicy tomatoes, tangy tamarind extract, finished with a smoking garlic and curry leaf tadka.",
        "intro": "No Hyderabadi meal is complete without Khatti Dal. Yellow pigeon peas (toor dal) are cooked tender with ripe tomatoes, seasoned with tart tamarind pulp, and tempered with crackling mustard seeds, cumin, garlic, and fragrant curry leaves.",
        "ing": ["Toor dal (pigeon pea lentils) 1 cup", "Ripe tomatoes chopped 3", "Thick tamarind extract 3 tbsp", "Ginger garlic paste 1 tbsp", "Turmeric powder 0.75 tsp", "Green chilies slit 4", "Fresh curry leaves 12", "Cumin and mustard seeds 1 tsp each", "Dried red button chilies 4", "Desi ghee 3 tbsp", "Salt 1.25 tsp"],
        "steps": [
            "Pressure cook toor dal with chopped tomatoes, turmeric, green chilies, and 3 cups water for 4 whistles until soft; whisk smoothly.",
            "Stir in thick tamarind extract, ginger-garlic paste, and salt; simmer on medium flame for 10 minutes until raw tamarind aroma disappears.",
            "In a small pan, heat desi ghee for tadka; add mustard seeds, cumin seeds, dried red chilies, garlic slivers, and curry leaves.",
            "When garlic turns light golden and curry leaves crackle, pour sizzling tadka directly into the simmering dal.",
            "Cover immediately with lid to trap the smoky aromatics for 5 minutes before serving with steamed rice."
        ],
        "tip": "Always allow the dal and tamarind to boil together for at least 8 to 10 minutes before tempering; this mellows the sharpness of the tamarind.",
        "nutrition": {"calories": 220, "proteinContent": 11.0, "fatContent": 7.0, "carbohydrateContent": 29.0},
        "lang": {
            "ru": {"name": "Hyderabadi Khatti Dal", "catLabel": "Desi Dishes", "diff": "Aasan", "servings": "4 log", "desc": "Imli aur tamatar ke tadke wali Hyderabadi khatti daal.", "alt": "Hyderabadi Khatti Dal"},
            "hi": {"name": "हैदराबादी खट्टी दाल", "catLabel": "देसी व्यंजन", "diff": "सरल", "servings": "4 लोग", "desc": "इमली और टमाटर के तड़के वाली खट्टी दाल।", "alt": "हैदराबादी खट्टी दाल"}
        }
    },
    {
        "id": "beef-kofta-curry",
        "country": "Pakistan",
        "name": "Traditional Beef Kofta Curry",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "nonveg",
        "time": 55,
        "diff": "Medium",
        "servings": "5 people",
        "alt": "Tender spiced beef meatballs simmered in silky yogurt onion gravy with ZaikaWorlds logo",
        "desc": "Spiced ground beef meatballs hand-rolled and gently poached in a royal browned onion, yogurt, and cardamom gravy.",
        "intro": "Traditional Pakistani Kofta Curry is an enduring culinary classic. Finely minced beef is pounded with roasted gram flour, poppy seeds, and whole spices, shaped into round meatballs, and gently simmered in a velvety golden gravy without breaking.",
        "ing": ["Finely minced beef (keema) 750g", "Roasted chickpea flour (bhuna besan) 3 tbsp", "Poppy seeds (khashkhash) ground 1 tbsp", "Yogurt whisked 1 cup", "Fried golden onions crushed 1 cup", "Ginger garlic paste 2 tbsp", "Coriander powder 1.5 tbsp", "Red chili powder 1 tbsp", "Garam masala 1 tsp", "Desi ghee or oil 0.5 cup", "Salt 1.5 tsp"],
        "steps": [
            "In a food processor, blend beef mince with roasted besan, ground poppy seeds, half the ginger-garlic paste, green chilies, and salt into a smooth pliable dough.",
            "Shape into 15 to 18 smooth, compact, crack-free meatballs.",
            "In a wide pot, heat ghee, add remaining ginger-garlic paste, coriander powder, red chili, and whisked yogurt; saute for 5 minutes.",
            "Stir in crushed fried onions and half cup water; bring to a gentle boil.",
            "Gently place meatballs side by side into the bubbling gravy in a single layer (do not stir with a spoon).",
            "Hold the pot with kitchen towels and gently swirl in a circular motion to coat meatballs in gravy; cover and cook on low heat for 25 minutes.",
            "Finish with garam masala and fresh coriander leaves."
        ],
        "tip": "Never use a spoon to stir koftas in the first 15 minutes of cooking; only swirl the pot by its handles to prevent the delicate meatballs from breaking.",
        "nutrition": {"calories": 490, "proteinContent": 42.0, "fatContent": 32.0, "carbohydrateContent": 8.0},
        "lang": {
            "ru": {"name": "Traditional Beef Kofta Curry", "catLabel": "Desi Dishes", "diff": "Darmiyana", "servings": "5 log", "desc": "Naram gosht ke kofte dahi pyaaz ke shorbe mein.", "alt": "Beef Kofta Curry"},
            "hi": {"name": "बीफ कोफ्ता करी", "catLabel": "देसी व्यंजन", "diff": "मध्यम", "servings": "5 लोग", "desc": "दही और प्याज की ग्रेवी में बने मुलायम बीफ कोफ्ते।", "alt": "बीफ कोफ्ता करी"}
        }
    },
    {
        "id": "zafrani-kheer",
        "country": "Pakistan",
        "name": "Shahi Zafrani Kheer",
        "cat": "desserts",
        "catLabel": "Desserts",
        "veg": "veg",
        "time": 60,
        "diff": "Easy",
        "servings": "6 people",
        "alt": "Thick creamy saffron rice pudding served in earthenware bowls with ZaikaWorlds logo",
        "desc": "Luxurious slow-cooked rice pudding enriched with full-fat milk, saffron strands, crushed cardamoms, and slivered dry fruit in clay cups.",
        "intro": "Zafrani Kheer is the undisputed queen of Subcontinental desserts. Fragrant basmati rice is crushed and cooked slowly in bubbling full-cream milk until it reduces into a creamy, golden pudding infused with Kashmiri saffron and rose water.",
        "ing": ["Basmati rice soaked and coarsely crushed 0.5 cup", "Full cream buffalo milk 1.5 liters", "Sugar 0.75 cup", "Green cardamom powder 1 tsp", "Pure saffron strands soaked in warm milk 1 generous pinch", "Condensed milk or khoya 0.25 cup", "Slivered pistachios and almonds 3 tbsp", "Kewra water 1 tsp", "Silver vark for garnish"],
        "steps": [
            "Bring milk to a boil in a heavy-bottomed pot; add coarsely crushed soaked rice.",
            "Cook on low heat, stirring frequently with a wooden spoon for 40 minutes until rice disintegrates and milk thickens to rabri consistency.",
            "Add sugar, saffron milk, and cardamom powder; simmer for another 10 minutes until sugar dissolves completely.",
            "Stir in condensed milk or khoya and slivered nuts; cook for 3 minutes.",
            "Turn off heat, add kewra water, and pour into traditional unglazed clay bowls (matkas).",
            "Chill thoroughly in the refrigerator for 4 hours; top with silver leaf and pistachios before serving."
        ],
        "tip": "Serving kheer in unglazed earthenware bowls absorbs excess moisture, leaving the pudding exceptionally thick and imparting an earthy fragrance.",
        "nutrition": {"calories": 310, "proteinContent": 8.0, "fatContent": 12.0, "carbohydrateContent": 44.0},
        "lang": {
            "ru": {"name": "Shahi Zafrani Kheer", "catLabel": "Desserts", "diff": "Aasan", "servings": "6 log", "desc": "Zafran aur doodh ki garhi shahi chawal kheer.", "alt": "Zafrani Kheer"},
            "hi": {"name": "शाही जाफरानी खीर", "catLabel": "मिठाई", "diff": "सरल", "servings": "6 लोग", "desc": "केसर और सूखे मेवों से बनी गाढ़ी चावल की खीर।", "alt": "शाही जाफरानी खीर"}
        }
    },
    {
        "id": "chicken-reshmi-handi",
        "country": "Pakistan",
        "name": "Silky Chicken Reshmi Handi",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "nonveg",
        "time": 40,
        "diff": "Easy",
        "servings": "4 people",
        "alt": "Silky smooth boneless chicken cooked in clay pot with cream and cashew gravy with ZaikaWorlds logo",
        "desc": "Tender boneless chicken cubes simmered in a silken, creamy gravy of butter, yogurt, cashew paste, and aromatic green chilies.",
        "intro": "Reshmi Handi is famous for its silk-like smooth texture. Prepared in an earthenware pot, succulent boneless chicken melts into a luscious gravy made from white butter, cashew cream, and fragrant kasuri methi.",
        "ing": ["Boneless chicken cubes 700g", "Whisked yogurt 0.75 cup", "Cashew nut paste 3 tbsp", "Fresh dairy cream 0.5 cup", "Butter 2 tbsp", "Ginger garlic paste 1.5 tbsp", "White pepper powder 1 tsp", "Black pepper powder 0.5 tsp", "Crushed green chilies 1.5 tbsp", "Kasuri methi 1 tbsp", "Salt 1.25 tsp"],
        "steps": [
            "Melt butter in a clay handi; saute ginger-garlic paste and green chili paste for 1 minute.",
            "Add boneless chicken cubes and fry on medium-high heat for 6 minutes until chicken turns white.",
            "Lower heat, add whisked yogurt, cashew paste, white pepper, and salt; stir constantly to combine.",
            "Cover handi with lid and cook on low heat for 15 minutes until chicken is tender and sauce is creamy.",
            "Pour in fresh dairy cream and crushed kasuri methi; simmer gently for 3 minutes without boiling.",
            "Serve piping hot in the clay pot with garlic naan."
        ],
        "tip": "Avoid using red chili powder or turmeric in Reshmi Handi; white pepper and green chilies keep the signature ivory-pearl color intact.",
        "nutrition": {"calories": 460, "proteinContent": 39.0, "fatContent": 31.0, "carbohydrateContent": 8.0},
        "lang": {
            "ru": {"name": "Silky Chicken Reshmi Handi", "catLabel": "Desi Dishes", "diff": "Aasan", "servings": "4 log", "desc": "Reshmi malai aur kaju paste mein bani mitti ki handi chicken.", "alt": "Chicken Reshmi Handi"},
            "hi": {"name": "चिकन रेशमी हांडी", "catLabel": "देसी व्यंजन", "diff": "सरल", "servings": "4 लोग", "desc": "मलाई और काजू की मखमली ग्रेवी में बनी चिकन हांडी।", "alt": "चिकन रेशमी हांडी"}
        }
    },
    {
        "id": "lahori-fried-chanay",
        "country": "Pakistan",
        "name": "Lahori Murgh Chanay",
        "cat": "breakfast",
        "catLabel": "Breakfast",
        "veg": "nonveg",
        "time": 50,
        "diff": "Medium",
        "servings": "5 people",
        "alt": "Soft spiced chickpeas and chicken stewed with black pepper gravy with ZaikaWorlds logo",
        "desc": "Famous Lahore street-food breakfast of meltingly soft chickpeas and chicken cooked in a heavily spiced black pepper, cumin, and lentil gravy.",
        "intro": "Murgh Chanay is the legendary heartbeat of Lahore's Sunday breakfast culture. Chickpeas cooked with baking soda to supreme tenderness are braised with bone-in chicken in an aromatic black-pepper gravy thickened naturally with masoor dal paste.",
        "ing": ["White chickpeas (kabuli chana) soaked overnight 2 cups", "Chicken bone-in pieces 600g", "Red masoor dal cooked and mashed 0.5 cup", "Baking soda 0.5 tsp", "Ginger garlic paste 2 tbsp", "Coarsely crushed black pepper 1.5 tbsp", "Roasted cumin powder 1 tbsp", "Garam masala 1 tsp", "Desi ghee or oil 0.5 cup", "Salt 1.5 tsp"],
        "steps": [
            "Boil soaked chickpeas with baking soda and salt until completely soft and creamy; drain and reserve 1 cup of cooking broth.",
            "Heat ghee in a pot, add ginger-garlic paste and chicken; saute for 8 minutes until golden.",
            "Add crushed black pepper, cumin powder, and garam masala; saute with 2 tbsp water for 2 minutes.",
            "Add mashed masoor dal paste, boiled chickpeas, and reserved chickpea broth; stir well to combine.",
            "Bring to boil, cover, and simmer on lowest heat (dum) for 20 minutes until ghee surfaces and the gravy is thick and glossy.",
            "Serve hot with crispy puri, rogheni naan, and sliced raw onions."
        ],
        "tip": "Mashing half a cup of boiled red lentils into the gravy is the secret technique Lahori halwais use to give the sauce its rich, clinging body.",
        "nutrition": {"calories": 480, "proteinContent": 36.0, "fatContent": 20.0, "carbohydrateContent": 42.0},
        "lang": {
            "ru": {"name": "Lahori Murgh Chanay", "catLabel": "Breakfast", "diff": "Darmiyana", "servings": "5 log", "desc": "Lahori subah ke nashte wale chicken chholay chanay.", "alt": "Murgh Chanay"},
            "hi": {"name": "लाहौरी मुर्ग चने", "catLabel": "नाश्ता", "diff": "मध्यम", "servings": "5 लोग", "desc": "काली मिर्च और मसालों में पके चिकन और काबुली चने।", "alt": "लाहौरी मुर्ग चने"}
        }
    },
    {
        "id": "afghani-chicken-boti",
        "country": "Pakistan",
        "name": "Peshawari Afghani Chicken Boti",
        "cat": "bbq",
        "catLabel": "BBQ",
        "veg": "nonveg",
        "time": 35,
        "diff": "Easy",
        "servings": "4 people",
        "alt": "Mildly spiced creamy white charcoal grilled chicken skewers with ZaikaWorlds logo",
        "desc": "Tender boneless chicken skewers marinated in cream, hung curd, garlic, cashew paste, and cracked black pepper, charcoal grilled to perfection.",
        "intro": "Afghani Boti is celebrated for its mild, rich, and aromatic flavor profile. Free of fiery red spices, succulent chicken thigh pieces are steeped in a marinade of malai, yogurt, cashews, and aromatic cardamom before being charred over live charcoal.",
        "ing": ["Boneless chicken thigh cubes 750g", "Thick hung curd 0.5 cup", "Fresh heavy cream 0.25 cup", "Cashew nut paste 2 tbsp", "Ginger garlic paste 1.5 tbsp", "Lemon juice 2 tbsp", "Cardamom powder 0.5 tsp", "Cracked black pepper 1 tbsp", "Melted butter for basting 3 tbsp", "Salt 1.25 tsp"],
        "steps": [
            "Whisk hung curd, fresh cream, cashew paste, ginger-garlic, lemon juice, cardamom, black pepper, and salt into a thick marinade.",
            "Toss chicken cubes in the marinade; cover and refrigerate for at least 2 hours.",
            "Thread chicken cubes onto metal or soaked wooden skewers leaving a little space between pieces.",
            "Grill over live glowing coals or in a preheated oven at 220°C (425°F) for 15 to 18 minutes, turning skewers halfway.",
            "Generously baste with melted butter and grill for final 2 minutes until lightly charred and smoky.",
            "Serve immediately with mint raita and thin Afghani naan."
        ],
        "tip": "Use boneless chicken thighs instead of breast meat; thighs contain more intramuscular fat and stay remarkably juicy when exposed to high grilling heat.",
        "nutrition": {"calories": 440, "proteinContent": 41.0, "fatContent": 27.0, "carbohydrateContent": 6.5},
        "lang": {
            "ru": {"name": "Peshawari Afghani Chicken Boti", "catLabel": "BBQ", "diff": "Aasan", "servings": "4 log", "desc": "Kaju aur malai ke amezay mein bani Afghani chicken boti.", "alt": "Afghani Chicken Boti"},
            "hi": {"name": "अफगानी चिकन बोटी", "catLabel": "बारबेक्यू", "diff": "सरल", "servings": "4 लोग", "desc": "काजू और मलाई में मैरीनेट की गई रसीली चिकन बोटी।", "alt": "अफगानी चिकन बोटी"}
        }
    },
    {
        "id": "shahi-gulab-jamun-special",
        "country": "Pakistan",
        "name": "Halwai Shahi Gulab Jamun",
        "cat": "desserts",
        "catLabel": "Desserts",
        "veg": "veg",
        "time": 45,
        "diff": "Medium",
        "servings": "6 people",
        "alt": "Glossy golden-brown milk dough balls soaked in warm rose cardamom sugar syrup with ZaikaWorlds logo",
        "desc": "Classic festive sweet of golden-brown fried milk solids (khoya) dumplings soaked in warm, fragrant rose-cardamom sugar syrup.",
        "intro": "Gulab Jamun is the undisputed king of celebratory South Asian confections. Soft, melt-in-mouth dumplings made from fresh khoya and paneer are fried gently in desi ghee until mahogany brown, then soaked deeply in rose-infused sugar syrup.",
        "ing": ["Soft unsweetened khoya (mawa) 1.5 cups", "Fresh paneer grated 0.5 cup", "All-purpose flour (maida) 3 tbsp", "Semolina (sooji) 1 tbsp", "Baking powder 0.25 tsp", "Sugar for syrup 2 cups", "Water 2 cups", "Cardamom pods 4", "Rose water 1 tbsp", "Desi ghee or oil for deep frying"],
        "steps": [
            "For syrup: boil sugar, water, and crushed cardamoms for 8 minutes into a sticky, fragrant syrup; stir in rose water and keep warm.",
            "Grate khoya and paneer onto a flat plate; knead thoroughly with palms for 8 minutes until completely smooth with no grains.",
            "Add flour, semolina, and baking powder; gently knead into a soft, crack-free dough.",
            "Roll into 15 to 18 small smooth balls without any surface cracks.",
            "Heat ghee on lowest flame; gently slide in balls and fry very slowly on low heat for 12 to 14 minutes, gently swirling ghee around them until evenly deep golden-brown.",
            "Remove directly from hot ghee and drop into warm sugar syrup; let soak for at least 1 hour.",
            "Serve warm garnished with slivered pistachios."
        ],
        "tip": "The ghee temperature must be low; if the ghee is too hot, the jamuns will brown on the outside while remaining raw and doughy inside.",
        "nutrition": {"calories": 320, "proteinContent": 5.0, "fatContent": 12.0, "carbohydrateContent": 48.0},
        "lang": {
            "ru": {"name": "Halwai Shahi Gulab Jamun", "catLabel": "Desserts", "diff": "Darmiyana", "servings": "6 log", "desc": "Khoya aur sheere mein doobay garam gulab jamun.", "alt": "Shahi Gulab Jamun"},
            "hi": {"name": "शाही गुलाब जामुन", "catLabel": "मिठाई", "diff": "मध्यम", "servings": "6 लोग", "desc": "खोया और गुलाब की चाशनी में डूबे रसीले गुलाब जामुन।", "alt": "शाही गुलाब जामुन"}
        }
    },
    {
        "id": "hyderabadi-mutton-haleem",
        "country": "India",
        "name": "Royal Hyderabadi Mutton Haleem",
        "cat": "desi-dishes",
        "catLabel": "Desi Dishes",
        "veg": "nonveg",
        "time": 150,
        "diff": "Hard",
        "servings": "8 people",
        "alt": "Rich pounded mutton and multi-grain stew topped with fried onions, mint and ghee with ZaikaWorlds logo",
        "desc": "Slow-cooked savory porridge of tender mutton, pounded wheat, barley, lentils, and desi ghee, beaten into a velvety, stretchy delicacy.",
        "intro": "Hyderabadi Haleem holds a prestigious Geographical Indication (GI) status for its unique preparation. Mutton, cracked wheat, lentils, and whole spices are cooked for hours and continuously beaten with wooden pestles until the meat fibers dissolve into a rich, stretchy stew.",
        "ing": ["Boneless mutton 1kg", "Cracked wheat (daliya) 1 cup", "Mixed lentils (chana, moong, masoor, urad) 0.5 cup", "Ginger garlic paste 3 tbsp", "Garam masala whole and powdered 2 tbsp", "Desi ghee 1 cup", "Fried crisp onions (birista) 1 cup", "Green chilies chopped 4", "Fresh mint and coriander chopped 0.5 cup", "Lemon wedges and fried cashews for garnish", "Salt 2 tsp"],
        "steps": [
            "Soak cracked wheat and mixed lentils in warm water for 2 hours; cook in 5 cups water until mushy and blend coarsely.",
            "In a heavy pot, heat half the desi ghee; fry ginger-garlic paste and mutton pieces with salt, chili, and garam masala for 10 minutes.",
            "Add 4 cups water, cover, and pressure cook or simmer for 60 minutes until meat is ultra-tender.",
            "Shred the cooked meat using a wooden masher (ghota).",
            "Combine shredded meat, meat broth, and cooked lentil-wheat mixture in a large heavy pot.",
            "Pound and mash continuously with a wooden masher on low heat for 35 minutes until the mixture develops its characteristic stretchy, velvety texture.",
            "Fold in remaining melted desi ghee and half the fried onions.",
            "Serve hot garnished with crisp golden onions, mint leaves, fried cashews, and a squeeze of fresh lemon."
        ],
        "tip": "The continuous wooden mashing (ghotna) is essential; it stretches the shredded meat fibers into the wheat starches to create the signature silky texture.",
        "nutrition": {"calories": 580, "proteinContent": 48.0, "fatContent": 32.0, "carbohydrateContent": 36.0},
        "lang": {
            "ru": {"name": "Royal Hyderabadi Mutton Haleem", "catLabel": "Desi Dishes", "diff": "Mushkil", "servings": "8 log", "desc": "Asal Hyderabadi mutton aur daliya ghota haleem.", "alt": "Hyderabadi Mutton Haleem"},
            "hi": {"name": "हैदराबादी मटन हलीम", "catLabel": "देसी व्यंजन", "diff": "कठिन", "servings": "8 लोग", "desc": "गेहूं, दालों और मटन का मखमली रेशेदार हलीम।", "alt": "हैदराबादी मटन हलीम"}
        }
    }
]

# Write to file
with open("new_15_batch.json", "w", encoding="utf-8") as f:
    json.dump(NEW_15_RECIPES, f, indent=2, ensure_ascii=False)

print(f"Generated {len(NEW_15_RECIPES)} recipes data in new_15_batch.json")
