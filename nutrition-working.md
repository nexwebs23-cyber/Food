# Nutrition estimates — working notes

Per-serving nutrition estimates for all 33 Zaika Worlds recipes, computed 2026-10-31 from each recipe's REAL ingredient list in `index.html` (RECIPES array, `ing` field) and its listed servings. These are estimates, not lab measurements. Companion file: `nutrition.json` (same numbers, machine-readable).

## Method

1. Each ingredient quantity in the recipe's `ing` list was converted to grams (see conversions below).
2. Each gram amount was multiplied by a USDA FoodData Central per-100g value (SR Legacy / Foundation, verified by web search 2026-10-31 for the big staples: chicken breast raw, basmati rice raw, ghee, chickpeas cooked, beef stew meat, lentils dry, yoghurt plain whole milk, wheat flour white all-purpose; remaining values are standard USDA SR Legacy entries).
3. Totals were divided by the recipe's listed servings. Calories are rounded to the nearest whole number, macros to 1 decimal place, sodium to the nearest whole mg.
4. RAW nutrient values are used with RAW weights: nutrients are conserved through cooking (water loss only concentrates them per gram). Bone-in chicken is counted at 70% edible yield; a whole duck at 50% edible yield.
5. Where a quantity was vague ("to taste", "a pinch", "as needed", "for garnish", "to serve") a small standard amount was assumed and is marked "amount assumed" in the breakdown. Sub-2g spice pinches (turmeric, cumin, oregano, cardamom, etc.) are nutritionally negligible and are omitted.
6. If a recipe's ingredients are insufficient to compute a field, that field is OMITTED for that recipe — never 0, never a guess. See "Omitted fields" below.

## Conversions used

- 1 cup: rice (dry) 185g, flour 125g, sugar 200g, semolina 167g, lentils dry 192g, chickpeas (cooked) 164g, beans (dry) 200g, milk/yoghurt 245g, ghee 205g, oil 218g, peas 145g, bean sprouts 104g, wheat berries 190g, barley 184g.
- 1 tbsp: oil/ghee/butter 14g, flour 8g, sugar 12.5g, honey 21g, soy sauce 16g, fish sauce 18g, tomato paste 16g, tahini 15g, miso 17g, mayonnaise 14g, hoisin 16g, tamarind paste 15g, spice mix 7g, chutney 15g, juice/vinegar 15g.
- 1 tsp: salt 6g, sugar 4g, spices ~2g. 1 onion 150g, 1 tomato 120g (large 180g), 1 potato 170g, 1 egg 50g, 1 yolk 17g, 1 garlic clove 3g, 1 green chilli 15g, 1 lemon/lime (juice) 30g, 1 carrot 60g, 1 cucumber 300g, 1 mango (flesh) 200g, 1 spring onion 15g, 1 red pepper 120g, 1 aubergine (large) 450g, 1 fennel bulb 200g, 1 leek 90g, 1 orange 130g, 1 nori sheet 2.6g, 1 wonton wrapper 8g, 1 mandarin pancake 25g, 1 corn tortilla 30g, 1 bun 60g, 1 bread slice 30g, 1 ramen portion (dry) 90g.
- Frying oil absorbed (not the oil in the pan): deep-fry 3 tbsp (42g), shallow-fry 2 tbsp (28g), brushing/toasting 1 tbsp (14g).
- Salt = 387.5 mg sodium per gram. Salted butter sodium 700 mg/100g. Dried ramen noodle sodium estimated 800 mg/100g.

## Key assumptions and estimates

- **Bone-in chicken** (biryani, karahi, coq au vin): 70% edible yield; blended skinless chicken meat value 150 kcal / 22g protein / 6g fat / 1.8g sat fat / 75mg sodium per 100g.
- **Beef**: stew/shank 240 kcal / 26g protein / 14g fat / 5.8g sat fat per 100g (mid-range of the verified 124–251 kcal range); ground beef 85% lean 215/19/15/5.8; brisket 216/20/14/5.5; chuck 215/20/14/5.5 per 100g.
- **Peking duck**: whole bird 2.25kg at 50% edible yield = 1125g meat with skin (337 kcal / 18g protein / 28g fat / 9.5g sat fat per 100g).
- **Khoya**: no USDA entry — estimated 400 kcal / 12g protein / 28g fat / 18g sat fat / 28g carbs / 25g sugar / 100mg sodium per 100g (gulab jamun, gajar halwa).
- **Shami kebabs** (bun kebab): ready-made, composition unknown — estimated 220 kcal / 20g protein / 13g fat / 5g sat fat / 5g carbs / 2g fiber / 400mg sodium per 100g, 8 x 50g = 400g.
- **Meat pie pastry**: no weight listed — estimated 270g total (135g shortcrust + 135g puff) for 6 pies.
- **Gulab jamun syrup**: 400g sugar in the syrup; only 150g counted as absorbed into the jamuns, the rest stays in the syrup.
- **Beef bones** (beef pho 1.5kg, haleem 250g): NOT counted — broth extraction is unquantified.
- **"Beef or lamb" mince** (bobotie, moussaka): computed as beef; lamb would be slightly higher in fat.
- **Achiote paste** (tacos): no USDA entry — tamarind value used as a proxy.

## Omitted fields

**sodiumContent is omitted for 8 recipes** because no salt or salty ingredient is listed at all, so any number would be invented: biryani, nihari, tikka, halwapuri, samosa, gulabjamun, gajarhalwa, lassi.

**Sodium is included but UNDERSTATED for 3 recipes** (no added salt is listed; sodium comes only from the salty ingredients that are listed): moussaka (butter, cheese, milk only), feijoada (cured meats only), meatpie (stock, sauces, Vegemite only). Pizza sodium is slightly understated (salt in the sauce is unquantified).

**Accompaniments without quantities are omitted** (and flagged per recipe below): pitta for hummus/falafel, rice + collard greens + farofa for feijoada, salsa for tacos, rouille for bouillabaisse, pickled ginger / wasabi for sushi, extra pecorino for carbonara, chilli oil / extra soy / black vinegar for dim sum.

**Bun kebab sodium is approximate**: it comes only from estimated items (ready-made kebab, bun, chutneys).

**Ramen sodium (3199 mg/serving) is high but real**: stock 1.5L + soy sauce + miso + dried noodles are all salty; ramen is genuinely a high-sodium dish.

## Per-recipe breakdowns

Per-serving values are the numbers in `nutrition.json`. The tables show each ingredient's contribution to the WHOLE recipe (before dividing by servings); kcal are rounded to 1 decimal here for checking.

### Chicken Biryani (`biryani`) — 4 servings

**Per serving:** 917 kcal, protein 43.8g, fat 22.2g, saturated fat 10.3g, carbs 130.7g, sugar 10.6g, fiber 6.1g, sodium OMITTED (no salt listed)

- ⚠️ No salt or salty ingredient listed - sodiumContent omitted, not guessed.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Chicken, bone-in 750g (70% edible) | 525g | 787.5 | 115.5 | 31.5 | 9.5 | 0.0 | 0.0 | 0.0 | 393.8 |
| Yoghurt 1 cup | 245g | 149.5 | 8.6 | 8.1 | 5.1 | 11.5 | 11.5 | 0.0 | 112.7 |
| Basmati rice 3 cups | 555g | 1998.0 | 38.9 | 3.3 | 1.1 | 432.9 | 0.0 | 5.5 | 27.8 |
| Biryani masala 3 tbsp | 21g | 63.0 | 2.1 | 2.1 | 0.2 | 11.5 | 1.1 | 5.2 | 21.0 |
| Ginger-garlic paste 2 tbsp | 30g | 24.0 | 0.5 | 0.2 | 0.1 | 5.4 | 0.5 | 0.6 | 3.9 |
| Onions 3, browned | 450g | 180.0 | 5.0 | 0.5 | 0.0 | 41.9 | 18.9 | 7.6 | 18.0 |
| Tomatoes 2 | 240g | 43.2 | 2.2 | 0.5 | 0.0 | 9.4 | 6.2 | 2.9 | 12.0 |
| Green chillies 4 | 60g | 24.0 | 1.2 | 0.1 | 0.0 | 5.7 | 3.0 | 0.9 | 4.2 |
| Fresh coriander (assumed) *(amount assumed)* | 30g | 6.9 | 0.6 | 0.1 | 0.0 | 1.1 | 0.3 | 0.8 | 13.8 |
| Mint (assumed) *(amount assumed)* | 15g | 6.6 | 0.5 | 0.1 | 0.0 | 1.3 | 0.0 | 0.8 | 4.5 |
| Lemon juice 1 (assumed) *(amount assumed)* | 30g | 6.6 | 0.1 | 0.1 | 0.0 | 2.1 | 0.8 | 0.1 | 0.3 |
| Ghee 3 tbsp | 42g | 378.0 | 0.0 | 42.0 | 25.2 | 0.0 | 0.0 | 0.0 | 0.0 |
| **Whole recipe** | | **3667.2** | **175.1** | **88.6** | **41.2** | **522.7** | **42.2** | **24.5** | **611.9** |

### Beef Nihari (`nihari`) — 5 servings

**Per serving:** 723 kcal, protein 53.6g, fat 49.7g, saturated fat 24.3g, carbs 11.4g, sugar 2.0g, fiber 2.3g, sodium OMITTED (no salt listed)

- ⚠️ No salt or salty ingredient listed - sodiumContent omitted, not guessed.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Beef shank 1kg | 1000g | 2400.0 | 260.0 | 140.0 | 58.0 | 0.0 | 0.0 | 0.0 | 700.0 |
| Nihari masala 4 tbsp | 28g | 84.0 | 2.8 | 2.8 | 0.3 | 15.4 | 1.4 | 7.0 | 28.0 |
| Flour 3 tbsp | 24g | 87.4 | 2.5 | 0.2 | 0.0 | 18.3 | 0.1 | 0.6 | 0.5 |
| Ginger-garlic paste 2 tbsp | 30g | 24.0 | 0.5 | 0.2 | 0.1 | 5.4 | 0.5 | 0.6 | 3.9 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Ghee/oil 1/2 cup | 105g | 945.0 | 0.0 | 105.0 | 63.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Fresh coriander (assumed) *(amount assumed)* | 15g | 3.4 | 0.3 | 0.1 | 0.0 | 0.6 | 0.1 | 0.4 | 6.9 |
| Green chilli (assumed) *(amount assumed)* | 15g | 6.0 | 0.3 | 0.0 | 0.0 | 1.4 | 0.8 | 0.2 | 1.1 |
| Lemon juice (assumed) *(amount assumed)* | 30g | 6.6 | 0.1 | 0.1 | 0.0 | 2.1 | 0.8 | 0.1 | 0.3 |
| **Whole recipe** | | **3616.4** | **268.2** | **248.6** | **121.4** | **57.1** | **9.9** | **11.5** | **746.6** |

### Chicken Karahi (`karahi`) — 4 servings

