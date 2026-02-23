# Cohere Reranker Prototype

A minimal implementation that retrieves top 20 documents from OpenSearch Serverless and reranks them using Cohere Rerank 3.5 via AWS Bedrock.

## Setup

1. Set your AWS credentials (use temporary credentials from your AWS SSO/CLI):
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_SESSION_TOKEN="your-session-token"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the reranker:
```bash
python reranker.py
```

Enter your search query when prompted, and the script will:
1. Retrieve top 20 documents from OpenSearch Serverless (index: `sde-web`)
2. Rerank them using Cohere Rerank 3.5 via AWS Bedrock
3. Display the top 10 reranked results
4. Save full results to `reranking_results.json`

## Configuration

The script is configured for:
- **OpenSearch Endpoint**: `https://blu7t5amz4xhrhjlwr7f.us-east-1.aoss.amazonaws.com`
- **Collection**: `sde-search-test`
- **Index**: `sde-web`
- **AWS Region**: `us-east-1`
- **Bedrock Model**: `cohere.rerank-v3-5:0`

## How It Works

1. **OpenSearch Query**: Performs a `multi_match` query across all fields to retrieve top 20 documents
2. **Document Preparation**: Extracts text content from document fields
3. **Bedrock Reranking**: Sends query and documents to Cohere Rerank 3.5 API
4. **Result Matching**: Maps reranked results back to original documents with both scores

## Notes

- No changes are made to the OpenSearch instance or indexes
- The reranker uses AWS Bedrock's serverless API (pay-per-request)
- Adjust the `top_n` parameter to control how many results are returned after reranking
- The document text extraction logic may need adjustment based on your specific schema
