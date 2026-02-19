from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from backend.models.models import DocArticle
import uuid

INITIAL_DOCS = [
    {
        "slug": "what-is-kosh-ai",
        "title": "What is Kosh-AI?",
        "summary": "Kosh-AI is your smart assistant for saving money on procurement.",
        "content": """
# What is Kosh-AI?

Kosh-AI is a smart tool that helps you save money on the things you buy for your business.

### How it helps:
*   **Reads your bills:** You upload a photo of your invoice, and we read it automatically.
*   **Finds better prices:** We compare what you paid with other suppliers to find cheaper options.
*   **suggests savings:** We tell you exactly where you can save money on your next order.

Think of it like a smart calculator that watches your spending and finds hidden discounts for you.
""",
        "category": "Getting Started",
        "order_index": 1
    },
    {
        "slug": "how-to-upload-invoice",
        "title": "How do I upload an invoice?",
        "summary": "Learn how to add your bills to Kosh-AI in 3 simple steps.",
        "content": """
# How to Upload an Invoice

Uploading is easy and takes less than 30 seconds.

### Steps:
1.  Go to the **Invoices** page on your dashboard.
2.  Click the blue **"Add Purchase Document"** box or the **"Select File"** button.
3.  Choose the invoice file (PDF or Image) from your computer or phone.

### What happens next?
*   You will see a "Processing" badge.
*   Our system reads the items, quantities, and prices.
*   Once done, the status changes to **"Verified"**.

**Tip:** Make sure the photo is clear and not blurry for the best results!
""",
        "category": "Getting Started",
        "order_index": 2
    },
    {
        "slug": "how-to-save-money",
        "title": "How do I save money using this?",
        "summary": "Turn insights into cash savings with our Recommendation Engine.",
        "content": """
# How to Save Money

The core goal of Kosh-AI is to keep money in your pocket.

### How it works:
1.  **We Analyze:** After you upload invoices, we look at what you bought.
2.  **We Compare:** We check if other suppliers are selling the same items for less.
3.  **We Recommend:** If we find a lower price, we show you a **"Recommendation"**.

### What you need to do:
*   Check the **"Recommendations"** page regularly.
*   If you see a savings opportunity, click **"Execute"** or **"Show Me How"**.
*   We will help you switch to the cheaper supplier for your next order.
""",
        "category": "How It Works",
        "order_index": 3
    },
    {
        "slug": "what-happens-after-upload",
        "title": "What happens after I upload?",
        "summary": "Understanding the magic behind the 'Processing' status.",
        "content": """
# What Happens After I Upload?

When you upload a bill, our intelligent system gets to work immediately.

### The Process:
1.  **Digitization:** We turn the picture into digital text.
2.  **Item Extraction:** We list out every single product you bought.
3.  **Price Analysis:** We record how much you paid for each item.
4.  **Market Check:** We instantly check if that price was good or high.

You don't need to do anything during this time. We will notify you when the analysis is complete!
""",
        "category": "How It Works",
        "order_index": 4
    },
    {
        "slug": "what-is-recommendation",
        "title": "What does 'Recommendation' mean?",
        "summary": "A Recommendation is a verified opportunity to save money.",
        "content": """
# What is a Recommendation?

A **Recommendation** is basically a "Savings Alert".

It means we found a way for you to buy the *exact same product* you need, but for a cheaper price.

### Example:
*   **You bought:** 100kg Sugar for ₹50/kg.
*   **We found:** Supplier B selling it for ₹45/kg.
*   **Result:** We send you a Recommendation to buy from Supplier B next time.

**Action:** You can blindly trust these recommendations because we verify the supplier quality first.
""",
        "category": "Features",
        "order_index": 5
    },
    {
        "slug": "is-my-data-safe",
        "title": "Is my data safe?",
        "summary": "Your business data is yours. We respect your privacy.",
        "content": """
# Is My Data Safe?

**Yes, absolutely.**

*   **Encryption:** All your data is encrypted (locked) so no one else can read it.
*   **Private:** We do not sell your data to anyone.
*   **Control:** You can delete your invoices or account at any time.

We use bank-grade security to ensure your business secrets stay secret.
""",
        "category": "Safety & Trust",
        "order_index": 6
    },
    {
        "slug": "why-did-i-get-alert",
        "title": "Why did I get an alert?",
        "summary": "Alerts notify you of urgent savings or actions needed.",
        "content": """
# Understanding Alerts

You might get an alert on your dashboard for a few reasons:

1.  **New Savings Found:** We found a big opportunity to save money.
2.  **Price Spike:** One of your regular items suddenly got expensive.
3.  **Action Required:** We need you to verify an invoice details.

**Tip:** Don't ignore alerts! They are usually worth money.
""",
        "category": "Understanding Alerts",
        "order_index": 7
    },
    {
        "slug": "how-to-place-order",
        "title": "How do I place an order?",
        "summary": "Ordering is not yet fully automated, but we help you prepare.",
        "content": """
# How to Place an Order

Currently, Kosh-AI helps you **plan** your order.

1.  Go to **"Orders"** (coming soon).
2.  Create a list of items you need.
3.  We will tell you the best supplier for each item.
4.  You can then send that list to the supplier via WhatsApp or Email.

We are working on a "One-Click Order" button. Stay tuned!
""",
        "category": "Features",
        "order_index": 8
    },
    {
        "slug": "what-is-kosh-credit",
        "title": "What is Kosh Credit?",
        "summary": "Kosh Credit is our rewards program for smart procurement.",
        "content": """
# What is Kosh Credit?

**Kosh Credit** is money you earn by using the platform.

### How to earn:
*   Upload invoices regularly.
*   Accept our savings recommendations.
*   Refer other shop owners.

### How to use:
You can use Kosh Credits to pay for your subscription or get discounts on partner services.
""",
        "category": "Payments & Credit",
        "order_index": 9
    },
    {
        "slug": "do-i-need-app-daily",
        "title": "Do I need to open the app daily?",
        "summary": "No, but checking weekly is recommended.",
        "content": """
# Do I Need to Open the App Daily?

No, you don't need to be glued to the screen.

*   **Best Practice:** Upload invoices as soon as you receive them.
*   **Routine:** Check the app once a week to review savings and recommendations.
*   **Notifications:** We will email or message you if something urgent comes up.

Kosh-AI works in the background for you 24/7.
""",
        "category": "getting Started",
        "order_index": 10
    }
]

class DocsService:
    @staticmethod
    async def get_categories(db: AsyncSession):
        stmt = select(DocArticle.category).where(DocArticle.is_published == True).distinct()
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_articles(db: AsyncSession, category: str = None):
        stmt = select(DocArticle).where(DocArticle.is_published == True)
        if category:
            stmt = stmt.where(DocArticle.category == category)
        stmt = stmt.order_by(DocArticle.category, DocArticle.order_index)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_article(db: AsyncSession, slug: str):
        stmt = select(DocArticle).where(DocArticle.slug == slug, DocArticle.is_published == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def search_articles(db: AsyncSession, query: str):
        stmt = select(DocArticle).where(
            DocArticle.is_published == True,
            or_(
                DocArticle.title.ilike(f"%{query}%"),
                DocArticle.summary.ilike(f"%{query}%"),
                DocArticle.content.ilike(f"%{query}%")
            )
        ).limit(10)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def seed_initial_data(db: AsyncSession):
        # Check if data exists
        stmt = select(DocArticle).limit(1)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            return

        for doc in INITIAL_DOCS:
            article = DocArticle(**doc)
            db.add(article)
        
        await db.commit()