**Per serving:** 478 kcal, protein 31.0g, fat 34.6g, saturated fat 18.1g, carbs 9.9g, sugar 5.6g, fiber 2.6g, sodium 692 mg

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Chicken, bone-in 750g (70% edible) | 525g | 787.5 | 115.5 | 31.5 | 9.5 | 0.0 | 0.0 | 0.0 | 393.8 |
| Tomatoes 4 large | 720g | 129.6 | 6.5 | 1.4 | 0.0 | 28.1 | 18.7 | 8.6 | 36.0 |
| Ginger-garlic paste 1 tbsp | 15g | 12.0 | 0.3 | 0.1 | 0.0 | 2.7 | 0.3 | 0.3 | 1.9 |
| Ginger julienne (assumed) *(amount assumed)* | 15g | 12.0 | 0.3 | 0.1 | 0.0 | 2.7 | 0.3 | 0.3 | 1.9 |
| Green chillies 4 | 60g | 24.0 | 1.2 | 0.1 | 0.0 | 5.7 | 3.0 | 0.9 | 4.2 |
| Ghee/oil 1/2 cup | 105g | 945.0 | 0.0 | 105.0 | 63.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Salt 1 tsp (assumed) *(amount assumed)* | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| Fresh coriander (assumed) *(amount assumed)* | 15g | 3.4 | 0.3 | 0.1 | 0.0 | 0.6 | 0.1 | 0.4 | 6.9 |
| **Whole recipe** | | **1913.5** | **124.0** | **138.4** | **72.5** | **39.7** | **22.4** | **10.6** | **2769.8** |

### Daal Fry (Tadka Daal) (`daal`) — 4 servings

**Per serving:** 363 kcal, protein 18.3g, fat 11.7g, saturated fat 6.5g, carbs 48.8g, sugar 2.1g, fiber 8.6g, sodium 590 mg

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Masoor/moong daal 1.5 cups dry | 288g | 1013.8 | 70.8 | 3.2 | 0.6 | 182.6 | 5.8 | 30.8 | 17.3 |
| Salt 1 tsp (assumed) *(amount assumed)* | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| Garlic 4 cloves | 12g | 17.9 | 0.8 | 0.1 | 0.0 | 4.0 | 0.1 | 0.3 | 2.0 |
| Whole red chillies 3 | 9g | 25.2 | 0.9 | 1.3 | 0.2 | 4.5 | 0.9 | 2.5 | 9.0 |
| Ghee 3 tbsp | 42g | 378.0 | 0.0 | 42.0 | 25.2 | 0.0 | 0.0 | 0.0 | 0.0 |
| Green chilli (assumed) *(amount assumed)* | 15g | 6.0 | 0.3 | 0.0 | 0.0 | 1.4 | 0.8 | 0.2 | 1.1 |
| Fresh coriander (assumed) *(amount assumed)* | 15g | 3.4 | 0.3 | 0.1 | 0.0 | 0.6 | 0.1 | 0.4 | 6.9 |
| Lemon juice (assumed) *(amount assumed)* | 30g | 6.6 | 0.1 | 0.1 | 0.0 | 2.1 | 0.8 | 0.1 | 0.3 |
| **Whole recipe** | | **1450.9** | **73.3** | **46.7** | **26.0** | **195.1** | **8.4** | **34.3** | **2361.6** |

### Chapli Kabab (`chapli`) — 4 servings

**Per serving:** 376 kcal, protein 25.1g, fat 26.1g, saturated fat 8.2g, carbs 10.0g, sugar 3.5g, fiber 1.7g, sodium 673 mg

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Beef mince 500g | 500g | 1075.0 | 95.0 | 75.0 | 29.0 | 0.0 | 0.0 | 0.0 | 350.0 |
| Tomato 1 | 120g | 21.6 | 1.1 | 0.2 | 0.0 | 4.7 | 3.1 | 1.4 | 6.0 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Pomegranate seeds 1 tbsp | 15g | 12.4 | 0.3 | 0.2 | 0.0 | 2.9 | 2.1 | 0.6 | 0.4 |
| Green chillies 3 | 45g | 18.0 | 0.9 | 0.1 | 0.0 | 4.3 | 2.2 | 0.7 | 3.1 |
| Ginger (assumed) *(amount assumed)* | 15g | 12.0 | 0.3 | 0.1 | 0.0 | 2.7 | 0.3 | 0.3 | 1.9 |
| Salt 1 tsp (assumed) *(amount assumed)* | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| Maize flour 2 tbsp | 16g | 57.6 | 1.4 | 0.6 | 0.1 | 11.5 | 0.1 | 1.1 | 0.8 |
| Oil for shallow frying (absorbed, assumed) *(amount assumed)* | 28g | 247.5 | 0.0 | 28.0 | 3.6 | 0.0 | 0.0 | 0.0 | 0.0 |
| **Whole recipe** | | **1504.2** | **100.6** | **104.3** | **32.8** | **40.0** | **14.1** | **6.7** | **2693.4** |

### Chicken Tikka (`tikka`) — 4 servings

**Per serving:** 279 kcal, protein 43.6g, fat 8.9g, saturated fat 3.6g, carbs 3.6g, sugar 1.8g, fiber 0.5g, sodium OMITTED (no salt listed)

- ⚠️ No salt or salty ingredient listed - sodiumContent omitted, not guessed.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Chicken, boneless 750g | 750g | 900.0 | 168.8 | 19.5 | 4.5 | 0.0 | 0.0 | 0.0 | 555.0 |
| Yoghurt 1/2 cup | 122g | 74.4 | 4.3 | 4.0 | 2.6 | 5.7 | 5.7 | 0.0 | 56.1 |
| Red chilli 1 tbsp | 7g | 21.0 | 0.7 | 0.7 | 0.1 | 3.9 | 0.4 | 1.8 | 7.0 |
| Ginger-garlic paste 1 tbsp | 15g | 12.0 | 0.3 | 0.1 | 0.0 | 2.7 | 0.3 | 0.3 | 1.9 |
| Lemon juice 1 | 30g | 6.6 | 0.1 | 0.1 | 0.0 | 2.1 | 0.8 | 0.1 | 0.3 |
| Butter for brushing 1 tbsp (assumed) *(amount assumed)* | 14g | 100.4 | 0.1 | 11.3 | 7.1 | 0.0 | 0.0 | 0.0 | 98.0 |
| **Whole recipe** | | **1114.4** | **174.2** | **35.7** | **14.3** | **14.4** | **7.1** | **2.1** | **718.4** |

### Halwa Puri Nashta (`halwapuri`) — 4 servings

**Per serving:** 1017 kcal, protein 21.4g, fat 31.5g, saturated fat 16.3g, carbs 163.3g, sugar 57.0g, fiber 11.9g, sodium OMITTED (no salt listed)

- ⚠️ No salt or salty ingredient listed - sodiumContent omitted, not guessed.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Flour 2 cups | 250g | 910.0 | 25.8 | 2.5 | 0.5 | 190.8 | 0.8 | 6.8 | 5.0 |
| Semolina 1 cup | 167g | 601.2 | 21.2 | 1.8 | 0.3 | 121.9 | 0.0 | 6.5 | 1.7 |
| Sugar 1 cup | 200g | 774.0 | 0.0 | 0.0 | 0.0 | 200.0 | 200.0 | 0.0 | 0.0 |
| Ghee 1/2 cup | 105g | 945.0 | 0.0 | 105.0 | 63.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Chickpeas, boiled 2 cups | 328g | 537.9 | 29.2 | 8.5 | 1.0 | 89.9 | 15.7 | 24.9 | 23.0 |
| Potato 1 | 170g | 130.9 | 3.4 | 0.2 | 0.0 | 28.9 | 1.4 | 3.7 | 10.2 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Tomato 1 | 120g | 21.6 | 1.1 | 0.2 | 0.0 | 4.7 | 3.1 | 1.4 | 6.0 |
| Almonds for garnish (assumed) *(amount assumed)* | 15g | 86.8 | 3.1 | 7.5 | 0.6 | 3.3 | 0.7 | 1.8 | 0.1 |
| **Whole recipe** | | **4067.5** | **85.4** | **125.9** | **65.4** | **653.4** | **227.9** | **47.7** | **52.0** |

### Punjabi Samosa (`samosa`) — 6 servings

**Per serving:** 317 kcal, protein 7.4g, fat 7.6g, saturated fat 1.0g, carbs 54.1g, sugar 2.3g, fiber 4.5g, sodium OMITTED (no salt listed)

- ⚠️ No salt or salty ingredient listed - sodiumContent omitted, not guessed.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Flour 2 cups | 250g | 910.0 | 25.8 | 2.5 | 0.5 | 190.8 | 0.8 | 6.8 | 5.0 |
| Potatoes, boiled 4 | 680g | 523.6 | 13.6 | 0.7 | 0.0 | 115.6 | 5.4 | 15.0 | 40.8 |
| Peas 1/2 cup | 72g | 60.5 | 3.9 | 0.3 | 0.1 | 10.8 | 4.1 | 4.0 | 1.4 |
| Ginger (assumed) *(amount assumed)* | 15g | 12.0 | 0.3 | 0.1 | 0.0 | 2.7 | 0.3 | 0.3 | 1.9 |
| Green chilli (assumed) *(amount assumed)* | 15g | 6.0 | 0.3 | 0.0 | 0.0 | 1.4 | 0.8 | 0.2 | 1.1 |
| Fresh coriander (assumed) *(amount assumed)* | 15g | 3.4 | 0.3 | 0.1 | 0.0 | 0.6 | 0.1 | 0.4 | 6.9 |
| Pomegranate seeds (assumed) *(amount assumed)* | 15g | 12.4 | 0.3 | 0.2 | 0.0 | 2.9 | 2.1 | 0.6 | 0.4 |
| Oil for deep frying (absorbed, assumed) *(amount assumed)* | 42g | 371.3 | 0.0 | 42.0 | 5.5 | 0.0 | 0.0 | 0.0 | 0.0 |
| **Whole recipe** | | **1899.3** | **44.4** | **45.9** | **6.1** | **324.7** | **13.5** | **27.2** | **57.6** |

### Bun Kebab (`bunkebab`) — 4 servings

**Per serving:** 462 kcal, protein 26.7g, fat 19.5g, saturated fat 7.6g, carbs 45.0g, sugar 9.0g, fiber 5.0g, sodium 740 mg

- ⚠️ Sodium comes only from estimated items (ready-made kebab, bun, chutneys) - treat as approximate.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Shami kebabs 8 (50g each, estimated composition) *(composition estimated)* | 400g | 880.0 | 80.0 | 52.0 | 20.0 | 20.0 | 0.0 | 8.0 | 1600.0 |
| Buns 4 (60g each) | 240g | 696.0 | 21.6 | 12.0 | 2.4 | 124.8 | 14.4 | 6.0 | 1080.0 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Tomato 1 | 120g | 21.6 | 1.1 | 0.2 | 0.0 | 4.7 | 3.1 | 1.4 | 6.0 |
| Green chutney (assumed) *(amount assumed)* | 30g | 18.0 | 0.6 | 0.9 | 0.1 | 1.8 | 0.9 | 0.6 | 90.0 |
| Tamarind chutney (assumed) *(amount assumed)* | 30g | 45.0 | 0.1 | 0.1 | 0.0 | 11.4 | 9.0 | 0.6 | 60.0 |
| Yoghurt (assumed) *(amount assumed)* | 30g | 18.3 | 1.1 | 1.0 | 0.6 | 1.4 | 1.4 | 0.0 | 13.8 |
| Green chilli (assumed) *(amount assumed)* | 15g | 6.0 | 0.3 | 0.0 | 0.0 | 1.4 | 0.8 | 0.2 | 1.1 |
| Fresh coriander (assumed) *(amount assumed)* | 15g | 3.4 | 0.3 | 0.1 | 0.0 | 0.6 | 0.1 | 0.4 | 6.9 |
| Butter for toasting 1 tbsp (assumed) *(amount assumed)* | 14g | 100.4 | 0.1 | 11.3 | 7.1 | 0.0 | 0.0 | 0.0 | 98.0 |
| **Whole recipe** | | **1848.7** | **106.9** | **77.9** | **30.3** | **180.0** | **36.0** | **19.8** | **2961.8** |

