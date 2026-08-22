# 🧪 Testing Guide for Issue Fixes

## Prerequisites

```bash
cd back-end

# Install new dependency
pip install opencv-python>=4.8.0

# Verify installation
python -c "import cv2; print(f'OpenCV {cv2.__version__} installed')"
```

---

## 🔬 **Test 1: OCR Improvements**

### **Preparation:**
Get a low-quality test image:
- Take a photo of a document with your phone (slight angle)
- OR use a low-resolution scan (< 1000px wide)
- OR use an image with poor lighting

### **Test Steps:**

```bash
# Start backend
cd back-end
python -m uvicorn routes.routes:app --reload

# In another terminal, upload image
curl -X POST http://localhost:8000/upload \
  -F "files=@your_test_image.png" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200"
```

### **What to Check:**

1. **OCR Confidence** in response:
   ```json
   {
     "classification_confidence": 0.85,  // Should be >0.7 now
     "extracted_fields": [
       {
         "field": "name",
         "value": "John Doe",
         "confidence": 0.92  // High confidence
       }
     ]
   }
   ```

2. **Text Accuracy**:
   - Check extracted text for character errors
   - Before: Many OCR errors (l→I, 0→O, etc.)
   - After: Clean text with few errors

3. **Processing Details**:
   - Check logs for "Enhanced preprocessing completed"
   - Should see: upscale + Otsu + deskew messages

### **Expected Results:**
- ✅ Confidence: **>70%** (was ~25%)
- ✅ Fewer character recognition errors
- ✅ Handles skewed/rotated images
- ✅ Works with low-resolution photos

---

## 🔍 **Test 2: Evidence Matching (Fuzzy)**

### **Test Steps:**

```bash
# 1. Upload a document
curl -X POST http://localhost:8000/upload \
  -F "files=@test_document.pdf"

# 2. Query for information
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the applicant name?",
    "top_k": 3
  }'
```

### **What to Check:**

Look at the `evidence` field in the response:

```json
{
  "response": "The applicant name is John Doe.",
  "evidence": [
    {
      "source_document": "test_document.pdf",
      "page": 1,
      "evidence_snippet": "Applicant Name: John Doe",
      "confidence": 1.0,  // Exact match
      "match_type": "exact"
    }
  ]
}
```

### **Test Cases:**

**Case 1: Exact match**
- Query: "What is the date?"
- Document has: "Date: 2024-01-15"
- Expected: Exact match, confidence 1.0

**Case 2: OCR typo**
- Document OCR: "Narne: John Doe" (typo)
- Query asks about: "name"
- Expected: Fuzzy match finds "Narne: John Doe", confidence ~0.85

**Case 3: LLM reformatting**
- Document: "15 Jan 2024"
- LLM extracts: "2024-01-15"
- Expected: Fuzzy match finds original format

### **Expected Results:**
- ✅ Evidence snippets are **relevant** to the answer
- ✅ Confidence scores are **accurate** (0.8-1.0 for good matches)
- ✅ `match_type` shows "exact", "fuzzy", or "fallback"
- ✅ No more "Value not found in document" for valid data

---

## 👁️ **Test 3: Chat Input Visibility**

### **Test Steps:**

```bash
cd back-end
streamlit run streamlit-app.py
```

### **What to Check:**

1. **Light Mode:**
   - Open http://localhost:8501
   - Go to "Search" tab
   - Type in the text input box
   - **Expected**: Black text on white background (visible!)

2. **Dark Mode:**
   - If your system uses dark mode, OR
   - Use browser DevTools → Toggle dark theme
   - Type in text input
   - **Expected**: White text on dark background (visible!)

3. **All Input Types:**
   - Check `st.text_input` (Search tab)
   - Check `st.text_area` (if any)
   - Check Settings page inputs
   - **Expected**: All text visible

### **Expected Results:**
- ✅ Text is **always visible** while typing
- ✅ Proper contrast in **both light and dark modes**
- ✅ No white-on-white or black-on-black text

---

## 📤 **Test 4: Multi-File Upload**

### **Test A: API (curl)**

```bash
# Upload 3 files at once
curl -X POST http://localhost:8000/upload \
  -F "files=@document1.pdf" \
  -F "files=@image1.png" \
  -F "files=@text1.txt"
```

**Expected Response:**
```json
[
  {
    "filename": "document1.pdf",
    "status": "success",
    "document_id": "abc-123",
    "document_type": "Application",
    "classification_confidence": 0.85,
    "extracted_fields": [...]
  },
  {
    "filename": "image1.png",
    "status": "success",
    "document_id": "def-456",
    "document_type": "Certificate",
    "classification_confidence": 0.92,
    "extracted_fields": [...]
  },
  {
    "filename": "text1.txt",
    "status": "success",
    "document_id": "ghi-789",
    "document_type": "Other",
    "classification_confidence": 0.70,
    "extracted_fields": [...]
  }
]
```

