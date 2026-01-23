"""
Sample Ads Data for Sponsored AI
Contains 30 text-based ads from real companies across various categories.
"""

SAMPLE_ADS = [
    # Technology
    {
        "id": "ad_001",
        "company": "Apple",
        "category": "Technology",
        "ad_text": "Experience the future with MacBook Pro. M3 chip, 22-hour battery life, stunning Liquid Retina display. Power meets portability.",
        "keywords": ["laptop", "computer", "macbook", "productivity", "work", "coding", "developer"]
    },
    {
        "id": "ad_002",
        "company": "Microsoft",
        "category": "Technology",
        "ad_text": "Microsoft 365 - Your complete productivity suite. Word, Excel, PowerPoint, Teams, and 1TB OneDrive storage. Work smarter, not harder.",
        "keywords": ["office", "productivity", "software", "documents", "spreadsheet", "work", "business"]
    },
    {
        "id": "ad_003",
        "company": "Samsung",
        "category": "Technology",
        "ad_text": "Samsung Galaxy S24 Ultra - AI-powered photography, 200MP camera, S Pen included. Capture every moment in stunning detail.",
        "keywords": ["phone", "smartphone", "mobile", "camera", "photography", "android"]
    },
    {
        "id": "ad_004",
        "company": "Dell",
        "category": "Technology",
        "ad_text": "Dell XPS 15 - InfinityEdge display, Intel Core Ultra processors, premium design. The ultimate laptop for creators and professionals.",
        "keywords": ["laptop", "computer", "work", "design", "creator", "professional"]
    },
    {
        "id": "ad_005",
        "company": "Sony",
        "category": "Technology",
        "ad_text": "PlayStation 5 - Immersive gaming with haptic feedback, 4K graphics, and lightning-fast SSD. Play has no limits.",
        "keywords": ["gaming", "console", "playstation", "games", "entertainment", "video games"]
    },
    
    # Finance
    {
        "id": "ad_006",
        "company": "Chase",
        "category": "Finance",
        "ad_text": "Chase Sapphire Preferred - Earn 3X points on dining and travel. $95 annual fee, 60,000 bonus points after qualifying spend.",
        "keywords": ["credit card", "bank", "finance", "travel", "rewards", "points", "money"]
    },
    {
        "id": "ad_007",
        "company": "Fidelity",
        "category": "Finance",
        "ad_text": "Fidelity Investments - Zero commission stock trading, retirement planning, and wealth management. Your financial future starts here.",
        "keywords": ["investing", "stocks", "retirement", "savings", "wealth", "finance", "money"]
    },
    {
        "id": "ad_008",
        "company": "PayPal",
        "category": "Finance",
        "ad_text": "PayPal - Send money worldwide, shop securely online, and manage your finances all in one app. Fast, safe, and simple.",
        "keywords": ["payment", "money", "transfer", "online shopping", "secure", "digital wallet"]
    },
    
    # Food & Beverage
    {
        "id": "ad_009",
        "company": "Starbucks",
        "category": "Food",
        "ad_text": "Starbucks - Handcrafted beverages made just for you. Join Starbucks Rewards for free drinks, birthday treats, and exclusive offers.",
        "keywords": ["coffee", "drinks", "cafe", "breakfast", "morning", "caffeine"]
    },
    {
        "id": "ad_010",
        "company": "DoorDash",
        "category": "Food",
        "ad_text": "DoorDash - Your favorite restaurants delivered to your door. Free delivery on your first order with code WELCOME.",
        "keywords": ["food delivery", "restaurant", "takeout", "dinner", "lunch", "hungry", "eat"]
    },
    {
        "id": "ad_011",
        "company": "HelloFresh",
        "category": "Food",
        "ad_text": "HelloFresh - Fresh ingredients and chef-designed recipes delivered weekly. Cook delicious meals in 30 minutes or less.",
        "keywords": ["cooking", "meal kit", "recipes", "healthy eating", "dinner", "food", "chef"]
    },
    {
        "id": "ad_012",
        "company": "Whole Foods",
        "category": "Food",
        "ad_text": "Whole Foods Market - Organic, sustainable, and locally-sourced groceries. Prime members save extra on hundreds of items.",
        "keywords": ["grocery", "organic", "healthy", "food", "shopping", "natural"]
    },
    
    # Travel
    {
        "id": "ad_013",
        "company": "Booking.com",
        "category": "Travel",
        "ad_text": "Booking.com - Over 28 million accommodation listings worldwide. Free cancellation on most bookings. Your perfect stay awaits.",
        "keywords": ["hotel", "travel", "vacation", "booking", "accommodation", "trip", "stay"]
    },
    {
        "id": "ad_014",
        "company": "Airbnb",
        "category": "Travel",
        "ad_text": "Airbnb - Unique stays and experiences around the world. From cozy cabins to luxury villas, find your perfect getaway.",
        "keywords": ["travel", "vacation", "rental", "stay", "trip", "holiday", "accommodation"]
    },
    {
        "id": "ad_015",
        "company": "Delta Airlines",
        "category": "Travel",
        "ad_text": "Delta Air Lines - Fly with confidence. Earn SkyMiles on every flight, enjoy free entertainment, and experience award-winning service.",
        "keywords": ["flights", "airline", "travel", "flying", "vacation", "trip", "airplane"]
    },
    {
        "id": "ad_016",
        "company": "Expedia",
        "category": "Travel",
        "ad_text": "Expedia - Bundle flight + hotel and save up to 30%. One Key rewards on every booking. Your journey starts here.",
        "keywords": ["travel", "vacation", "hotel", "flight", "booking", "trip", "deals"]
    },
    
    # Health & Fitness
    {
        "id": "ad_017",
        "company": "Peloton",
        "category": "Health",
        "ad_text": "Peloton - World-class workouts at home. Bike, tread, or app-only membership. Join millions achieving their fitness goals.",
        "keywords": ["fitness", "exercise", "workout", "gym", "health", "cycling", "training"]
    },
    {
        "id": "ad_018",
        "company": "Nike",
        "category": "Health",
        "ad_text": "Nike - Just Do It. Performance gear engineered for athletes. From running shoes to training apparel, push your limits.",
        "keywords": ["sports", "running", "shoes", "fitness", "athletic", "workout", "gym"]
    },
    {
        "id": "ad_019",
        "company": "Headspace",
        "category": "Health",
        "ad_text": "Headspace - Meditation and mindfulness for everyone. Reduce stress, sleep better, and find your calm. Try 14 days free.",
        "keywords": ["meditation", "mental health", "sleep", "stress", "wellness", "mindfulness", "calm"]
    },
    {
        "id": "ad_020",
        "company": "Fitbit",
        "category": "Health",
        "ad_text": "Fitbit - Track your health journey. Monitor heart rate, sleep, stress, and activity. Premium insights to reach your goals.",
        "keywords": ["fitness tracker", "health", "exercise", "sleep", "wellness", "wearable", "smart watch"]
    },
    
    # Shopping & E-commerce
    {
        "id": "ad_021",
        "company": "Amazon",
        "category": "Shopping",
        "ad_text": "Amazon Prime - Free 2-day shipping, Prime Video, Music, and more. Join millions of members enjoying exclusive benefits.",
        "keywords": ["shopping", "online", "delivery", "prime", "deals", "buy", "store"]
    },
    {
        "id": "ad_022",
        "company": "IKEA",
        "category": "Shopping",
        "ad_text": "IKEA - Affordable home furnishing solutions. Scandinavian design, sustainable materials, and endless inspiration for every room.",
        "keywords": ["furniture", "home", "decor", "design", "interior", "house", "living"]
    },
    {
        "id": "ad_023",
        "company": "Wayfair",
        "category": "Shopping",
        "ad_text": "Wayfair - A zillion things home. Furniture, decor, and more with fast shipping. Find exactly what you're looking for.",
        "keywords": ["furniture", "home", "decor", "shopping", "interior", "house"]
    },
    
    # Entertainment
    {
        "id": "ad_024",
        "company": "Netflix",
        "category": "Entertainment",
        "ad_text": "Netflix - Unlimited movies, TV shows, and award-winning originals. Watch anywhere, anytime. Start your free trial today.",
        "keywords": ["streaming", "movies", "tv shows", "entertainment", "watch", "series", "film"]
    },
    {
        "id": "ad_025",
        "company": "Spotify",
        "category": "Entertainment",
        "ad_text": "Spotify Premium - Ad-free music, offline listening, and unlimited skips. Discover millions of songs and podcasts.",
        "keywords": ["music", "streaming", "songs", "playlist", "podcast", "audio", "listen"]
    },
    {
        "id": "ad_026",
        "company": "Disney+",
        "category": "Entertainment",
        "ad_text": "Disney+ - Stream Disney, Pixar, Marvel, Star Wars, and National Geographic. Family entertainment with the stories you love.",
        "keywords": ["streaming", "movies", "disney", "kids", "family", "marvel", "star wars"]
    },
    
    # Education & Learning
    {
        "id": "ad_027",
        "company": "Coursera",
        "category": "Education",
        "ad_text": "Coursera - Learn from top universities and companies. Earn certificates in data science, business, tech, and more.",
        "keywords": ["learning", "education", "courses", "skills", "career", "online learning", "certificate"]
    },
    {
        "id": "ad_028",
        "company": "Duolingo",
        "category": "Education",
        "ad_text": "Duolingo - Learn a new language for free. Fun, bite-sized lessons in Spanish, French, Japanese, and 35+ languages.",
        "keywords": ["language", "learning", "education", "spanish", "french", "study", "app"]
    },
    {
        "id": "ad_029",
        "company": "MasterClass",
        "category": "Education",
        "ad_text": "MasterClass - Learn from the world's best. Cooking with Gordon Ramsay, writing with Neil Gaiman, and 180+ classes.",
        "keywords": ["learning", "education", "skills", "cooking", "writing", "creative", "expert"]
    },
    
    # Automotive
    {
        "id": "ad_030",
        "company": "Tesla",
        "category": "Automotive",
        "ad_text": "Tesla - Accelerating the world's transition to sustainable energy. Model 3 starting at $38,990. Zero emissions, maximum performance.",
        "keywords": ["car", "electric", "ev", "vehicle", "driving", "automotive", "sustainable"]
    }
]


def get_all_ads():
    """Return all sample ads."""
    return SAMPLE_ADS


def get_ads_for_embedding():
    """Return ads formatted for embedding into ChromaDB."""
    documents = []
    metadatas = []
    ids = []
    
    for ad in SAMPLE_ADS:
        # Combine ad text with keywords for better semantic matching
        doc_text = f"{ad['ad_text']} Keywords: {', '.join(ad['keywords'])}"
        documents.append(doc_text)
        metadatas.append({
            "company": ad["company"],
            "category": ad["category"],
            "ad_text": ad["ad_text"]
        })
        ids.append(ad["id"])
    
    return documents, metadatas, ids
