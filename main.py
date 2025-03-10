import os
import base64
import json
import re
import sys
import argparse
from typing import Dict, Any, List
from datetime import datetime
from fireworks.client import Fireworks
from dotenv import load_dotenv

# Constants
MODEL_ID = "accounts/fireworks/models/qwen2-vl-72b-instruct"

class DocumentType:
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    UNKNOWN = "unknown"

class KYCFunc:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = Fireworks(api_key=api_key)
        self.model_id = MODEL_ID
    
    # Helper function to encode the image
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    # Detect Type
    def detect_document_type(self, image_path: str) -> str:
        image_base64 = self.encode_image(image_path)
        
        prompt = """
        Analyze this identity document image and determine what type of document it is.
        Please respond with just one of these categories: "passport", "drivers_license", or "unknown".
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": prompt,
                    }, {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        },
                    }],
                }]
            )
            
            text_response = response.choices[0].message.content.lower()

            if "passport" in text_response:
                return DocumentType.PASSPORT
            elif "driver" in text_response or "license" in text_response:
                return DocumentType.DRIVERS_LICENSE
            else:
                return DocumentType.UNKNOWN
        except Exception as e:
            print(f"Error detecting document type: {str(e)}")
            return DocumentType.UNKNOWN
    
    # Get information
    def extract_document_info(self, image_path: str) -> Dict[str, Any]:
        doc_type = self.detect_document_type(image_path)
        print(f"Detected type: {doc_type}")
        image_base64 = self.encode_image(image_path)
        
        # Create appropriate prompt based on document type
        if doc_type == DocumentType.PASSPORT:
            prompt = """
            Extract the following information from this passport:
            1. Full Name
            2. Passport Number
            3. Nationality
            4. Date of Birth
            5. Sex/Gender
            6. Issue Date
            7. Expiration Date
            
            Format the response as a JSON object with these fields.
            """
        elif doc_type == DocumentType.DRIVERS_LICENSE:
            prompt = """
            Extract the following information from this driver's license:
            1. Full Name
            2. License Number
            3. Address
            4. Date of Birth
            5. Sex/Gender
            6. Issue Date
            7. Expiration Date
            8. State/Province
            
            Format the response as a JSON object with these fields.
            """
        else:
            prompt = """
            Extract all personal identification information from this document,
            including name, ID number, date of birth, and any other relevant information.
            
            Format the response as a JSON object.
            """
        
        # Prepare and send the request
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
            )
            
            text_response = response.choices[0].message.content
            
            # Try to extract JSON from the response
            try:
                # Look for JSON-like content in the response
                json_match = re.search(r'({[\s\S]*})', text_response)
                if json_match:
                    json_str = json_match.group(1)
                    data = json.loads(json_str)
                    # Add document type to the result
                    data["documentType"] = doc_type
                    return data
                else:
                    return {
                        "error": "Could not parse JSON from response", 
                        "rawResponse": text_response,
                        "documentType": doc_type
                    }
            except json.JSONDecodeError:
                return {
                    "error": "Invalid JSON in response", 
                    "rawResponse": text_response,
                    "documentType": doc_type
                }
        except Exception as e:
            return {"error": f"API error: {str(e)}", "documentType": doc_type}
    
    def check_document_validity(self, document_info: Dict[str, Any]) -> Dict[str, Any]:
        valid = True
        reasons = []
        # Check document expiration if available
        if document_info.get("Expiration Date"):
            try:
                # Try to parse the date (handling different formats)
                formats = [
                    "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d",  # Standard formats
                    "%B %d, %Y", "%d %B %Y", "%Y %B %d",  # Month name formats
                    "%d %m %Y", "%m %d %Y", "%Y %m %d",   # Space-separated formats
                    "%d-%m-%Y", "%m-%d-%Y",               # Hyphen-separated formats
                    "%d.%m.%Y", "%m.%d.%Y", "%Y.%m.%d",   # Dot-separated formats
                    "%b %d, %Y", "%d %b %Y", "%Y %b %d",  # Abbreviated month formats
                    "%Y%m%d"                              # Compact format
                ]
                
                for fmt in formats:
                    try:
                        exp_date = datetime.strptime(document_info["Expiration Date"], fmt)
                        if exp_date < datetime.now():
                            valid = False
                            reasons.append("Document has expired")
                        break
                    except ValueError:
                        continue
            except Exception:
                reasons.append("Could not verify expiration date format")
        
        # Add validity information to the document data
        document_info["isValid"] = valid
        if reasons:
            document_info["validityNotes"] = reasons
        
        return document_info

def process_document(api_key: str, image_path: str) -> Dict[str, Any]:
    extractor = KYCFunc(api_key)
    print(f"\nProcessing: {os.path.basename(image_path)}")
    try:
        # Extract document information
        doc_info = extractor.extract_document_info(image_path)
        
        # Perform basic validity checks
        if "error" not in doc_info:
            doc_info = extractor.check_document_validity(doc_info)
            
        # Add source file information
        doc_info["sourceFile"] = os.path.basename(image_path)
        
        # Print basic info for visibility
        print(f"Document type: {doc_info.get('documentType', 'Unknown')}")
        print(f"Valid: {doc_info.get('isValid', 'Unknown')}")
        
        return doc_info
        
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return {
            "sourceFile": os.path.basename(image_path),
            "error": str(e),
            "documentType": "error"
        }

def main():
    # Parse command-line arguments 
    parser = argparse.ArgumentParser(description='Process a document image for KYC verification')
    parser.add_argument('image_path', help='Path to the document image file')
    parser.add_argument('-o', '--output', help='Output JSON file path (default: based on input filename)')
    args = parser.parse_args()
    
    # Check if the specified image file exists
    if not os.path.isfile(args.image_path):
        print(f"Error: File '{args.image_path}' does not exist")
        sys.exit(1)
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment variables
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        raise ValueError("FIREWORKS_API_KEY not found in environment variables")
    
    # Process the document
    result = process_document(api_key, args.image_path)
    
    # Determine output file path
    if args.output:
        output_path = args.output
    else:
        # Generate output filename based on input filename
        input_basename = os.path.basename(args.image_path)
        input_name = os.path.splitext(input_basename)[0]
        output_path = f"{input_name}_kyc_result.json"
    
    # Save the result to the JSON file
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\nProcessed document. Results saved to {output_path}")

if __name__ == "__main__":
    main()