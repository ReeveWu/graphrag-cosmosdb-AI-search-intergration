from azure.search.documents.indexes.models import (  
    SimpleField,
    SearchField,
    SearchableField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    HnswParameters,
    VectorSearchAlgorithmMetric,
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIParameters,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
    SearchIndex,
    )

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("ai_search_endpoint")
key = os.getenv("ai_search_key")
credential = AzureKeyCredential(key)
index_name = os.getenv("ai_search_index_name")
index_client = SearchIndexClient(endpoint=endpoint, credential=credential) 
search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
    
# Create a search index  
fields = [  
    SearchableField(name="id", type=SearchFieldDataType.String, key=True,  sortable=True, filterable=True, facetable=True),  
    SearchableField(name="name", type=SearchFieldDataType.String), 
    SearchableField(name="type", type=SearchFieldDataType.String),  
    SearchableField(name="description", type=SearchFieldDataType.String), 
    SearchableField(name="human_readable_id", type=SearchFieldDataType.String),  
    SearchField(name="description_embedding", 
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single), 
                hidden=False, 
                searchable=True,
                filterable=False,
                sortable=False,
                facetable=False,
                vector_search_dimensions=3072,
                vector_search_profile_name="myHnswProfile"
                ),  
]  
  
# Configure the vector search configuration  
vector_search = VectorSearch(  
    algorithms=[  
        HnswAlgorithmConfiguration(  
            name="myHnsw",  
            parameters=HnswParameters(  
                m=4,  
                ef_construction=400,  
                ef_search=500,  
                metric=VectorSearchAlgorithmMetric.COSINE,  
            ),  
        ),  
        ExhaustiveKnnAlgorithmConfiguration(  
            name="myExhaustiveKnn",  
            parameters=ExhaustiveKnnParameters(  
                metric=VectorSearchAlgorithmMetric.COSINE,  
            ),  
        ),  
    ],  
    profiles=[  
        VectorSearchProfile(  
            name="myHnswProfile",  
            algorithm_configuration_name="myHnsw",  
            vectorizer="myOpenAI",  
        ),  
        VectorSearchProfile(  
            name="myExhaustiveKnnProfile",  
            algorithm_configuration_name="myExhaustiveKnn",  
            vectorizer="myOpenAI",  
        ),  
    ],  
    vectorizers=[  
        AzureOpenAIVectorizer(  
            name="myOpenAI",  
            kind="azureOpenAI",  
            azure_open_ai_parameters=AzureOpenAIParameters(  
                resource_uri=os.getenv("aoai_resource_uri"),  
                deployment_id=os.getenv("aoai_embedding_deployment_name"),  
                model_name= "text-embedding-3-large",
                api_key=os.getenv("aozai_api_key"),  
            ),  
        ),  
    ],  
)  
  
semantic_config = SemanticConfiguration(  
    name="default",  
    prioritized_fields=SemanticPrioritizedFields(  
        title_field=SemanticField(field_name="name"),
        keywords_fields=[SemanticField(field_name="type")],
        content_fields=[SemanticField(field_name="description")],  
    ),  
)  

  
# Create the semantic search with the configuration  
semantic_search = SemanticSearch(configurations=[semantic_config])  
  
# Create the search index with the semantic settings
index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, semantic_search=semantic_search)  
try:    
    index_client.delete_index(index)
    print ('Index Deleted')
except Exception as ex:
    print (f"OK: Looks like index does not exist")

result = index_client.create_or_update_index(index)
print(f"{result.name} created")  

print("Index created")

print("Uploading documents...")
INPUT_DIR = "./data/output"
ENTITY_EMBEDDING_TABLE = "create_final_entities"

entity_embedding_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_EMBEDDING_TABLE}.parquet")
  
final_results = []

for _, row in entity_embedding_df.iterrows():
    final_results.append({
        'id': row['id'],
        'name': row['name'],
        'type': row['type'],
        'description': row['description'],
        'human_readable_id': str(row['human_readable_id']),
        'description_embedding': row['description_embedding'].tolist(),
    })

result = search_client.upload_documents(final_results)
print(f"Uploaded {len(final_results)} documents") 