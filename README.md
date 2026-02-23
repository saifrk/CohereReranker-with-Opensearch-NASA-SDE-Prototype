# Cohere Reranker with OpenSearch: NASA SDE Prototype

A minimal implementation that retrieves top 100 documents from OpenSearch Serverless and reranks them to the top 20 using Cohere Rerank 3.5 via AWS Bedrock.

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
1. Retrieve **top 100 documents** from OpenSearch Serverless (index: `sde-web`)
2. Rerank them using **Cohere Rerank 3.5** via AWS Bedrock using each document's full `full_text` field
3. Display the **top 20 reranked results**
4. Save full results to `reranking_results.json`

## Configuration

The script is configured for:
- **OpenSearch Endpoint**: `https://blu7t5amz4xhrhjlwr7f.us-east-1.aoss.amazonaws.com`
- **Collection**: `sde-search-test`
- **Index**: `sde-web`
- **AWS Region**: `us-east-1`
- **Bedrock Model**: `cohere.rerank-v3-5:0`

## How It Works

1. **OpenSearch Query**: Performs a `multi_match` query across all fields to retrieve top 100 documents
2. **Document Preparation**: Extracts the `full_text` field from each document (untruncated) for accurate semantic reranking
3. **Bedrock Reranking**: Sends the query and document texts to Cohere Rerank 3.5 API
4. **Result Matching**: Maps reranked results back to original documents, returning both the original OpenSearch score and the new Cohere rerank score

## Why Top 100 → Rerank to 20?

Retrieving a larger candidate pool (100) before reranking consistently surfaces better results than reranking a smaller pool (20). OpenSearch uses keyword-based BM25 scoring which can miss semantically relevant documents — Cohere's reranker reads the full document content and can promote docs that OpenSearch ranked mediocre but are actually highly relevant to the query.

## Notes

- No changes are made to the OpenSearch instance or indexes
- The reranker uses AWS Bedrock's serverless API (pay-per-request, no always-on instance)
- Reranking is fully deterministic — same query produces identical results every run
