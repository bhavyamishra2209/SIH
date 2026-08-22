#!/usr/bin/env python3
"""
Quick test script to verify the upload API endpoints work correctly.
"""

import requests
import sys
from pathlib import Path

API_URL = "http://localhost:8000"

def test_single_upload():
    """Test /upload endpoint with a single file."""
    print("\n=== Testing /upload endpoint (single file) ===")
    
    # Create a temporary test file
    test_content = """
    Test Document
    
    Name: John Doe
    Date: 2024-01-15
    Application Number: APP-12345
    
    This is a test document for verifying the upload API.
    """
    
    test_file = Path("test_document.txt")
    test_file.write_text(test_content)
    
    try:
        with open(test_file, 'rb') as f:
            files = [('files', ('test_document.txt', f, 'text/plain'))]
            data = {
                'chunk_size': 1000,
                'chunk_overlap': 200
            }
            
            print(f"Uploading {test_file} to {API_URL}/upload...")
            response = requests.post(f"{API_URL}/upload", files=files, data=data)
            
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    result = results[0]
                    print("✅ Upload successful!")
                    print(f"  Status: {result.get('status')}")
                    print(f"  Document ID: {result.get('document_id')}")
                    print(f"  Document Type: {result.get('document_type')}")
                    print(f"  Classification Confidence: {result.get('classification_confidence', 0)*100:.1f}%")
                    print(f"  Chunks: {result.get('chunk_count')}")
                    print(f"  Processing Time: {result.get('processing_time_seconds')}s")
                    
                    if result.get('extracted_fields'):
                        print(f"  Extracted Fields: {len(result['extracted_fields'])} fields")
                        for field in result['extracted_fields']:
                            if field.get('value'):
                                print(f"    - {field['field']}: {field['value']} (confidence: {field['confidence']*100:.0f}%)")
                    return True
                else:
                    print("❌ No results returned")
                    return False
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()


def test_multi_upload():
    """Test /upload endpoint with multiple files."""
    print("\n=== Testing /upload endpoint (multiple files) ===")
    
    # Create test files
    test_files = []
    for i in range(1, 4):
        content = f"""
        Test Document {i}
        
        Name: Test Person {i}
        Date: 2024-01-{15+i}
        Reference: REF-{1000+i}
        
        This is test document number {i}.
        """
        file_path = Path(f"test_doc_{i}.txt")
        file_path.write_text(content)
        test_files.append(file_path)
    
    try:
        # Prepare files for upload
        files = [
            ('files', (f.name, open(f, 'rb'), 'text/plain'))
            for f in test_files
        ]
        
        data = {
            'chunk_size': 1000,
            'chunk_overlap': 200
        }
        
        print(f"Uploading {len(test_files)} files to {API_URL}/upload...")
        response = requests.post(f"{API_URL}/upload", files=files, data=data)
        
        # Close file handles
        for _, (_, f, _) in files:
            f.close()
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Upload successful! Processed {len(results)} files")
            
            for i, result in enumerate(results, 1):
                print(f"\nFile {i}: {result.get('filename')}")
                print(f"  Status: {result.get('status')}")
                print(f"  Document ID: {result.get('document_id')}")
                print(f"  Document Type: {result.get('document_type')}")
                print(f"  Confidence: {result.get('classification_confidence', 0)*100:.1f}%")
                print(f"  Chunks: {result.get('chunk_count')}")
            
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    finally:
        # Clean up test files
        for f in test_files:
            if f.exists():
                f.unlink()


def check_api_health():
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is running")
            print(f"  Status: {data.get('status')}")
            print(f"  Version: {data.get('version')}")
            print(f"  Document Count: {data.get('document_count')}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {API_URL}")
        print("   Make sure the backend is running:")
        print("   cd back-end && python -m uvicorn routes.routes:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False


def main():
    print("=" * 60)
    print("SIH Document Intelligence - API Upload Test")
    print("=" * 60)
    
    # Check API health
    if not check_api_health():
        sys.exit(1)
    
    # Test single file upload
    success1 = test_single_upload()
    
    # Test multi-file upload
    success2 = test_multi_upload()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