### Gulab Jamun (`gulabjamun`) — 6 servings

**Per serving:** 340 kcal, protein 5.4g, fat 18.7g, saturated fat 8.4g, carbs 39.7g, sugar 35.4g, fiber 0.1g, sodium OMITTED (no salt listed)

- ⚠️ No salt or salty ingredient listed - sodiumContent omitted, not guessed.
- ⚠️ Only ~150g of the 400g syrup sugar is counted as absorbed; the rest stays in the syrup.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Khoya 250g (estimated value) *(khoya value estimated)* | 250g | 1000.0 | 30.0 | 70.0 | 45.0 | 70.0 | 62.5 | 0.0 | 250.0 |
| Flour 3 tbsp | 24g | 87.4 | 2.5 | 0.2 | 0.0 | 18.3 | 0.1 | 0.6 | 0.5 |
| Sugar absorbed from syrup 150g of 400g (assumed) *(absorption assumed)* | 150g | 580.5 | 0.0 | 0.0 | 0.0 | 150.0 | 150.0 | 0.0 | 0.0 |
| Oil/ghee for frying (absorbed, assumed) *(amount assumed)* | 42g | 371.3 | 0.0 | 42.0 | 5.5 | 0.0 | 0.0 | 0.0 | 0.0 |
| **Whole recipe** | | **2039.1** | **32.5** | **112.2** | **50.5** | **238.3** | **212.6** | **0.6** | **250.5** |

### Gajar Ka Halwa (`gajarhalwa`) — 5 servings

**Per serving:** 603 kcal, protein 12.6g, fat 28.6g, saturated fat 16.1g, carbs 78.9g, sugar 67.3g, fiber 6.1g, sodium OMITTED (no salt listed)

- ⚠️ No salt or salty ingredient listed - sodiumContent omitted, not guessed.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Red carrots 1kg | 1000g | 410.0 | 9.0 | 2.0 | 0.0 | 100.0 | 47.0 | 28.0 | 690.0 |
| Milk 1 litre | 1000g | 610.0 | 32.0 | 33.0 | 19.0 | 48.0 | 51.0 | 0.0 | 440.0 |
| Sugar 1 cup | 200g | 774.0 | 0.0 | 0.0 | 0.0 | 200.0 | 200.0 | 0.0 | 0.0 |
| Ghee 4 tbsp | 56g | 504.0 | 0.0 | 56.0 | 33.6 | 0.0 | 0.0 | 0.0 | 0.0 |
| Khoya 150g (estimated value) *(khoya value estimated)* | 150g | 600.0 | 18.0 | 42.0 | 27.0 | 42.0 | 37.5 | 0.0 | 150.0 |
| Almonds (assumed) *(amount assumed)* | 20g | 115.8 | 4.2 | 10.0 | 0.8 | 4.4 | 0.9 | 2.4 | 0.2 |
| **Whole recipe** | | **3013.8** | **63.2** | **143.0** | **80.4** | **394.4** | **336.4** | **30.4** | **1280.2** |

### Mango Lassi (`lassi`) — 3 servings

**Per serving:** 212 kcal, protein 6.7g, fat 5.9g, saturated fat 3.5g, carbs 36.2g, sugar 34.8g, fiber 2.2g, sodium OMITTED (no salt listed)

- ⚠️ No salt or salty ingredient listed - sodiumContent omitted, not guessed.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Ripe mangoes 2 (flesh) | 400g | 240.0 | 3.2 | 1.6 | 0.4 | 60.0 | 56.0 | 6.4 | 4.0 |
| Yoghurt 1.5 cups | 367g | 223.9 | 12.8 | 12.1 | 7.7 | 17.2 | 17.2 | 0.0 | 168.8 |
| Milk 1/2 cup | 122g | 74.4 | 3.9 | 4.0 | 2.3 | 5.9 | 6.2 | 0.0 | 53.7 |
| Sugar 2 tbsp | 25g | 96.8 | 0.0 | 0.0 | 0.0 | 25.0 | 25.0 | 0.0 | 0.0 |
| Mint for garnish (assumed) *(amount assumed)* | 5g | 2.2 | 0.2 | 0.0 | 0.0 | 0.4 | 0.0 | 0.2 | 1.5 |
| **Whole recipe** | | **637.2** | **20.1** | **17.8** | **10.4** | **108.5** | **104.5** | **6.7** | **228.0** |

### Margherita Pizza (`pizza`) — 4 servings

**Per serving:** 769 kcal, protein 28.7g, fat 25.9g, saturated fat 9.9g, carbs 103.4g, sugar 3.6g, fiber 5.2g, sodium 1371 mg

- ⚠️ Salt in the sauce is unquantified, so sodium is slightly understated.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Strong bread flour 500g | 500g | 1820.0 | 51.5 | 5.0 | 1.0 | 381.5 | 1.5 | 13.5 | 10.0 |
| Water 325ml | 325g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Instant yeast 7g | 7g | 22.8 | 2.8 | 0.6 | 0.1 | 2.9 | 0.0 | 1.9 | 3.5 |
| Fine salt 10g | 10g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3875.0 |
| Olive oil 2 tbsp (dough) | 28g | 247.5 | 0.0 | 28.0 | 3.9 | 0.0 | 0.0 | 0.0 | 0.6 |
| Olive oil 1 tbsp (sauce, assumed) *(amount assumed)* | 14g | 123.8 | 0.0 | 14.0 | 2.0 | 0.0 | 0.0 | 0.0 | 0.3 |
| San Marzano tomatoes 400g | 400g | 72.0 | 3.6 | 0.8 | 0.0 | 15.6 | 10.4 | 4.8 | 20.0 |
| Mozzarella 250g | 250g | 747.5 | 55.0 | 55.0 | 32.5 | 5.0 | 2.5 | 0.0 | 1575.0 |
| Fresh basil 1 handful (assumed) *(amount assumed)* | 10g | 2.3 | 0.3 | 0.1 | 0.0 | 0.3 | 0.0 | 0.2 | 0.4 |
| Garlic 1 clove | 3g | 4.5 | 0.2 | 0.0 | 0.0 | 1.0 | 0.0 | 0.1 | 0.5 |
| Semolina for dusting (assumed) *(amount assumed)* | 10g | 36.0 | 1.3 | 0.1 | 0.0 | 7.3 | 0.0 | 0.4 | 0.1 |
| **Whole recipe** | | **3076.3** | **114.7** | **103.5** | **39.5** | **413.5** | **14.5** | **20.8** | **5485.4** |

### Spaghetti Carbonara (`carbonara`) — 4 servings

**Per serving:** 673 kcal, protein 26.7g, fat 27.9g, saturated fat 10.9g, carbs 77.3g, sugar 2.8g, fiber 3.5g, sodium 1356 mg

- ⚠️ Extra pecorino/pepper to serve is unquantified and omitted.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Spaghetti 400g | 400g | 1484.0 | 52.0 | 6.0 | 1.2 | 300.0 | 10.8 | 12.8 | 24.0 |
| Guanciale 150g | 150g | 675.0 | 18.0 | 66.0 | 24.0 | 1.5 | 0.0 | 0.0 | 2250.0 |
| Egg yolks 4 | 68g | 219.0 | 10.9 | 18.4 | 6.8 | 2.4 | 0.1 | 0.0 | 32.6 |
| Whole egg 1 | 50g | 71.5 | 6.3 | 4.8 | 1.6 | 0.3 | 0.2 | 0.0 | 71.0 |
| Pecorino Romano 60g | 60g | 232.2 | 19.2 | 16.2 | 10.2 | 2.4 | 0.0 | 0.0 | 720.0 |
| Black pepper 2 tsp | 4g | 10.0 | 0.4 | 0.1 | 0.0 | 2.6 | 0.0 | 1.0 | 0.8 |
| Salt for pasta water 1 tsp (assumed retained) *(amount assumed)* | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| **Whole recipe** | | **2691.7** | **106.8** | **111.4** | **43.8** | **309.3** | **11.2** | **13.8** | **5423.4** |

### Sushi (`sushi`) — 4 servings

**Per serving:** 626 kcal, protein 23.5g, fat 19.4g, saturated fat 3.7g, carbs 84.5g, sugar 7.9g, fiber 2.0g, sodium 1213 mg

- ⚠️ Pickled ginger and wasabi to serve are unquantified and omitted.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Sushi rice 2 cups dry | 370g | 1332.0 | 24.1 | 1.9 | 0.4 | 292.3 | 0.0 | 1.9 | 3.7 |
| Rice vinegar 4 tbsp | 60g | 10.8 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 0.0 | 0.0 |
| Sugar 2 tbsp | 25g | 96.8 | 0.0 | 0.0 | 0.0 | 25.0 | 25.0 | 0.0 | 0.0 |
| Salt 1 tsp | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| Nori sheets 4 | 10g | 35.0 | 4.0 | 0.2 | 0.1 | 4.4 | 0.0 | 3.5 | 200.0 |
| Salmon 300g | 300g | 624.0 | 60.0 | 39.0 | 9.0 | 0.0 | 0.0 | 0.0 | 180.0 |
| Cucumber 1 | 300g | 45.0 | 2.1 | 0.3 | 0.0 | 10.8 | 5.1 | 1.5 | 6.0 |
| Mayonnaise 3 tbsp | 42g | 285.6 | 0.4 | 31.5 | 4.6 | 0.4 | 0.4 | 0.0 | 266.7 |
| Sriracha 1 tsp | 6g | 6.0 | 0.1 | 0.1 | 0.0 | 1.2 | 1.0 | 0.1 | 108.0 |
| Soy sauce to serve 2 tbsp (assumed) *(amount assumed)* | 32g | 17.0 | 1.6 | 0.0 | 0.0 | 1.6 | 0.1 | 0.1 | 1760.0 |
| Sesame seeds 1 tbsp | 9g | 51.6 | 1.6 | 4.5 | 0.6 | 2.1 | 0.0 | 1.1 | 1.0 |
| **Whole recipe** | | **2503.7** | **93.8** | **77.4** | **14.7** | **338.0** | **31.6** | **8.1** | **4850.4** |

### Ramen (`ramen`) — 4 servings

