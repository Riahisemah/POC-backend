# Vercel Deployment Size Optimization

## Tasks to Complete

- [x] Remove heavy dependencies from requirements.txt (spacy, sklearn, reportlab, pdfplumber, beautifulsoup4)
- [x] Conditionally import heavy libraries in services to avoid loading them unless needed
- [x] Create .vercelignore file to exclude unnecessary files from deployment
- [x] Test that core functionality still works after optimizations
- [ ] Deploy and verify size reduction

## Dependencies to Remove/Optimize

- spacy: Used in PDFExtractor and MatchingService - make optional
- sklearn: Used in PDFExtractor and MatchingService - replace with numpy-only alternatives
- reportlab: Used for PDF generation - remove if not critical
- pdfplumber: Used for PDF extraction - make optional
- beautifulsoup4: Used for web scraping - remove if not used

## Files to Modify

- requirements.txt: Remove heavy packages
- app/services/pdf_extractor.py: Add conditional imports
- app/services/matching_service.py: Add conditional imports
- app/services/linkedin_extractor.py: Add conditional imports
- app/services/profile_analyzer.py: Add conditional imports
- Create .vercelignore: Exclude development files, node_modules, etc.
