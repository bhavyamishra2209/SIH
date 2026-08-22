# 🚀 Quick Start Testing Guide

## ✅ Status: All Fixed!

- **Frontend**: JSX syntax error fixed ✅
- **Backend API**: Multi-file upload working ✅
- **Tests**: All passing ✅

---

## 🧪 **Testing Options**

### **Option 1: Automated Test Script (Recommended)**

```bash
cd back-end
python test_upload_api.py
```

**Expected Output:**
```
============================================================
SIH Document Intelligence - API Upload Test
============================================================
✅ API is running
=== Testing /upload endpoint (single file) ===
✅ Upload successful!
=== Testing /upload endpoint (multiple files) ===
✅ Upload successful! Processed 3 files
============================================================
✅ All tests passed!
============================================================
```

---

### **Option 2: Swagger UI (Interactive)**

1. **Start Backend:**
   ```bash
   cd back-end
   python main.py
   # OR
   python -m uvicorn routes.routes:app --reload
   ```

2. **Open Swagger UI:**
   - Go to: http://localhost:8000/docs

3. **Test Upload:**
   - Find `/upload` endpoint
   - Click "Try it out"
   - Click "Add string item" to add files
   - Browse and select file(s)
   - Set `chunk_size` (default: 1000)
   - Set `chunk_overlap` (default: 200)
   - Click "Execute"

4. **Expected Response:**
   ```json
   [
     {
       "filename": "your_file.txt",
       "status": "success",
       "document_id": "uuid-here",
       "document_type": "Other",
       "classification_confidence": 0.25,
       "extracted_fields": [...],
       "chunk_count": 1,
       "processing_time_seconds": 2.5
     }
   ]
   ```

---

### **Option 3: Frontend (Next.js)**

1. **Start Backend:**
   ```bash
   cd back-end
   python main.py
   ```

2. **Start Frontend:**
   ```bash
   cd front-end
   npm install  # First time only
   npm run dev
   ```

3. **Open Browser:**
   - Go to: http://localhost:3000

4. **Test Upload:**
   - Click "Upload Document" tab
   - Drag & drop **multiple files** at once
   - OR click to browse and select multiple files
   - See results for each file

5. **Expected:**
   - ✅ Multiple file upload works
   - ✅ Individual cards for each document
   - ✅ Extraction results shown per file
   - ✅ Success/error status per file

---

### **Option 4: cURL (Command Line)**

**Single File:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@path/to/your/document.pdf" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200"
```

**Multiple Files:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@document1.pdf" \
  -F "files=@document2.png" \
  -F "files=@document3.txt" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200"
```

**Expected Response:**
```json
[
  {
    "filename": "document1.pdf",
    "status": "success",
    "document_id": "...",
    "document_type": "Application",
    ...
  },
  {
    "filename": "document2.png",
    "status": "success",
    "document_id": "...",
    "document_type": "Certificate",
    ...
  },
  {
    "filename": "document3.txt",
    "status": "success",
    "document_id": "...",
    "document_type": "Other",
    ...
  }
]
```

---

## 🔍 **Swagger UI Notes**

### **How to Upload Multiple Files in Swagger:**

1. Click "Try it out" on `/upload` endpoint
2. In the "files" section, you'll see an array input
3. Click "+ Add string item" for each file you want to upload
4. Each item lets you select a different file
5. After adding all files, click "Execute"

**Example:**
```
files (array of files):
  [0] file: Browse... → document1.pdf
  [1] file: Browse... → document2.png
  [2] file: Browse... → document3.txt
```

---

## 📊 **What to Expect**

### **Response Structure:**

The API always returns an **array** of results:

```json
[
  {
    "filename": "doc1.pdf",
    "status": "success",
    "message": "Processed document into 5 chunks",
    "document_id": "uuid",
    "document_type": "Application",
    "classification_confidence": 0.85,
    "extracted_fields": [
      {
        "field": "name",
        "value": "John Doe",
        "confidence": 0.92,
        "evidence": {
          "source_document": "doc1.pdf",
          "page": 1,
          "evidence_snippet": "Applicant Name: John Doe",
          "confidence": 1.0
        }
      }
    ],
    "chunk_count": 5,
    "document_ids": ["chunk-id-1", "chunk-id-2", ...],
    "processing_time_seconds": 3.5,
    "firebase_enabled": false
  }
]
```

### **Single File Upload:**
- Send 1 file → Get 1-item array

### **Multi-File Upload:**
- Send 3 files → Get 3-item array
- Each item has independent status
- One file failing doesn't stop others

---

## 🐛 **Troubleshooting**

### **Issue: API not responding**

**Fix:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend if not running
cd back-end
python main.py
```

### **Issue: Frontend build error**

**Fix:**
```bash
cd front-end
rm -rf node_modules .next
npm install
npm run dev
```

### **Issue: Upload returns 404**

**Fix:**
- Check you're using `/upload` (not `/upload-single`)
- Verify backend is running on port 8000
- Check API docs: http://localhost:8000/docs

### **Issue: Low OCR confidence**

**Note:** This is expected for simple text files. For better results:
1. Upload actual scanned documents or images
2. Install opencv-python: `pip install opencv-python`
3. OCR improvements will show on images/scans

---

## ✅ **Verification Checklist**

- [ ] Backend API is running (http://localhost:8000/health)
- [ ] Automated test passes: `python test_upload_api.py`
- [ ] Swagger UI loads: http://localhost:8000/docs
- [ ] Can upload single file via Swagger
- [ ] Can upload multiple files via Swagger
- [ ] Frontend builds without errors: `npm run dev`
- [ ] Frontend loads: http://localhost:3000
- [ ] Can drag & drop multiple files in frontend
- [ ] Results display correctly for each file

---

## 🎯 **Summary**

### **What Works:**
- ✅ Backend `/upload` endpoint (single or multiple files)
- ✅ Swagger UI interactive testing
- ✅ Frontend drag & drop (multiple files)
- ✅ Automated test script
- ✅ cURL uploads

### **API Response:**
- Always returns **array** (even for single file)
- Each file processed independently
- Individual status/results per file

### **Frontend:**
- Accepts multiple files
- Displays results for each file
- Shows success/error per file
- No build errors

---

## 📞 **Quick Commands**

```bash
# Test everything automatically
cd back-end && python test_upload_api.py

# Start backend
cd back-end && python main.py

# Start frontend
cd front-end && npm run dev

# View API docs
# http://localhost:8000/docs

# View Frontend
# http://localhost:3000

# Test with cURL (single file)
curl -X POST http://localhost:8000/upload \
  -F "files=@test.pdf"

# Test with cURL (multiple files)
curl -X POST http://localhost:8000/upload \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.png"
```

---

**Everything is working! You can now upload documents via:**
1. ✅ Swagger UI (http://localhost:8000/docs)
2. ✅ Frontend (http://localhost:3000)
3. ✅ cURL/API calls
4. ✅ Automated tests

🎉 **Ready for demo/testing!**