**Per serving:** 696 kcal, protein 49.1g, fat 19.7g, saturated fat 4.3g, carbs 76.4g, sugar 2.9g, fiber 4.4g, sodium 3199 mg

- ⚠️ Dried-noodle sodium is an estimate (800 mg/100g); stock sodium is a standard value.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Chicken breasts/thighs 500g | 500g | 600.0 | 112.5 | 13.0 | 3.0 | 0.0 | 0.0 | 0.0 | 370.0 |
| Chicken stock 1.5 litres | 1500g | 105.0 | 10.5 | 4.5 | 1.5 | 7.5 | 3.0 | 0.0 | 5250.0 |
| Ramen noodles 4 portions dry | 360g | 1332.0 | 36.0 | 7.2 | 1.8 | 270.0 | 3.6 | 10.8 | 2880.0 |
| Garlic 4 cloves | 12g | 17.9 | 0.8 | 0.1 | 0.0 | 4.0 | 0.1 | 0.3 | 2.0 |
| Ginger 3cm piece (assumed) *(amount assumed)* | 15g | 12.0 | 0.3 | 0.1 | 0.0 | 2.7 | 0.3 | 0.3 | 1.9 |
| Soy sauce 3 tbsp | 48g | 25.4 | 2.4 | 0.0 | 0.0 | 2.4 | 0.2 | 0.1 | 2640.0 |
| Miso paste 2 tbsp | 34g | 68.0 | 4.1 | 2.0 | 0.3 | 8.8 | 2.0 | 1.7 | 1258.0 |
| Sesame oil 1 tbsp | 14g | 123.8 | 0.0 | 14.0 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Spring onions 4 | 60g | 19.2 | 1.1 | 0.1 | 0.0 | 4.4 | 1.4 | 1.6 | 9.6 |
| Eggs 4 | 200g | 286.0 | 25.2 | 19.0 | 6.2 | 1.4 | 0.8 | 0.0 | 284.0 |
| Chilli oil to serve 1 tbsp (assumed) *(amount assumed)* | 14g | 123.8 | 0.0 | 14.0 | 1.8 | 0.0 | 0.0 | 0.0 | 0.0 |
| Sesame seeds (assumed) *(amount assumed)* | 9g | 51.6 | 1.6 | 4.5 | 0.6 | 2.1 | 0.0 | 1.1 | 1.0 |
| Nori to serve (assumed) *(amount assumed)* | 5g | 17.5 | 2.0 | 0.1 | 0.0 | 2.2 | 0.0 | 1.8 | 100.0 |
| **Whole recipe** | | **2782.1** | **196.4** | **78.6** | **17.3** | **305.4** | **11.4** | **17.6** | **12796.6** |

### Tacos al Pastor (`tacos`) — 4 servings

**Per serving:** 678 kcal, protein 36.6g, fat 33.0g, saturated fat 10.9g, carbs 63.0g, sugar 14.5g, fiber 9.2g, sodium 736 mg

- ⚠️ Salsa to serve is unquantified and omitted; cumin/oregano pinches are nutritionally negligible and omitted.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Pork shoulder 700g | 700g | 1540.0 | 119.0 | 119.0 | 42.0 | 0.0 | 0.0 | 0.0 | 420.0 |
| Dried guajillo 3 + ancho 1 (assumed) *(amount assumed)* | 12g | 33.6 | 1.2 | 1.7 | 0.2 | 6.0 | 1.2 | 3.4 | 12.0 |
| Achiote paste 2 tbsp (tamarind proxy) *(proxy value)* | 30g | 72.0 | 0.9 | 0.2 | 0.0 | 18.6 | 11.4 | 1.5 | 9.0 |
| Garlic 3 cloves | 9g | 13.4 | 0.6 | 0.0 | 0.0 | 3.0 | 0.1 | 0.2 | 1.5 |
| White vinegar 3 tbsp | 45g | 8.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Orange juice 60ml | 60g | 27.0 | 0.4 | 0.1 | 0.0 | 6.0 | 5.0 | 0.1 | 0.6 |
| Salt 1 tsp (assumed) *(amount assumed)* | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| Pineapple 300g | 300g | 150.0 | 1.5 | 0.3 | 0.0 | 39.0 | 30.0 | 4.2 | 3.0 |
| Corn tortillas 12 | 360g | 784.8 | 20.5 | 10.4 | 1.4 | 158.4 | 2.9 | 22.7 | 158.4 |
| White onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Fresh coriander (assumed) *(amount assumed)* | 15g | 3.4 | 0.3 | 0.1 | 0.0 | 0.6 | 0.1 | 0.4 | 6.9 |
| Limes 2 (juice) | 60g | 18.0 | 0.4 | 0.1 | 0.0 | 6.6 | 1.0 | 1.7 | 1.2 |
| **Whole recipe** | | **2710.4** | **146.5** | **132.1** | **43.7** | **252.1** | **58.1** | **36.7** | **2943.6** |

### Pozole (`pozole`) — 6 servings

**Per serving:** 503 kcal, protein 31.8g, fat 29.8g, saturated fat 10.2g, carbs 27.6g, sugar 3.9g, fiber 5.3g, sodium 1225 mg

- ⚠️ 3 litres of water/light stock are not counted (water = 0; stock unquantified).

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Pork shoulder 1kg | 1000g | 2200.0 | 170.0 | 170.0 | 60.0 | 0.0 | 0.0 | 0.0 | 600.0 |
| White hominy 800g | 800g | 576.0 | 12.0 | 5.6 | 0.8 | 112.0 | 4.0 | 16.0 | 2000.0 |
| Dried guajillo 4 + ancho 2 (assumed) *(amount assumed)* | 18g | 50.4 | 1.8 | 2.5 | 0.4 | 9.0 | 1.8 | 5.0 | 18.0 |
| Onion 1 (pot) | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Garlic 6 cloves | 18g | 26.8 | 1.2 | 0.1 | 0.0 | 5.9 | 0.2 | 0.4 | 3.1 |
| Salt 2 tsp (assumed) *(amount assumed)* | 12g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4650.0 |
| Shredded cabbage to serve (assumed) *(amount assumed)* | 150g | 37.5 | 2.0 | 0.2 | 0.0 | 8.7 | 4.8 | 3.8 | 27.0 |
| Radish to serve (assumed) *(amount assumed)* | 100g | 16.0 | 0.7 | 0.1 | 0.0 | 3.4 | 1.9 | 1.6 | 39.0 |
| Onion to serve (assumed) *(amount assumed)* | 100g | 40.0 | 1.1 | 0.1 | 0.0 | 9.3 | 4.2 | 1.7 | 4.0 |
| Lime juice to serve (assumed) *(amount assumed)* | 30g | 9.0 | 0.2 | 0.1 | 0.0 | 3.3 | 0.5 | 0.8 | 0.6 |
| **Whole recipe** | | **3015.7** | **190.6** | **178.8** | **61.2** | **165.6** | **23.7** | **31.9** | **7347.7** |

### Pad Thai (`padthai`) — 4 servings

**Per serving:** 466 kcal, protein 26.5g, fat 8.1g, saturated fat 1.7g, carbs 74.5g, sugar 16.7g, fiber 3.7g, sodium 1081 mg

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Flat rice noodles 250g | 250g | 900.0 | 12.5 | 1.2 | 0.2 | 205.0 | 0.0 | 3.8 | 37.5 |
| Prawns 300g | 300g | 255.0 | 60.0 | 3.0 | 0.9 | 0.0 | 0.0 | 0.0 | 420.0 |
| Eggs 2 | 100g | 143.0 | 12.6 | 9.5 | 3.1 | 0.7 | 0.4 | 0.0 | 142.0 |
| Tamarind paste 3 tbsp | 45g | 108.0 | 1.4 | 0.3 | 0.0 | 27.9 | 17.1 | 2.2 | 13.5 |
| Fish sauce 3 tbsp | 54g | 18.9 | 2.8 | 0.0 | 0.0 | 1.9 | 1.9 | 0.0 | 3672.0 |
| Brown sugar 3 tbsp | 37g | 140.6 | 0.0 | 0.0 | 0.0 | 35.9 | 35.9 | 0.0 | 14.8 |
| Garlic 3 cloves | 9g | 13.4 | 0.6 | 0.0 | 0.0 | 3.0 | 0.1 | 0.2 | 1.5 |
| Bean sprouts 2 cups | 208g | 62.4 | 6.2 | 0.4 | 0.0 | 12.5 | 8.3 | 3.7 | 12.5 |
| Spring onions (assumed) *(amount assumed)* | 30g | 9.6 | 0.5 | 0.1 | 0.0 | 2.2 | 0.7 | 0.8 | 4.8 |
| Roasted peanuts 4 tbsp | 36g | 204.1 | 9.4 | 17.6 | 2.5 | 5.8 | 1.7 | 3.1 | 6.5 |
| Lime 1 (juice) | 30g | 9.0 | 0.2 | 0.1 | 0.0 | 3.3 | 0.5 | 0.8 | 0.6 |
| **Whole recipe** | | **1864.0** | **106.1** | **32.2** | **6.8** | **298.1** | **66.6** | **14.6** | **4325.7** |

### Peking Duck (`pekingduck`) — 6 servings

**Per serving:** 867 kcal, protein 38.1g, fat 54.0g, saturated fat 18.0g, carbs 51.0g, sugar 18.5g, fiber 1.9g, sodium 1867 mg

- ⚠️ Duck weight is the whole bird; 50% edible yield is an estimate.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Whole duck 2.25kg (50% edible) | 1125g | 3791.2 | 202.5 | 315.0 | 106.9 | 0.0 | 0.0 | 0.0 | 787.5 |
| Maltose/honey 3 tbsp | 63g | 191.5 | 0.2 | 0.0 | 0.0 | 51.7 | 51.7 | 0.0 | 2.5 |
| Rice vinegar 2 tbsp | 30g | 5.4 | 0.0 | 0.0 | 0.0 | 0.1 | 0.0 | 0.0 | 0.0 |
| Shaoxing wine 2 tbsp | 30g | 18.0 | 0.0 | 0.0 | 0.0 | 1.5 | 1.5 | 0.0 | 300.0 |
| Salt 1 tbsp | 18g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 6975.0 |
| Mandarin pancakes 12 | 300g | 870.0 | 21.0 | 6.0 | 0.9 | 180.0 | 6.0 | 6.0 | 1200.0 |
| Hoisin sauce 120ml | 120g | 264.0 | 1.8 | 2.4 | 0.4 | 57.6 | 45.6 | 2.4 | 1920.0 |
| Spring onions 4 | 60g | 19.2 | 1.1 | 0.1 | 0.0 | 4.4 | 1.4 | 1.6 | 9.6 |
| Cucumber 1 | 300g | 45.0 | 2.1 | 0.3 | 0.0 | 10.8 | 5.1 | 1.5 | 6.0 |
| **Whole recipe** | | **5204.4** | **228.7** | **323.8** | **108.1** | **306.1** | **111.2** | **11.5** | **11200.6** |

### Dim Sum (`dimsum`) — 4 servings

**Per serving:** 477 kcal, protein 27.8g, fat 11.9g, saturated fat 3.8g, carbs 63.8g, sugar 1.9g, fiber 1.2g, sodium 774 mg

