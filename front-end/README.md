# SIH Document Intelligence - Frontend

Modern React/Next.js frontend for the Document Intelligence System.

## ✨ Features

- 📤 **Drag & Drop Document Upload** - Upload PDFs, images, DOCX, and text files
- 💬 **AI-Powered Query Interface** - Ask questions about your documents in natural language
- 📊 **Document Management** - View uploaded documents and extraction results
- 🎨 **Modern UI** - Beautiful, responsive interface built with Tailwind CSS
- 🔥 **Firebase Integration** - Optional cloud storage support
- ⚡ **Real-time Processing** - See OCR and extraction results immediately

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install
# or
yarn install
```

### Configuration

1. Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

2. Update `.env.local` with your configuration:
```env
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Firebase (Optional - for cloud storage)
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

### Running

```bash
# Development mode
npm run dev
# or
yarn dev

# Production build
npm run build
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📂 Project Structure

```
front-end/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx             # Home page
│   └── globals.css          # Global styles
├── components/
│   ├── DocumentUpload.tsx   # File upload component
│   ├── QueryInterface.tsx   # AI chat interface
│   └── DocumentList.tsx     # Document list view
├── public/                  # Static assets
├── .env.example             # Environment template
├── next.config.js           # Next.js configuration
├── tailwind.config.js       # Tailwind CSS configuration
└── package.json             # Dependencies
```

## 🎯 Usage

### 1. Upload Documents

- Click "Upload Document" tab
- Drag & drop a file or click to browse
- Supports: PDF, PNG, JPG, DOCX, TXT
- View extracted information and classification results

### 2. Query Documents

- Click "Query Documents" tab
- Ask questions in natural language:
  - "What is the applicant's name?"
  - "When was this document filed?"
  - "Summarize the document"
- View AI responses with source evidence

### 3. View Documents

- Click "Documents" tab
- See all uploaded documents
- View extraction results and metadata

## 🎨 Features in Detail

### Document Upload
- Drag & drop interface
- Multi-format support (PDF, images, DOCX, TXT)
- Real-time processing feedback
- Displays:
  - Document classification
  - Extracted fields
  - OCR confidence scores
  - Processing time

### Query Interface
- Chat-like interface
- Natural language understanding
- Shows source evidence for answers
- Confidence scores for results
- Markdown support in responses

### Document List
- Grid view of all documents
- Quick-view extraction results
- Processing status indicators
- Firebase sync status

## 🔧 Customization

### Styling

Edit `tailwind.config.js` to customize colors and theme:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom colors
      },
    },
  },
}
```

### API Configuration

Update API URL in `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

## 📱 Mobile Support

The frontend is fully responsive and works on:
- 📱 Mobile devices (iOS/Android)
- 📲 Tablets
- 💻 Desktop browsers

## 🚢 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker

```bash
# Build image
docker build -t sih-frontend .

# Run container
docker run -p 3000:3000 sih-frontend
```

### Static Export

```bash
# Build static site
npm run build

# Deploy the 'out' folder to any static host
```

## 🔐 Security

- Never commit `.env.local` with real credentials
- Use environment variables for all sensitive data
- Enable CORS only for trusted domains in production
- Validate all file uploads on the backend

## 📊 Performance

- Code splitting with Next.js
- Image optimization
- Lazy loading components
- Optimized bundle size

## 🐛 Troubleshooting

### Backend Connection Issues

**Error:** "Failed to upload document"

**Fix:**
1. Check backend is running: `http://localhost:8000/docs`
2. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check CORS is enabled in backend

### Build Errors

**Error:** "Module not found"

**Fix:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### Styling Issues

**Error:** Tailwind classes not working

**Fix:**
```bash
npm run dev
# or clear Next.js cache
rm -rf .next
```

## 📚 Tech Stack

- **Framework:** Next.js 14
- **UI Library:** React 18
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **HTTP Client:** Axios
- **File Upload:** React Dropzone
- **Markdown:** React Markdown
- **Language:** TypeScript

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📄 License

Part of SIH 2024 Project

## 🆘 Support

For issues or questions:
- Check backend API is running
- Review console logs
- Check network requests in DevTools
- Refer to backend documentation

---

**Built for SIH 2024** 🚀
