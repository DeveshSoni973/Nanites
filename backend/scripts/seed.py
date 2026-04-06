import httpx
import asyncio

API_BASE = "http://127.0.0.1:8000"
EMAIL = "admin@admin.com"
PASSWORD = "admin"

# =====================================================================
# MASSIVE NOTES (1000+ WORDS EACH)
# =====================================================================

DATA_STRUCTURE = {
    "Engineering": {
        "Software Architecture": {
            "Microservices vs Monoliths": """Microservices and monoliths represent two fundamentally different approaches to structuring complex software systems. A monolithic architecture gathers all features, modules, and domain logic inside a single deployable unit. This means the codebase often grows into a tightly-coupled block where components depend heavily on one another. In the early stages of development, teams benefit from the simplicity of this model: a single build pipeline, one deployment process, straightforward debugging, and minimal operational overhead. However, as the product expands, a monolith tends to accumulate technical debt, merge conflicts increase, scaling becomes inefficient because the entire system must scale together, and deployments become risky since any small change can impact the whole application.

Microservices attempt to solve these issues by splitting a large system into smaller, independent services that communicate through APIs or asynchronous messages. Each service is responsible for a single bounded context. Teams can deploy, scale, and rewrite microservices independently of the rest of the system. This creates organizational and architectural flexibility. But the complexity shifts: instead of dealing with one large codebase, engineers must now handle distributed systems issues like network partitions, latency, service discovery, distributed tracing, and eventual consistency. Microservices demand strong DevOps maturity, observability tools, and culture alignment. Ultimately, the choice depends on company size, product stage, and engineering expertise. Microservices shine in large, fast-moving organizations, while monoliths remain the fastest way to ship V1 products.

In practice, companies rarely jump from monolith to microservices instantly. Teams usually extract critical domains piece by piece. This allows safer rewrites, gradual scaling, and easier testing. A microservice transition done without discipline leads to a distributed monolith—worst of both worlds. This is why architecture is not religion; it is strategy. Pick the right one for your team today, not the hypothetical team you think you’ll have someday.""",

            "Event-Driven Architecture": """Event-Driven Architecture (EDA) is a design paradigm where systems communicate by producing and reacting to events instead of directly calling one another. An event represents a meaningful state change—such as a user registering, a payment being processed, or inventory being updated. Instead of tightly coupling components through synchronous APIs, EDA uses brokers like Kafka, RabbitMQ, and NATS to decouple producers and consumers. This allows systems to scale independently, respond in near real-time, and handle massive throughput with resilience.

The biggest advantage of EDA is loose coupling. Producers don’t know who consumes events, and consumers don’t care who produced them. This leads to systems that are easier to evolve and extend. For example, when a new analytics service is added, it simply subscribes to the existing "order_placed" event without modifying any existing code.

From this foundation, more advanced architectural patterns emerge. Event Sourcing stores every state change as an immutable event, making it easy to rebuild state or audit behavior. CQRS splits reads and writes for better scalability. Streaming systems process millions of events per second with low latency. But developers must handle challenges: duplicates, out-of-order events, idempotency, and eventual consistency.

EDA powers modern large-scale platforms like Uber’s dispatch, Amazon’s inventory, Netflix’s playback pipelines, and countless fintech systems because it provides resilience, decoupling, and real-time behavior that synchronous request/response models simply cannot match.""",
        },

        "AI & Machine Learning": {
            "Transformers Explained": """Transformers revolutionized natural language processing by removing the sequential bottlenecks of RNNs and LSTMs. Traditional recurrent architectures process text word-by-word, which slows training and limits the ability to capture long-range dependencies. Transformers introduced self-attention, a mechanism that examines relationships between all tokens simultaneously. This lets the model understand that in a sentence like “The cat that the dog chased was fast,” the word “was” refers to “cat,” not “dog,” even though several words separate them.

Every token in a transformer generates Query, Key, and Value vectors. Attention weights determine which words influence which outputs. Multi-head attention allows parallel patterns: one head tracks subject relationships, another positional relationships, another syntax, and so on. Stacking 12–100+ layers builds deep hierarchical understanding.

Positional embeddings tell the model where each token is, since transformer layers treat all positions equally. Feed-forward networks add non-linearity. Residual layers help gradients propagate. The architecture scales horizontally—GPUs can process entire sequences at once.

This idea became the backbone of GPT, BERT, LLaMA, PaLM, Claude, and multimodal models. Transformers dominate vision (ViT), audio (Whisper), images (Stable Diffusion), robotics (RT-2), and more. Their parallelism, interpretability, and scaling laws changed AI forever.""",

            "Vector Embeddings": """Vector embeddings convert raw unstructured data into dense numerical vectors that encode meaning. They capture conceptual relationships instead of surface patterns. For example, embeddings learn that “doctor” is related to “hospital,” “medicine,” and “nurse,” while “mountain” clusters with “river,” “forest,” and “valley.” The closer two vectors are, the more semantically related the inputs.

These embeddings come from models like BERT, sentence-transformers, OpenAI embeddings, CLIP, and multimodal encoders. The vectors typically range from 256 to 4096 dimensions. They power search, recommendations, classification, similarity checks, clustering, anomaly detection, chat memory, and knowledge graphs.

Vector databases (Pinecone, Milvus, pgvector, Weaviate) index billions of vectors and perform fast nearest-neighbor search using cosine similarity or Euclidean distance. Unlike keyword search, vector search retrieves meaning, not literal text. This is why semantic search feels intelligent: the embeddings store compressed semantic knowledge learned from massive datasets.

Embeddings are now used in every serious AI system. They enable grounding, retrieval-augmented generation, real-time recommendation engines, memory architectures, and AI agents that can reason over long-term context.""",
        },
    },

    "Personal": {
        "Finances": {
            "2026 Budget Plan": """A structured 2026 budget requires clarity and long-term vision. Start with categorizing expenses: fixed (rent, utilities), essential (food, transport), and discretionary (subscriptions, entertainment). The goal is to cut discretionary spending by 15% without harming quality of life. These savings are redirected into a diversified ETF portfolio and a high-yield savings account.

Emergency funds must cover at least six months. Retirement contributions should be maxed by Q3. Asset allocation should follow stable risk distribution: equities for growth, bonds for stability, ETFs for diversification, and cash for short-term needs. Monthly financial audits track progress and prevent lifestyle creep.

The blueprint extends beyond 2026. The target is buying property by 2028, meaning large capital reserves and strict spending discipline. Staying consistent is more important than optimizing for every market fluctuation. Financial independence is a long game, but the 2026 plan sets the foundation.""",
        },

        "Travel": {
            "Japan Itinerary": """A 14-day Japan itinerary lets you explore urban, cultural, historical, and natural attractions without rushing. Tokyo takes the first four days. Shinjuku’s neon, Shibuya Crossing’s crowds, Harajuku’s street culture, and Akihabara’s tech madness form the core experiences. Asakusa offers classic temples and traditional shops. teamLab Borderless is the country’s futuristic art landmark.

Take the Shinkansen to Kyoto next. Spend three days visiting Fushimi Inari’s endless red torii gates, Arashiyama’s bamboo forest, Kiyomizu-dera, and historic tea houses in Gion. Kyoto is slower and deeply cultural.

Move to Osaka for food tourism: takoyaki, okonomiyaki, and the Dotonbori canal. Visit Osaka Castle and Universal Studios Japan. Then head to Hiroshima for peace memorials and ferry to Miyajima Island to see the floating torii.

Return to Tokyo for final shopping and exploration. Buy a JR Pass before arriving. Pick up portable Wi-Fi at Narita. Pack lightly because Japan rewards mobility. The itinerary balances technology, culture, history, and food in a way few countries can match.""",
        },
    },
}