- ⚠️ Chilli oil / extra soy / black vinegar to serve are unquantified and omitted.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Prawns 300g | 300g | 255.0 | 60.0 | 3.0 | 0.9 | 0.0 | 0.0 | 0.0 | 420.0 |
| Pork mince 200g | 200g | 460.0 | 34.0 | 36.0 | 13.0 | 0.0 | 0.0 | 0.0 | 120.0 |
| Wheat starch 120g | 120g | 420.0 | 0.4 | 0.1 | 0.0 | 103.2 | 0.0 | 0.0 | 0.0 |
| Tapioca starch 60g | 60g | 216.0 | 0.0 | 0.0 | 0.0 | 52.8 | 0.0 | 0.6 | 0.6 |
| Wonton wrappers 20 | 160g | 448.0 | 14.4 | 3.2 | 0.5 | 88.0 | 1.6 | 3.2 | 640.0 |
| Ginger 1 tbsp | 15g | 12.0 | 0.3 | 0.1 | 0.0 | 2.7 | 0.3 | 0.3 | 1.9 |
| Spring onions 2 | 30g | 9.6 | 0.5 | 0.1 | 0.0 | 2.2 | 0.7 | 0.8 | 4.8 |
| Soy sauce 2 tbsp | 32g | 17.0 | 1.6 | 0.0 | 0.0 | 1.6 | 0.1 | 0.1 | 1760.0 |
| Sesame oil 1 tsp | 5g | 44.2 | 0.0 | 5.0 | 0.7 | 0.0 | 0.0 | 0.0 | 0.0 |
| Sugar 1 tsp | 4g | 15.5 | 0.0 | 0.0 | 0.0 | 4.0 | 4.0 | 0.0 | 0.0 |
| Shaoxing wine 1 tbsp | 15g | 9.0 | 0.0 | 0.0 | 0.0 | 0.8 | 0.8 | 0.0 | 150.0 |
| **Whole recipe** | | **1906.2** | **111.2** | **47.5** | **15.1** | **255.2** | **7.4** | **5.0** | **3097.3** |

### Coq au Vin (`coqauvin`) — 4 servings

**Per serving:** 637 kcal, protein 47.5g, fat 31.3g, saturated fat 12.0g, carbs 16.2g, sugar 5.3g, fiber 2.2g, sodium 1665 mg

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Chicken thighs/legs, bone-in 1kg (70% edible) | 700g | 1050.0 | 154.0 | 42.0 | 12.6 | 0.0 | 0.0 | 0.0 | 525.0 |
| Red wine 500ml | 500g | 425.0 | 1.0 | 0.0 | 0.0 | 13.0 | 3.0 | 0.0 | 25.0 |
| Bacon lardons 150g | 150g | 615.0 | 19.5 | 58.5 | 21.0 | 0.8 | 0.0 | 0.0 | 2550.0 |
| Mushrooms 250g | 250g | 55.0 | 7.8 | 0.8 | 0.0 | 8.2 | 5.0 | 2.5 | 12.5 |
| Pearl onions 12 | 180g | 72.0 | 2.0 | 0.2 | 0.0 | 16.7 | 7.6 | 3.1 | 7.2 |
| Carrot 1 | 60g | 24.6 | 0.5 | 0.1 | 0.0 | 6.0 | 2.8 | 1.7 | 41.4 |
| Garlic 3 cloves | 9g | 13.4 | 0.6 | 0.0 | 0.0 | 3.0 | 0.1 | 0.2 | 1.5 |
| Chicken stock 250ml | 250g | 17.5 | 1.8 | 0.8 | 0.2 | 1.2 | 0.5 | 0.0 | 875.0 |
| Tomato paste 1 tbsp | 16g | 13.1 | 0.7 | 0.1 | 0.0 | 3.0 | 1.9 | 0.7 | 94.4 |
| Flour 2 tbsp | 16g | 58.2 | 1.6 | 0.2 | 0.0 | 12.2 | 0.0 | 0.4 | 0.3 |
| Butter 2 tbsp | 28g | 200.8 | 0.3 | 22.7 | 14.3 | 0.0 | 0.0 | 0.0 | 196.0 |
| Parsley (assumed) *(amount assumed)* | 10g | 3.6 | 0.3 | 0.1 | 0.0 | 0.6 | 0.1 | 0.3 | 5.6 |
| Salt 1 tsp (assumed) *(amount assumed)* | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| **Whole recipe** | | **2548.2** | **190.0** | **125.3** | **48.2** | **64.9** | **21.1** | **8.9** | **6658.9** |

### Bouillabaisse (`bouillabaisse`) — 6 servings

**Per serving:** 422 kcal, protein 46.6g, fat 13.7g, saturated fat 2.0g, carbs 29.1g, sugar 7.0g, fiber 3.7g, sodium 1242 mg

- ⚠️ Rouille to serve is unquantified and omitted.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Mixed firm white fish 800g | 800g | 656.0 | 144.0 | 5.6 | 0.8 | 0.0 | 0.0 | 0.0 | 432.0 |
| Prawns 300g | 300g | 255.0 | 60.0 | 3.0 | 0.9 | 0.0 | 0.0 | 0.0 | 420.0 |
| Mussels 300g | 300g | 258.0 | 36.0 | 6.6 | 1.2 | 11.1 | 0.0 | 0.0 | 870.0 |
| Fish stock 1.5 litres | 1500g | 90.0 | 12.0 | 3.0 | 0.0 | 6.0 | 0.0 | 0.0 | 4500.0 |
| Tomatoes 400g | 400g | 72.0 | 3.6 | 0.8 | 0.0 | 15.6 | 10.4 | 4.8 | 20.0 |
| Tomato paste 2 tbsp | 32g | 26.2 | 1.4 | 0.2 | 0.0 | 6.1 | 3.8 | 1.3 | 188.8 |
| Fennel 1 bulb | 200g | 62.0 | 2.4 | 0.4 | 0.0 | 14.6 | 7.8 | 6.2 | 104.0 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Leek 1 | 90g | 54.9 | 1.4 | 0.3 | 0.0 | 12.6 | 3.5 | 1.6 | 18.0 |
| Garlic 4 cloves | 12g | 17.9 | 0.8 | 0.1 | 0.0 | 4.0 | 0.1 | 0.3 | 2.0 |
| Olive oil 4 tbsp | 56g | 495.0 | 0.0 | 56.0 | 7.8 | 0.0 | 0.0 | 0.0 | 1.1 |
| Crusty bread 1 slice/serving (assumed) *(amount assumed)* | 180g | 477.0 | 16.2 | 5.8 | 1.3 | 88.2 | 9.0 | 4.9 | 882.0 |
| Parsley (assumed) *(amount assumed)* | 10g | 3.6 | 0.3 | 0.1 | 0.0 | 0.6 | 0.1 | 0.3 | 5.6 |
| Lemon juice (assumed) *(amount assumed)* | 30g | 6.6 | 0.1 | 0.1 | 0.0 | 2.1 | 0.8 | 0.1 | 0.3 |
| **Whole recipe** | | **2534.3** | **279.8** | **81.9** | **12.1** | **174.8** | **41.8** | **22.0** | **7449.9** |

### Seafood Paella (`paella`) — 6 servings

**Per serving:** 491 kcal, protein 29.0g, fat 12.5g, saturated fat 2.1g, carbs 64.1g, sugar 4.4g, fiber 3.0g, sodium 821 mg

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Bomba rice 400g | 400g | 1440.0 | 28.0 | 2.4 | 0.8 | 312.0 | 0.0 | 4.0 | 20.0 |
| Prawns 300g | 300g | 255.0 | 60.0 | 3.0 | 0.9 | 0.0 | 0.0 | 0.0 | 420.0 |
| Mussels 300g | 300g | 258.0 | 36.0 | 6.6 | 1.2 | 11.1 | 0.0 | 0.0 | 870.0 |
| Squid rings 200g | 200g | 184.0 | 32.0 | 2.8 | 0.8 | 6.2 | 0.0 | 0.0 | 88.0 |
| Chicken/fish stock 1 litre | 1000g | 70.0 | 7.0 | 3.0 | 1.0 | 5.0 | 2.0 | 0.0 | 3500.0 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Red pepper 1 | 120g | 37.2 | 1.2 | 0.4 | 0.0 | 7.2 | 5.0 | 2.5 | 4.8 |
| Garlic 3 cloves | 9g | 13.4 | 0.6 | 0.0 | 0.0 | 3.0 | 0.1 | 0.2 | 1.5 |
| Tomatoes 2, grated | 240g | 43.2 | 2.2 | 0.5 | 0.0 | 9.4 | 6.2 | 2.9 | 12.0 |
| Olive oil 4 tbsp | 56g | 495.0 | 0.0 | 56.0 | 7.8 | 0.0 | 0.0 | 0.0 | 1.1 |
| Lemon 1 (juice) | 30g | 6.6 | 0.1 | 0.1 | 0.0 | 2.1 | 0.8 | 0.1 | 0.3 |
| Peas 100g | 100g | 84.0 | 5.4 | 0.4 | 0.1 | 15.0 | 5.7 | 5.5 | 2.0 |
| **Whole recipe** | | **2946.4** | **174.1** | **75.3** | **12.6** | **384.9** | **26.1** | **17.7** | **4925.8** |

### Beef Pho (`beefpho`) — 6 servings

**Per serving:** 524 kcal, protein 22.7g, fat 12.2g, saturated fat 4.7g, carbs 78.1g, sugar 5.4g, fiber 2.8g, sodium 893 mg

- ⚠️ Beef bones 1.5kg are NOT counted (broth extraction unquantified); the broth is represented only by the fish sauce and noodles.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Beef brisket/shin 500g | 500g | 1080.0 | 100.0 | 70.0 | 27.5 | 0.0 | 0.0 | 0.0 | 350.0 |
| Rice noodles 500g | 500g | 1800.0 | 25.0 | 2.5 | 0.5 | 410.0 | 0.0 | 7.5 | 75.0 |
| Onion 2 | 300g | 120.0 | 3.3 | 0.3 | 0.0 | 27.9 | 12.6 | 5.1 | 12.0 |
| Ginger 1 large piece (assumed) *(amount assumed)* | 30g | 24.0 | 0.5 | 0.2 | 0.1 | 5.4 | 0.5 | 0.6 | 3.9 |
| Fish sauce 4 tbsp | 72g | 25.2 | 3.7 | 0.0 | 0.0 | 2.6 | 2.6 | 0.0 | 4896.0 |
| Rock sugar 1 tbsp | 12g | 46.4 | 0.0 | 0.0 | 0.0 | 12.0 | 12.0 | 0.0 | 0.0 |
| Bean sprouts to serve (assumed) *(amount assumed)* | 100g | 30.0 | 3.0 | 0.2 | 0.0 | 6.0 | 4.0 | 1.8 | 6.0 |
| Fresh coriander to serve (assumed) *(amount assumed)* | 30g | 6.9 | 0.6 | 0.1 | 0.0 | 1.1 | 0.3 | 0.8 | 13.8 |
| Lime juice to serve (assumed) *(amount assumed)* | 30g | 9.0 | 0.2 | 0.1 | 0.0 | 3.3 | 0.5 | 0.8 | 0.6 |
| **Whole recipe** | | **3141.5** | **136.4** | **73.5** | **28.1** | **468.3** | **32.5** | **16.7** | **5357.3** |

