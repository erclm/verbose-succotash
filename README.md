# verbose-succotash

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