# Demo / Sample Data Guide

This guide explains how to test the multimodal functionality immediately.

## 1. Generate the sample PDF

```bash
cd backend
python ../scripts/create_sample_pdf.py
```

This creates `data/uploads/sample.pdf` with:
- Page 1: intro text about a transformer architecture
- Page 2: an **architecture diagram** (Figure 1) — encoder/attention/decoder boxes
- Page 3: attention explanation + a **bar chart** (Figure 2)
- Page 4: a results table

## 2. Start the app

```bash
# Terminal 1 — backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open http://localhost:5173

## 3. Upload the sample PDF

Go to **Documents** → drag in `data/uploads/sample.pdf` → wait for indexing to complete.

## 4. Test the three query modes

### Text-only query
```
What architecture does the paper propose?
```
→ Should retrieve the Page 1 text **and** the Figure 1 diagram (CLIP cross-modal match).

### Image-only query
```
[upload the diagram image]  (no text)
```
→ Should retrieve visually similar figures from the PDF.

### Text + image query
```
[upload the diagram] + "Explain this architecture"
```
→ Should retrieve both the diagram and the related text, and the VLM should explain it.

## 5. Verify transparency

For each answer, expand **Retrieved Evidence** to see:
- text chunks with page numbers + scores
- image thumbnails with captions + scores
- the pipeline strip (query type → retrieval → fusion → generation)

## Sample queries to try

| Query | Mode | Expected evidence |
|---|---|---|
| "What architecture does the paper propose?" | text | Page 1 text + Figure 1 |
| "How does the attention layer work?" | text | Page 3 text |
| "What were the results?" | text | Page 4 table |
| [upload Figure 1] "what is this?" | image+text | Figure 1 + Page 1/2 text |
| [upload Figure 2] | image | Figure 2 + Page 3 text |