### Poutine (`poutine`) — 4 servings

**Per serving:** 583 kcal, protein 20.7g, fat 34.3g, saturated fat 16.3g, carbs 48.3g, sugar 3.1g, fiber 5.7g, sodium 1540 mg

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Potatoes 1kg | 1000g | 770.0 | 20.0 | 1.0 | 0.0 | 170.0 | 8.0 | 22.0 | 60.0 |
| Cheese curds 250g | 250g | 875.0 | 55.0 | 70.0 | 45.0 | 5.0 | 2.5 | 0.0 | 1500.0 |
| Beef stock 500ml | 500g | 40.0 | 5.0 | 1.5 | 0.5 | 2.5 | 1.0 | 0.0 | 1750.0 |
| Butter 2 tbsp | 28g | 200.8 | 0.3 | 22.7 | 14.3 | 0.0 | 0.0 | 0.0 | 196.0 |
| Flour 2 tbsp | 16g | 58.2 | 1.6 | 0.2 | 0.0 | 12.2 | 0.0 | 0.4 | 0.3 |
| Soy sauce 1 tsp | 5g | 2.7 | 0.2 | 0.0 | 0.0 | 0.2 | 0.0 | 0.0 | 275.0 |
| Worcestershire sauce 1 tsp | 5g | 3.9 | 0.0 | 0.0 | 0.0 | 1.0 | 0.5 | 0.0 | 50.0 |
| Garlic 1 clove | 3g | 4.5 | 0.2 | 0.0 | 0.0 | 1.0 | 0.0 | 0.1 | 0.5 |
| Oil for deep frying (absorbed, assumed) *(amount assumed)* | 42g | 371.3 | 0.0 | 42.0 | 5.5 | 0.0 | 0.0 | 0.0 | 0.0 |
| Salt 1 tsp (assumed) *(amount assumed)* | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| Spring onions to serve (assumed) *(amount assumed)* | 15g | 4.8 | 0.3 | 0.0 | 0.0 | 1.1 | 0.3 | 0.4 | 2.4 |
| **Whole recipe** | | **2331.1** | **82.6** | **137.4** | **65.3** | **193.0** | **12.5** | **22.9** | **6159.2** |

### Bobotie (`bobotie`) — 6 servings

**Per serving:** 435 kcal, protein 30.7g, fat 24.7g, saturated fat 9.0g, carbs 22.9g, sugar 12.6g, fiber 2.4g, sodium 598 mg

- ⚠️ "Beef or lamb" mince is computed as beef; lamb would be slightly higher in fat.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Beef/lamb mince 750g (computed as beef) | 750g | 1612.5 | 142.5 | 112.5 | 43.5 | 0.0 | 0.0 | 0.0 | 525.0 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Garlic 2 cloves | 6g | 8.9 | 0.4 | 0.0 | 0.0 | 2.0 | 0.1 | 0.1 | 1.0 |
| Ginger 1 tsp | 5g | 4.0 | 0.1 | 0.0 | 0.0 | 0.9 | 0.1 | 0.1 | 0.7 |
| Curry powder 2 tbsp (+ turmeric, folded in) | 14g | 42.0 | 1.4 | 1.4 | 0.1 | 7.7 | 0.7 | 3.5 | 14.0 |
| White bread 2 slices | 60g | 159.0 | 5.4 | 1.9 | 0.4 | 29.4 | 3.0 | 1.6 | 294.0 |
| Milk 250ml | 250g | 152.5 | 8.0 | 8.2 | 4.8 | 12.0 | 12.8 | 0.0 | 110.0 |
| Eggs 3 | 150g | 214.5 | 18.9 | 14.2 | 4.7 | 1.0 | 0.6 | 0.0 | 213.0 |
| Chutney 3 tbsp | 45g | 67.5 | 0.2 | 0.2 | 0.0 | 17.1 | 13.5 | 0.9 | 90.0 |
| Raisins 3 tbsp | 45g | 134.6 | 1.4 | 0.2 | 0.0 | 35.6 | 26.6 | 1.7 | 5.0 |
| Dried apricots 4 | 20g | 48.2 | 0.7 | 0.1 | 0.0 | 12.6 | 10.6 | 1.5 | 2.0 |
| Lemon juice 1 tbsp | 15g | 3.3 | 0.1 | 0.0 | 0.0 | 1.1 | 0.4 | 0.0 | 0.1 |
| Almonds 2 tbsp | 18g | 104.2 | 3.8 | 9.0 | 0.7 | 4.0 | 0.8 | 2.2 | 0.2 |
| Salt 1 tsp (assumed) *(amount assumed)* | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| **Whole recipe** | | **2611.2** | **184.4** | **148.1** | **54.2** | **137.2** | **75.3** | **14.1** | **3586.0** |

### Moussaka (`moussaka`) — 6 servings

**Per serving:** 569 kcal, protein 34.2g, fat 30.6g, saturated fat 14.6g, carbs 40.7g, sugar 13.7g, fiber 8.1g, sodium 433 mg

- ⚠️ No added salt is listed, so sodium comes only from butter, cheese and milk and is understated.
- ⚠️ "Lamb or beef" mince is computed as beef.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Aubergines 2 large | 900g | 225.0 | 9.0 | 1.8 | 0.0 | 53.1 | 31.5 | 27.0 | 18.0 |
| Potatoes 3 | 510g | 392.7 | 10.2 | 0.5 | 0.0 | 86.7 | 4.1 | 11.2 | 30.6 |
| Lamb/beef mince 600g (computed as beef) | 600g | 1290.0 | 114.0 | 90.0 | 34.8 | 0.0 | 0.0 | 0.0 | 420.0 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Garlic 3 cloves | 9g | 13.4 | 0.6 | 0.0 | 0.0 | 3.0 | 0.1 | 0.2 | 1.5 |
| Tomatoes 400g | 400g | 72.0 | 3.6 | 0.8 | 0.0 | 15.6 | 10.4 | 4.8 | 20.0 |
| Tomato paste 2 tbsp | 32g | 26.2 | 1.4 | 0.2 | 0.0 | 6.1 | 3.8 | 1.3 | 188.8 |
| Milk 500ml | 500g | 305.0 | 16.0 | 16.5 | 9.5 | 24.0 | 25.5 | 0.0 | 220.0 |
| Butter 50g | 50g | 358.5 | 0.5 | 40.5 | 25.5 | 0.1 | 0.1 | 0.0 | 350.0 |
| Flour 50g | 50g | 182.0 | 5.2 | 0.5 | 0.1 | 38.1 | 0.1 | 1.4 | 1.0 |
| Eggs 2 | 100g | 143.0 | 12.6 | 9.5 | 3.1 | 0.7 | 0.4 | 0.0 | 142.0 |
| Cheese 80g (parmesan proxy) | 80g | 344.0 | 30.4 | 23.2 | 14.4 | 3.2 | 0.0 | 0.0 | 1200.0 |
| **Whole recipe** | | **3411.8** | **205.0** | **183.7** | **87.4** | **244.5** | **82.3** | **48.5** | **2597.9** |

### Hummus (`hummus`) — 6 servings

**Per serving:** 273 kcal, protein 9.4g, fat 17.2g, saturated fat 2.5g, carbs 23.3g, sugar 3.5g, fiber 7.0g, sodium 396 mg

- ⚠️ Warm pitta bread to serve is unquantified and omitted.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Chickpeas, cooked 400g | 400g | 656.0 | 35.6 | 10.4 | 1.2 | 109.6 | 19.2 | 30.4 | 28.0 |
| Tahini 120g | 120g | 714.0 | 20.4 | 64.8 | 9.6 | 25.2 | 0.4 | 10.8 | 14.4 |
| Lemon juice 3 tbsp | 45g | 9.9 | 0.2 | 0.1 | 0.0 | 3.1 | 1.1 | 0.1 | 0.5 |
| Garlic 1 small clove | 3g | 4.5 | 0.2 | 0.0 | 0.0 | 1.0 | 0.0 | 0.1 | 0.5 |
| Olive oil 2 tbsp | 28g | 247.5 | 0.0 | 28.0 | 3.9 | 0.0 | 0.0 | 0.0 | 0.6 |
| Salt 1 tsp | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| Parsley (assumed) *(amount assumed)* | 10g | 3.6 | 0.3 | 0.1 | 0.0 | 0.6 | 0.1 | 0.3 | 5.6 |
| **Whole recipe** | | **1635.5** | **56.7** | **103.4** | **14.7** | **139.6** | **20.8** | **41.7** | **2374.5** |

### Falafel (`falafel`) — 4 servings

**Per serving:** 364 kcal, protein 13.6g, fat 14.7g, saturated fat 1.8g, carbs 47.1g, sugar 8.7g, fiber 12.2g, sodium 674 mg

- ⚠️ Pitta, salad and tahini sauce to serve are unquantified and omitted.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Dried chickpeas 250g, soaked | 250g | 910.0 | 47.5 | 15.0 | 1.8 | 152.5 | 27.5 | 42.5 | 60.0 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Garlic 3 cloves | 9g | 13.4 | 0.6 | 0.0 | 0.0 | 3.0 | 0.1 | 0.2 | 1.5 |
| Parsley 1 large bunch (assumed) *(amount assumed)* | 60g | 21.6 | 1.8 | 0.5 | 0.1 | 3.8 | 0.5 | 2.0 | 33.6 |
| Coriander 1 bunch (assumed) *(amount assumed)* | 30g | 6.9 | 0.6 | 0.1 | 0.0 | 1.1 | 0.3 | 0.8 | 13.8 |
| Cumin 2 tsp | 4g | 15.0 | 0.7 | 0.9 | 0.1 | 1.8 | 0.1 | 0.4 | 6.7 |
| Baking powder 1/2 tsp | 2.5g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 250.0 |
| Flour 2 tbsp | 16g | 58.2 | 1.6 | 0.2 | 0.0 | 12.2 | 0.0 | 0.4 | 0.3 |
| Salt 1 tsp | 6g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2325.0 |
| Oil for deep frying (absorbed, assumed) *(amount assumed)* | 42g | 371.3 | 0.0 | 42.0 | 5.5 | 0.0 | 0.0 | 0.0 | 0.0 |
| **Whole recipe** | | **1456.4** | **54.5** | **58.9** | **7.4** | **188.3** | **34.8** | **48.9** | **2697.0** |

### Feijoada (`feijoada`) — 8 servings

**Per serving:** 580 kcal, protein 32.3g, fat 31.3g, saturated fat 10.8g, carbs 43.9g, sugar 4.0g, fiber 10.4g, sodium 842 mg

