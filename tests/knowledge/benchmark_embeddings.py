import time

from medilink_ai.knowledge.embeddings import get_embedding_service


def main() -> None:
    service = get_embedding_service()
    texts = [
        "Patient registration and duplicate record prevention.",
        "Laboratory test results must be reviewed by authorized staff.",
        "Pharmacy dispensing requires prescription validation.",
        "Billing records contain charges and invoices.",
        "Hospital policies must be approved and version controlled.",
    ]
    start = time.perf_counter()
    vectors = service.embed_many(texts)
    elapsed = time.perf_counter() - start
    print(f"Embedded {len(vectors)} texts in {elapsed:.3f} seconds.")
    print(f"Vector dimension: {service.dimension}")
    print(f"Average time per text: {elapsed / len(vectors):.3f} seconds")


if __name__ == "__main__":
    main()
