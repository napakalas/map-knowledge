from mapknowledge import KnowledgeStore
from mapknowledge.scicrunch import SCICRUNCH_PRODUCTION, SCICRUNCH_STAGING

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    print("Production:")
    store = KnowledgeStore(scicrunch_release=SCICRUNCH_PRODUCTION)
    print(store.scicrunch.sckan_build()["released"])
    store.close()

    print("Staging:")
    store = KnowledgeStore(scicrunch_release=SCICRUNCH_STAGING)
    print(store.scicrunch.sckan_build()["released"])
    store.close()