- ⚠️ Rice, collard greens and farofa to serve are unquantified and omitted; no added salt is listed, so sodium comes only from the cured meats and is understated.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Dried black beans 500g | 500g | 1705.0 | 108.0 | 7.0 | 1.5 | 312.0 | 10.5 | 77.5 | 25.0 |
| Pork shoulder 500g | 500g | 1100.0 | 85.0 | 85.0 | 30.0 | 0.0 | 0.0 | 0.0 | 300.0 |
| Smoked sausage 300g | 300g | 900.0 | 42.0 | 78.0 | 27.0 | 6.0 | 3.0 | 0.0 | 3000.0 |
| Salt pork 200g | 200g | 800.0 | 20.0 | 80.0 | 28.0 | 0.0 | 0.0 | 0.0 | 3400.0 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Garlic 4 cloves | 12g | 17.9 | 0.8 | 0.1 | 0.0 | 4.0 | 0.1 | 0.3 | 2.0 |
| Orange 1 | 130g | 61.1 | 1.2 | 0.1 | 0.0 | 15.6 | 12.2 | 3.1 | 0.0 |
| **Whole recipe** | | **4644.0** | **258.6** | **250.3** | **86.5** | **351.5** | **32.1** | **83.4** | **6733.0** |

### Aussie Meat Pie (`meatpie`) — 6 servings

**Per serving:** 525 kcal, protein 29.1g, fat 31.4g, saturated fat 14.2g, carbs 28.3g, sugar 4.5g, fiber 1.7g, sodium 673 mg

- ⚠️ Pastry weight is an estimate (270g total for 6 pies); no added salt is listed, so sodium comes only from stock, sauces and Vegemite and is understated.

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Beef chuck 700g | 700g | 1505.0 | 140.0 | 98.0 | 38.5 | 0.0 | 0.0 | 0.0 | 490.0 |
| Onion 1 | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Garlic 2 cloves | 6g | 8.9 | 0.4 | 0.0 | 0.0 | 2.0 | 0.1 | 0.1 | 1.0 |
| Tomato paste 2 tbsp | 32g | 26.2 | 1.4 | 0.2 | 0.0 | 6.1 | 3.8 | 1.3 | 188.8 |
| Beef stock 400ml | 400g | 32.0 | 4.0 | 1.2 | 0.4 | 2.0 | 0.8 | 0.0 | 1400.0 |
| Worcestershire sauce 2 tbsp | 30g | 23.4 | 0.0 | 0.0 | 0.0 | 5.7 | 3.0 | 0.0 | 300.0 |
| Vegemite 1 tsp | 5g | 9.5 | 1.2 | 0.1 | 0.0 | 1.0 | 0.1 | 0.0 | 165.0 |
| Flour 2 tbsp | 16g | 58.2 | 1.6 | 0.2 | 0.0 | 12.2 | 0.0 | 0.4 | 0.3 |
| Shortcrust pastry (estimated) *(amount estimated)* | 135g | 567.0 | 8.1 | 35.1 | 20.2 | 54.0 | 1.4 | 2.7 | 472.5 |
| Puff pastry (estimated) *(amount estimated)* | 135g | 742.5 | 9.5 | 48.6 | 24.3 | 60.8 | 1.4 | 2.7 | 540.0 |
| Egg 1, for glazing | 50g | 71.5 | 6.3 | 4.8 | 1.6 | 0.3 | 0.2 | 0.0 | 71.0 |
| Tomato sauce to serve 3 tbsp (assumed) *(amount assumed)* | 45g | 45.0 | 0.7 | 0.1 | 0.0 | 11.7 | 9.9 | 0.1 | 405.0 |
| **Whole recipe** | | **3149.3** | **174.8** | **188.3** | **85.1** | **169.7** | **26.9** | **10.0** | **4039.6** |

### Haleem (`haleem`) — 8 servings

**Per serving:** 951 kcal, protein 46.8g, fat 59.5g, saturated fat 31.3g, carbs 58.6g, sugar 6.7g, fiber 12.3g, sodium 1865 mg

- ⚠️ Beef bones 250g are NOT counted (broth extraction unquantified).

| Ingredient | Amount | kcal | Protein g | Fat g | Sat fat g | Carbs g | Sugar g | Fiber g | Sodium mg |
|---|---|---|---|---|---|---|---|---|---|
| Whole wheat berries 1 cup | 190g | 646.0 | 24.7 | 4.8 | 0.8 | 136.8 | 0.8 | 20.9 | 3.8 |
| Barley 1/2 cup | 92g | 325.7 | 11.5 | 2.1 | 0.4 | 67.2 | 0.7 | 15.6 | 8.3 |
| Chana daal 1/2 cup dry | 96g | 345.6 | 19.2 | 5.8 | 0.7 | 57.6 | 9.6 | 16.3 | 19.2 |
| Masoor daal 1/4 cup dry | 48g | 169.0 | 11.8 | 0.5 | 0.1 | 30.4 | 1.0 | 5.1 | 2.9 |
| Moong daal 1/4 cup dry | 48g | 163.2 | 11.5 | 0.6 | 0.1 | 29.8 | 1.0 | 7.7 | 7.2 |
| Mash daal 1/4 cup dry | 48g | 163.2 | 11.5 | 0.6 | 0.1 | 29.8 | 1.0 | 7.7 | 7.2 |
| Beef 1kg | 1000g | 2400.0 | 260.0 | 140.0 | 58.0 | 0.0 | 0.0 | 0.0 | 700.0 |
| Ghee 1 cup | 205g | 1845.0 | 0.0 | 205.0 | 123.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Onions 2 large | 300g | 120.0 | 3.3 | 0.3 | 0.0 | 27.9 | 12.6 | 5.1 | 12.0 |
| Ginger paste 2 tbsp | 30g | 24.0 | 0.5 | 0.2 | 0.1 | 5.4 | 0.5 | 0.6 | 3.9 |
| Garlic paste 2 tbsp | 30g | 44.7 | 1.9 | 0.1 | 0.0 | 9.9 | 0.3 | 0.6 | 5.1 |
| Yoghurt 1 cup | 245g | 149.5 | 8.6 | 8.1 | 5.1 | 11.5 | 11.5 | 0.0 | 112.7 |
| Red chilli powder 2 tbsp | 14g | 42.0 | 1.4 | 1.4 | 0.1 | 7.7 | 0.7 | 3.5 | 14.0 |
| Kashmiri chilli powder 1 tbsp | 7g | 21.0 | 0.7 | 0.7 | 0.1 | 3.9 | 0.4 | 1.8 | 7.0 |
| Coriander powder 1.5 tbsp | 10g | 30.0 | 1.0 | 1.0 | 0.1 | 5.5 | 0.5 | 2.5 | 10.0 |
| Haleem masala 2 tbsp | 14g | 42.0 | 1.4 | 1.4 | 0.1 | 7.7 | 0.7 | 3.5 | 14.0 |
| Cumin seeds 1 tbsp | 7g | 21.0 | 0.7 | 0.7 | 0.1 | 3.9 | 0.4 | 1.8 | 7.0 |
| Salt 2 tbsp | 36g | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 13950.0 |
| Ghee 1/2 cup (tarka) | 102g | 918.0 | 0.0 | 102.0 | 61.2 | 0.0 | 0.0 | 0.0 | 0.0 |
| Onion 1 medium (tarka) | 150g | 60.0 | 1.7 | 0.2 | 0.0 | 14.0 | 6.3 | 2.5 | 6.0 |
| Ginger julienne 2 tbsp | 30g | 24.0 | 0.5 | 0.2 | 0.1 | 5.4 | 0.5 | 0.6 | 3.9 |
| Fresh coriander 1/2 cup | 30g | 6.9 | 0.6 | 0.1 | 0.0 | 1.1 | 0.3 | 0.8 | 13.8 |
| Fresh mint 1/2 cup | 15g | 6.6 | 0.5 | 0.1 | 0.0 | 1.3 | 0.0 | 0.8 | 4.5 |
| Green chillies 4 | 60g | 24.0 | 1.2 | 0.1 | 0.0 | 5.7 | 3.0 | 0.9 | 4.2 |
| Lemons 3 (juice) | 90g | 19.8 | 0.4 | 0.2 | 0.0 | 6.3 | 2.2 | 0.3 | 0.9 |
| **Whole recipe** | | **7611.1** | **374.7** | **476.2** | **250.2** | **468.5** | **53.8** | **98.6** | **14917.6** |

## USDA per-100g values used

(kcal, protein g, fat g, saturated fat g, carbs g, sugar g, fiber g, sodium mg)