# =====================================================================
# HELPERS
# =====================================================================

async def login(client):
    try:
        res = await client.post(
            f"{API_BASE}/auth/login",
            data={"username": EMAIL, "password": PASSWORD},
        )
        res.raise_for_status()
        return res.json()["access_token"]
    except httpx.HTTPStatusError:
        await client.post(
            f"{API_BASE}/auth/signup",
            json={"email": EMAIL, "password": PASSWORD},
        )
        res = await client.post(
            f"{API_BASE}/auth/login",
            data={"username": EMAIL, "password": PASSWORD},
        )
        res.raise_for_status()
        return res.json()["access_token"]


async def create_node(client, headers, title, type_, parent_id=None, content=""):
    r = await client.post(
        f"{API_BASE}/nodes",
        headers=headers,
        json={
            "title": title,
            "type": type_,
            "parent_id": parent_id,
            "content": content,
        },
    )
    r.raise_for_status()
    return r.json()


# =====================================================================
# SEED LOGIC
# =====================================================================

async def seed():
    note_count = 0

    async with httpx.AsyncClient(timeout=90.0) as client:
        print("Authenticating...")
        token = await login(client)
        headers = {"Authorization": f"Bearer {token}"}

        print("Seeding content...")

        for root_name, subfolders in DATA_STRUCTURE.items():
            root = await create_node(client, headers, root_name, "folder")
            print(f"Folder: {root_name}")

            for folder_name, notes in subfolders.items():
                sub = await create_node(client, headers, folder_name, "folder", root["id"])
                print(f"  Subfolder: {folder_name}")

                for note_title, note_content in notes.items():
                    final_body = f"# {note_title}\n\n" + (note_content + "\n\n") * 3
                    await create_node(client, headers, note_title, "note", sub["id"], final_body)
                    note_count += 1
                    print(f"    Note: {note_title}")

                    await asyncio.sleep(0.3)

    print(f"Seed complete. Total notes: {note_count}")


if __name__ == "__main__":
    asyncio.run(seed())