**What to Check:**
- ✅ Returns **array** (not single object)
- ✅ Each file has its own `document_id`
- ✅ Independent processing (one error doesn't stop others)
- ✅ Each result has `filename` field

### **Test B: Streamlit UI**

```bash
cd back-end
streamlit run streamlit-app.py
```

1. Go to "Upload" tab
2. Click "Browse files"
3. **Select multiple files** (Ctrl+Click or Cmd+Click)
4. OR drag multiple files at once
5. Wait for processing

**Expected:**
- ✅ All files are uploaded together
- ✅ Individual success message per file
- ✅ Each file's extraction results shown separately

### **Test C: Next.js Frontend**

```bash
cd front-end
npm install  # First time only
npm run dev
```

1. Open http://localhost:3000
2. Go to "Upload Document" tab
3. **Drag multiple files** onto the dropzone
4. OR click and select multiple files

**Expected:**
- ✅ Accepts multiple files
- ✅ Shows "Processing 3 documents..." if 3 files
- ✅ Displays result cards for each file
- ✅ Success/error status per file
- ✅ Each card shows extraction results independently

### **Test D: Error Handling**

Upload mix of valid and invalid files:

```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@valid.pdf" \
  -F "files=@corrupt.pdf" \
  -F "files=@another_valid.png"
```

**Expected:**
```json
[
  {
    "filename": "valid.pdf",
    "status": "success",
    ...
  },
  {
    "filename": "corrupt.pdf",
    "status": "error",
    "message": "Failed to process document: ..."
  },
  {
    "filename": "another_valid.png",
    "status": "success",
    ...
  }
]
```

**What to Check:**
- ✅ Corrupted file doesn't stop processing
- ✅ Other files still succeed
- ✅ Each file has independent status

---

## 🎯 **Complete System Test**

### **End-to-End Workflow:**

```bash
# 1. Install dependencies
cd back-end
pip install opencv-python>=4.8.0

# 2. Start backend
python -m uvicorn routes.routes:app --reload

# In another terminal:

# 3. Upload multiple documents (with low-quality images)
curl -X POST http://localhost:8000/upload \
  -F "files=@skewed_photo.jpg" \
  -F "files=@low_res_scan.png" \
  -F "files=@application.pdf"

# 4. Query the system
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are all the applicant names in the documents?",
    "top_k": 5
  }'

# 5. Check response
# - Should extract names correctly from all 3 docs
# - Evidence snippets should match answers
# - Confidence scores should be high (>0.7)
```

### **Success Criteria:**

1. **OCR (Issue 1):**
   - ✅ Skewed photo processed correctly
   - ✅ Low-res scan upscaled and binarized
   - ✅ Confidence >70% for both images

2. **Evidence (Issue 2):**
   - ✅ Evidence snippets match the extracted values
   - ✅ Fuzzy matching handles OCR typos
   - ✅ Confidence scores make sense

3. **UI (Issue 3):**
   - ✅ (Test via Streamlit) Text input is visible

4. **Multi-Upload (Issue 4):**
   - ✅ All 3 files processed
   - ✅ Independent results for each
   - ✅ Query searches across all documents

---

## 🚨 **Troubleshooting**

### **Issue: opencv-python not found**

```bash
pip install opencv-python
# OR if that fails:
pip install opencv-python-headless
```

### **Issue: "Module cv2 has no attribute ..."**

```bash
# Reinstall opencv
pip uninstall opencv-python
pip install opencv-python>=4.8.0
```

### **Issue: API returns single object, not array**

Check you're using the new endpoint format:
```bash
# Correct (plural):
-F "files=@doc.pdf"

# Wrong (singular):
-F "file=@doc.pdf"
```

### **Issue: Streamlit CSS not applying**

1. Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear Streamlit cache: Delete `~/.streamlit/cache`
3. Restart Streamlit server

### **Issue: Low OCR confidence still**

Check logs for preprocessing messages:
```bash
# Should see:
# "Upscaled image from 800x600 to 1500x1125"
# "Deskewed image by 3.2 degrees"
# "Enhanced preprocessing completed: upscale + Otsu + deskew + denoise"
```

If not seeing these, check:
1. opencv-python is installed
2. No errors in preprocessing
3. Image format is supported (JPG, PNG)

---

## ✅ **Verification Checklist**

Before marking tests complete:

- [ ] **OCR Test**: Upload low-quality image, confidence >70%
- [ ] **Evidence Test**: Query returns relevant snippets with fuzzy matching
- [ ] **UI Test**: Text visible in Streamlit input boxes (light & dark mode)
- [ ] **Multi-Upload API**: Upload 3 files via curl, get array back
- [ ] **Multi-Upload UI**: Drag 3 files in frontend, see all results
- [ ] **Error Handling**: Mix of valid/invalid files, partial success
- [ ] **End-to-End**: Upload → Query → Verify evidence matches
- [ ] **API Docs**: Check http://localhost:8000/docs - `/upload` shows `files` array

---

## 📊 **Performance Benchmarks**

Track these metrics before/after:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| OCR Confidence (clean scan) | 25% | ? | >85% |
| OCR Confidence (photo) | 15% | ? | >70% |
| Evidence Match Rate | 40% | ? | >90% |
| Multi-file upload speed (3 docs) | N/A | ? | <10s |
| Chat input visibility | Broken | Fixed | ✓ |

Fill in "After" column with your test results!

---

## 🎉 **All Tests Passed?**

Great! Your system now has:
- ✅ High-accuracy OCR with preprocessing
- ✅ Fuzzy evidence matching for reliable citations
- ✅ Visible chat inputs in all themes
- ✅ Multi-file upload support

**Ready for production!** 🚀