- `chicken_blend`: (150, 22.0, 6.0, 1.8, 0, 0, 0, 75)
- `chicken_breast`: (120, 22.5, 2.6, 0.6, 0, 0, 0, 74)
- `beef_stew`: (240, 26.0, 14.0, 5.8, 0, 0, 0, 70)
- `beef_mince`: (215, 19.0, 15.0, 5.8, 0, 0, 0, 70)
- `beef_brisket`: (216, 20.0, 14.0, 5.5, 0, 0, 0, 70)
- `beef_chuck`: (215, 20.0, 14.0, 5.5, 0, 0, 0, 70)
- `pork_shoulder`: (220, 17.0, 17.0, 6.0, 0, 0, 0, 60)
- `pork_mince`: (230, 17.0, 18.0, 6.5, 0, 0, 0, 60)
- `duck`: (337, 18.0, 28.0, 9.5, 0, 0, 0, 70)
- `prawn`: (85, 20.0, 1.0, 0.3, 0, 0, 0, 140)
- `salmon`: (208, 20.0, 13.0, 3.0, 0, 0, 0, 60)
- `whitefish`: (82, 18.0, 0.7, 0.1, 0, 0, 0, 54)
- `mussel`: (86, 12.0, 2.2, 0.4, 3.7, 0, 0, 290)
- `squid`: (92, 16.0, 1.4, 0.4, 3.1, 0, 0, 44)
- `egg`: (143, 12.6, 9.5, 3.1, 0.7, 0.4, 0, 142)
- `yolk`: (322, 16.0, 27.0, 10.0, 3.6, 0.2, 0, 48)
- `bacon`: (410, 13.0, 39.0, 14.0, 0.5, 0, 0, 1700)
- `guanciale`: (450, 12.0, 44.0, 16.0, 1.0, 0, 0, 1500)
- `sausage_smoked`: (300, 14.0, 26.0, 9.0, 2.0, 1.0, 0, 1000)
- `saltpork`: (400, 10.0, 40.0, 14.0, 0, 0, 0, 1700)
- `mozzarella`: (299, 22.0, 22.0, 13.0, 2.0, 1.0, 0, 630)
- `pecorino`: (387, 32.0, 27.0, 17.0, 4.0, 0, 0, 1200)
- `parmesan`: (430, 38.0, 29.0, 18.0, 4.0, 0, 0, 1500)
- `curds`: (350, 22.0, 28.0, 18.0, 2.0, 1.0, 0, 600)
- `khoya`: (400, 12.0, 28.0, 18.0, 28.0, 25.0, 0, 100)
- `yoghurt`: (61, 3.5, 3.3, 2.1, 4.7, 4.7, 0, 46)
- `milk`: (61, 3.2, 3.3, 1.9, 4.8, 5.1, 0, 44)
- `butter`: (717, 0.9, 81.0, 51.0, 0.1, 0.1, 0, 700)
- `ghee`: (900, 0, 100.0, 60.0, 0, 0, 0, 0)
- `olive_oil`: (884, 0, 100.0, 14.0, 0, 0, 0, 2)
- `veg_oil`: (884, 0, 100.0, 13.0, 0, 0, 0, 0)
- `sesame_oil`: (884, 0, 100.0, 14.0, 0, 0, 0, 0)
- `basmati`: (360, 7.0, 0.6, 0.2, 78.0, 0, 1.0, 5)
- `sushi_rice`: (360, 6.5, 0.5, 0.1, 79.0, 0, 0.5, 1)
- `bomba`: (360, 7.0, 0.6, 0.2, 78.0, 0, 1.0, 5)
- `flour`: (364, 10.3, 1.0, 0.2, 76.3, 0.3, 2.7, 2)
- `wholewheat_flour`: (339, 13.0, 2.5, 0.4, 72.0, 0.4, 11.0, 5)
- `semolina`: (360, 12.7, 1.1, 0.2, 73.0, 0, 3.9, 1)
- `maize_flour`: (360, 9.0, 3.5, 0.5, 72.0, 0.6, 7.0, 5)
- `wheat_starch`: (350, 0.3, 0.1, 0, 86.0, 0, 0, 0)
- `tapioca`: (360, 0, 0, 0, 88.0, 0, 1.0, 1)
- `spaghetti`: (371, 13.0, 1.5, 0.3, 75.0, 2.7, 3.2, 6)
- `ramen_noodle`: (370, 10.0, 2.0, 0.5, 75.0, 1.0, 3.0, 800)
- `rice_noodle`: (360, 5.0, 0.5, 0.1, 82.0, 0, 1.5, 15)
- `lentil_dry`: (352, 24.6, 1.1, 0.2, 63.4, 2.0, 10.7, 6)
- `chickpea_cooked`: (164, 8.9, 2.6, 0.3, 27.4, 4.8, 7.6, 7)
- `chickpea_dry`: (364, 19.0, 6.0, 0.7, 61.0, 11.0, 17.0, 24)
- `blackbean_dry`: (341, 21.6, 1.4, 0.3, 62.4, 2.1, 15.5, 5)
- `chana_dry`: (360, 20.0, 6.0, 0.7, 60.0, 10.0, 17.0, 20)
- `moong_dry`: (340, 24.0, 1.2, 0.3, 62.0, 2.0, 16.0, 15)
- `wheatberry`: (340, 13.0, 2.5, 0.4, 72.0, 0.4, 11.0, 2)
- `barley`: (354, 12.5, 2.3, 0.4, 73.0, 0.8, 17.0, 9)
- `sugar`: (387, 0, 0, 0, 100.0, 100.0, 0, 0)
- `brownsugar`: (380, 0, 0, 0, 97.0, 97.0, 0, 40)
- `honey`: (304, 0.3, 0, 0, 82.0, 82.0, 0, 4)
- `maltose`: (380, 0, 0, 0, 95.0, 95.0, 0, 0)
- `rocksugar`: (387, 0, 0, 0, 100.0, 100.0, 0, 0)
- `potato`: (77, 2.0, 0.1, 0, 17.0, 0.8, 2.2, 6)
- `carrot`: (41, 0.9, 0.2, 0, 10.0, 4.7, 2.8, 69)
- `onion`: (40, 1.1, 0.1, 0, 9.3, 4.2, 1.7, 4)
- `tomato`: (18, 0.9, 0.2, 0, 3.9, 2.6, 1.2, 5)
- `tomato_paste`: (82, 4.3, 0.5, 0.1, 19.0, 12.0, 4.2, 590)
- `peas`: (84, 5.4, 0.4, 0.1, 15.0, 5.7, 5.5, 2)
- `cabbage`: (25, 1.3, 0.1, 0, 5.8, 3.2, 2.5, 18)
- `mushroom`: (22, 3.1, 0.3, 0, 3.3, 2.0, 1.0, 5)
- `aubergine`: (25, 1.0, 0.2, 0, 5.9, 3.5, 3.0, 2)
- `redpepper`: (31, 1.0, 0.3, 0, 6.0, 4.2, 2.1, 4)
- `cucumber`: (15, 0.7, 0.1, 0, 3.6, 1.7, 0.5, 2)
- `mango`: (60, 0.8, 0.4, 0.1, 15.0, 14.0, 1.6, 1)
- `pineapple`: (50, 0.5, 0.1, 0, 13.0, 10.0, 1.4, 1)
- `lemonjuice`: (22, 0.4, 0.2, 0, 7.0, 2.5, 0.3, 1)
- `limejuice`: (30, 0.7, 0.2, 0, 11.0, 1.7, 2.8, 2)
- `orange`: (47, 0.9, 0.1, 0, 12.0, 9.4, 2.4, 0)
- `peanut`: (567, 26.0, 49.0, 7.0, 16.0, 4.7, 8.5, 18)
- `almond`: (579, 21.0, 50.0, 3.8, 22.0, 4.4, 12.0, 1)
- `tahini`: (595, 17.0, 54.0, 8.0, 21.0, 0.3, 9.0, 12)
- `sesame`: (573, 18.0, 50.0, 7.0, 23.0, 0.3, 12.0, 11)
- `tortilla`: (218, 5.7, 2.9, 0.4, 44.0, 0.8, 6.3, 44)
- `bread_white`: (265, 9.0, 3.2, 0.7, 49.0, 5.0, 2.7, 490)
- `bun`: (290, 9.0, 5.0, 1.0, 52.0, 6.0, 2.5, 450)
- `pitta`: (280, 9.0, 2.0, 0.3, 56.0, 1.0, 2.0, 500)
- `pancake`: (290, 7.0, 2.0, 0.3, 60.0, 2.0, 2.0, 400)
- `wonton`: (280, 9.0, 2.0, 0.3, 55.0, 1.0, 2.0, 400)
- `shortcrust`: (420, 6.0, 26.0, 15.0, 40.0, 1.0, 2.0, 350)
- `puff`: (550, 7.0, 36.0, 18.0, 45.0, 1.0, 2.0, 400)
- `hoisin`: (220, 1.5, 2.0, 0.3, 48.0, 38.0, 2.0, 1600)
- `soy`: (53, 5.0, 0, 0, 5.0, 0.4, 0.3, 5500)
- `fishsauce`: (35, 5.1, 0, 0, 3.6, 3.6, 0, 6800)
- `sriracha`: (100, 1.0, 1.0, 0, 20.0, 16.0, 1.0, 1800)
- `mayo`: (680, 1.0, 75.0, 11.0, 1.0, 1.0, 0, 635)
- `miso`: (200, 12.0, 6.0, 1.0, 26.0, 6.0, 5.0, 3700)
- `tamarind`: (240, 3.0, 0.6, 0.1, 62.0, 38.0, 5.0, 30)
- `ketchup`: (100, 1.5, 0.2, 0, 26.0, 22.0, 0.3, 900)
- `worcester`: (78, 0, 0, 0, 19.0, 10.0, 0, 1000)
- `vegemite`: (190, 25.0, 1.0, 0, 20.0, 2.0, 0, 3300)
- `chutney_sweet`: (150, 0.5, 0.5, 0, 38.0, 30.0, 2.0, 200)
- `chutney_green`: (60, 2.0, 3.0, 0.5, 6.0, 3.0, 2.0, 300)
- `sprouts`: (30, 3.0, 0.2, 0, 6.0, 4.0, 1.8, 6)
- `hominy`: (72, 1.5, 0.7, 0.1, 14.0, 0.5, 2.0, 250)
- `redwine`: (85, 0.2, 0, 0, 2.6, 0.6, 0, 5)
- `shaoxing`: (60, 0, 0, 0, 5.0, 5.0, 0, 1000)
- `ricevinegar`: (18, 0, 0, 0, 0.4, 0, 0, 0)
- `vinegar`: (18, 0, 0, 0, 0.1, 0, 0, 0)
- `orangejuice`: (45, 0.7, 0.2, 0, 10.0, 8.4, 0.2, 1)
- `stock_chicken`: (7, 0.7, 0.3, 0.1, 0.5, 0.2, 0, 350)
- `stock_beef`: (8, 1.0, 0.3, 0.1, 0.5, 0.2, 0, 350)
- `stock_fish`: (6, 0.8, 0.2, 0, 0.4, 0, 0, 300)
- `garlic`: (149, 6.4, 0.5, 0.1, 33.0, 1.0, 2.1, 17)
- `ginger`: (80, 1.8, 0.8, 0.2, 18.0, 1.7, 2.0, 13)
- `springonion`: (32, 1.8, 0.2, 0, 7.3, 2.3, 2.6, 16)
- `coriander`: (23, 2.1, 0.5, 0, 3.7, 0.9, 2.8, 46)
- `mint`: (44, 3.3, 0.7, 0.2, 8.4, 0, 5.0, 30)
- `basil`: (23, 3.2, 0.6, 0.1, 2.7, 0.3, 1.6, 4)
- `parsley`: (36, 3.0, 0.8, 0.1, 6.3, 0.9, 3.3, 56)
- `radish`: (16, 0.7, 0.1, 0, 3.4, 1.9, 1.6, 39)
- `leek`: (61, 1.5, 0.3, 0, 14.0, 3.9, 1.8, 20)
- `fennel`: (31, 1.2, 0.2, 0, 7.3, 3.9, 3.1, 52)
- `greenchilli`: (40, 2.0, 0.2, 0, 9.5, 5.0, 1.5, 7)
- `driedchilli`: (280, 10.0, 14.0, 2.0, 50.0, 10.0, 28.0, 100)
- `blackpepper`: (250, 10.0, 3.0, 1.0, 64.0, 0.6, 26.0, 20)
- `cumin`: (375, 18.0, 22.0, 1.5, 44.0, 2.2, 10.5, 168)
- `pomegranate`: (83, 1.7, 1.2, 0.1, 19.0, 14.0, 4.0, 3)
- `raisin`: (299, 3.0, 0.5, 0.1, 79.0, 59.0, 3.7, 11)
- `apricot_dried`: (241, 3.4, 0.5, 0, 63.0, 53.0, 7.3, 10)
- `spice_mix`: (300, 10.0, 10.0, 1.0, 55.0, 5.0, 25.0, 100)
- `salt`: (0, 0, 0, 0, 0, 0, 0, 38750)
- `bakingpowder`: (0, 0, 0, 0, 0, 0, 0, 10000)
- `yeast`: (325, 40.0, 8.0, 1.0, 41.0, 0, 27.0, 50)
- `nori`: (350, 40.0, 2.0, 0.5, 44.0, 0, 35.0, 2000)
- `shami_kebab`: (220, 20.0, 13.0, 5.0, 5.0, 0, 2.0, 400)
- `water`: (0, 0, 0, 0, 0, 0, 0, 0)

## Reproducing this

Working script: `/tmp/nutrition_calc.py` (DB + per-recipe weighed mappings + compute code). Re-run with `python3 /tmp/nutrition_calc.py`; it writes `/tmp/nutrition.json` and `/tmp/nutrition-results.json`. This file is generated from those results by `/tmp/nutrition_working_gen.py`.