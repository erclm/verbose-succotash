# verbose-succotash

## About

This project uses Generative AI through Fireworks AI to analyze and extract information from identity documents (passports and driver's licenses). The system uses computer vision and natural language processing to:

- Automatically detect document type
- Extract relevant information (names, dates, numbers)
- Validate document expiration dates
- Output structured JSON data

## Technology

- **Fireworks AI**: Cloud platform providing efficient access to large vision-language models
- **Qwen2-VL-72B**: Advanced vision-language model optimized for document analysis
- **Python SDK**: Simple integration with Fireworks AI API

## Prerequisites

- Fireworks AI account (get one at [fireworks.ai](https://fireworks.ai))
- API key from Fireworks AI dashboard
- Python 3.8+

## Setup
add .env file
> FIREWORKS_API_KEY=YOUR API KEY HERE

## Basic usage
> python main.py ./idocs/passport-1.jpeg

## With custom output path
> python main.py ./idocs/License-2.jpg -o my_results.json


# Design Choices & Tradeoffs

## Model

**Choice**: Qwen2-VL-72B-Instruct model 

**Rationale**:
- Advanced vision capabilities for document processing
- Strong text recognition from images
- Document type classification without specialized training
- serverless available on Fireworks ai

**Tradeoffs**:
- Higher accuracy than smaller models
- Better handling of diverse document formats
- Higher inference costs and latency

## Technical Considerations

- JSON extraction for data standardization
- CLI command-based
- checking for expiration date of KYC documents
- Structured reporting with minimal dependencies

## Future Improvements

- Batch processing capabilities
- Result comparison between multiple documents
- Confidence scoring for extracted fields