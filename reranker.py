#!/usr/bin/env python3
"""
Cohere Reranker Prototype using AWS Bedrock
Retrieves top 20 docs from OpenSearch Serverless and reranks them using Cohere Rerank 3.5
"""

import json
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


class CohereReranker:
    def __init__(self, opensearch_endpoint, index_name, region='us-east-1'):
        """
        Initialize the reranker with OpenSearch and Bedrock clients.
        
        Args:
            opensearch_endpoint: OpenSearch Serverless endpoint URL
            index_name: Name of the index to query
            region: AWS region (default: us-east-1)
        """
        self.index_name = index_name
        self.region = region
        
        # Get AWS credentials from environment
        credentials = boto3.Session().get_credentials()
        
        # Setup AWS4Auth for OpenSearch Serverless
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            'aoss',
            session_token=credentials.token
        )
        
        # Initialize OpenSearch client
        self.opensearch_client = OpenSearch(
            hosts=[{'host': opensearch_endpoint.replace('https://', ''), 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
        
        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region
        )
    
    def search_opensearch(self, query, size=20):
        """
        Search OpenSearch and retrieve top documents.
        
        Args:
            query: Search query string
            size: Number of documents to retrieve (default: 20)
            
        Returns:
            List of documents with their scores and content
        """
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["*"]
                }
            },
            "size": size
        }
        
        response = self.opensearch_client.search(
            index=self.index_name,
            body=search_body
        )
        
        documents = []
        for hit in response['hits']['hits']:
            documents.append({
                'id': hit['_id'],
                'score': hit['_score'],
                'source': hit['_source']
            })
        
        return documents
    
    def rerank_with_cohere(self, query, documents, top_n=10):
        """
        Rerank documents using Cohere Rerank 3.5 via AWS Bedrock.
        
        Args:
            query: The original search query
            documents: List of documents to rerank
            top_n: Number of top results to return after reranking
            
        Returns:
            List of reranked documents with new scores
        """
        # Prepare documents for Cohere reranker
        # Extract only full_text field without truncation
        doc_texts = []
        for doc in documents:
            # Use the full_text field for reranking
            full_text = doc['source'].get('full_text', '')
            doc_texts.append(full_text)
        
        # Prepare request body for Bedrock Cohere Rerank
        request_body = {
            "query": query,
            "documents": doc_texts,
            "top_n": top_n,
            "api_version": 2
        }
        
        # Call Bedrock Cohere Rerank API
        response = self.bedrock_client.invoke_model(
            modelId='cohere.rerank-v3-5:0',
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        # Match reranked results back to original documents
        reranked_docs = []
        for result in response_body['results']:
            original_doc = documents[result['index']]
            reranked_docs.append({
                'id': original_doc['id'],
                'original_score': original_doc['score'],
                'rerank_score': result['relevance_score'],
                'source': original_doc['source']
            })
        
        return reranked_docs
    
    def search_and_rerank(self, query, initial_size=20, top_n=10):
        """
        Complete workflow: search OpenSearch and rerank with Cohere.
        
        Args:
            query: Search query string
            initial_size: Number of initial results from OpenSearch
            top_n: Number of top results to return after reranking
            
        Returns:
            Dictionary with original and reranked results
        """
        print(f"Searching OpenSearch for: '{query}'")
        original_docs = self.search_opensearch(query, size=initial_size)
        print(f"Retrieved {len(original_docs)} documents from OpenSearch")
        
        print(f"\nReranking with Cohere...")
        reranked_docs = self.rerank_with_cohere(query, original_docs, top_n=top_n)
        print(f"Reranked to top {len(reranked_docs)} documents")
        
        return {
            'query': query,
            'original_results': original_docs,
            'reranked_results': reranked_docs
        }


def main():
    """Example usage"""
    # Configuration from environment
    opensearch_endpoint = "https://blu7t5amz4xhrhjlwr7f.us-east-1.aoss.amazonaws.com"
    index_name = "sde-web"
    
    # Initialize reranker
    reranker = CohereReranker(
        opensearch_endpoint=opensearch_endpoint,
        index_name=index_name,
        region='us-east-1'
    )
    
    # Example query - modify this based on your needs
    query = input("Enter your search query: ")
    
    # Search and rerank
    results = reranker.search_and_rerank(
        query=query,
        initial_size=100,  # Get top 100 from OpenSearch
        top_n=20  # Return top 20 after reranking
    )
    
    # Display results
    print("\n" + "="*80)
    print("RERANKED RESULTS")
    print("="*80)
    
    for idx, doc in enumerate(results['reranked_results'], 1):
        print(f"\n{idx}. Document ID: {doc['id']}")
        print(f"   Rerank Score: {doc['rerank_score']:.4f}")
        print(f"   Original Score: {doc['original_score']:.4f}")
        print(f"   Content Preview: {str(doc['source'])[:200]}...")
    
    # Optionally save results to file
    output_file = "reranking_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n\nFull results saved to {output_file}")


if __name__ == "__main__":
    main()
