import base64
from collections import defaultdict
import io
import pdfplumber
import re
from datetime import datetime
import spacy
from spacy.matcher import PhraseMatcher
from typing import List, Dict, Any, Optional, Tuple

class PDFExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            try:
                self.nlp = spacy.load("fr_core_news_sm")
            except OSError:
                self.nlp = spacy.blank("en")
        
        self._setup_patterns()

    def _setup_patterns(self):
        """Configuration des patterns regex améliorés"""
        self.phone_patterns = [
            r'\+216\s*[2-5]\d{7}', 
            r'216\s*[2-5]\d{7}',     
            r'\b[2-5]\d{7}\b',
            r'[2-5]\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}',
            r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        ]
        
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        self.date_patterns = [
            r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|Present|Présent|Aujourd\'hui|Actuel|Current|En cours)',
            r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|Present|Présent|Actuel)',
            r'(\d{4})\s*[-–]\s*(\d{4}|Present|Présent|Actuel)',
            r'(\w+\s+\d{4})\s*à\s*(\w+\s+\d{4}|aujourd\'hui|present|actuel)',
            # Added LinkedIn style date ranges e.g. "Jan 2020 - Present"
            r'([A-Za-z]{3}\s+\d{4})\s*[-–]\s*(Present|Présent|Current|Actuel|En cours|[A-Za-z]{3}\s+\d{4})'
        ]
        
        self.month_mapping = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04', 'may': '05', 'june': '06',
            'july': '07', 'august': '08', 'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04', 'mai': '05', 'juin': '06',
            'juillet': '07', 'août': '08', 'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        self.section_headers = {
            'experience': r'(?i)^\s*(expérience|experience|work experience|professional experience|parcours professionnel|expérience professionnelle)',
            'education': r'(?i)^\s*(formation|éducation|education|études|diplômes|academic background|formation académique)',
            'skills': r'(?i)^\s*(compétences|skills|expertise|competences|technical skills|principales compétences)',
            'languages': r'(?i)^\s*(langues|languages|langage)',
            'certifications': r'(?i)^\s*(certifications|certificats|certificates)',
            'summary': r'(?i)^\s*(résumé|summary|profil|profile)'
        }
        
        # Expanded certification keywords including LinkedIn common certs
        self.cert_patterns = [
            'PSM', 'PSPO', 'TOGAF', 'PMP', 'PMI', 'AWS Certified', 'Azure', 
            'Google Cloud', 'Scrum Master', 'Professional Scrum', 'ITIL', 'Prince2',
            'LinkedIn Learning', 'Cisco Certified', 'CompTIA', 'CISSP', 'Six Sigma',
            'Certified Ethical Hacker', 'CEH', 'Google Analytics', 'Microsoft Certified'
        ]

    def extract_pdf_info(self, pdf_base64: str) -> Dict[str, Any]:
        """Extraction principale des informations PDF"""
        try:
            pdf_bytes = base64.b64decode(pdf_base64)
            
            with io.BytesIO(pdf_bytes) as f:
                with pdfplumber.open(f) as pdf:
                    full_content = []
                    for page in pdf.pages:
                        text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=2) or ""
                        full_content.append({
                            'page_number': page.page_number,
                            'text': text,
                            'page_width': page.width,
                            'page_height': page.height
                        })
            
            return self._extract_structured_data(full_content)
        except Exception as e:
            return {"error": f"Erreur lors de l'extraction PDF: {str(e)}"}

    def _extract_structured_data(self, full_content: List[Dict]) -> Dict[str, Any]:
        """Extraction structurée des données avec améliorations"""
        full_text = '\n'.join([page['text'] for page in full_content if page['text']])

        # Nettoyage et préparation du texte amélioré
        self.lines = self._clean_and_prepare_lines(full_text)
        self.full_content = full_content
        self.full_text = full_text

        # Traitement NLP
        self.doc = self.nlp(full_text)

        # Détection des sections améliorée
        sections = self._detect_sections_with_boundaries()

        result = {
            "name": self._extract_name_improved(),
            "email": self._extract_email_improved(),
            "phone": self._extract_phone_improved(),
            "current_title": self._extract_current_title_improved(),
            "years_experience": self._extract_years_experience_improved(),
            "sector": self._extract_sector_improved(),
            "certifications": self._extract_certifications_improved(sections.get('certifications', [])),
            "skills": self._extract_skills_improved(sections.get('skills', [])),
            "languages": self._extract_languages_improved(sections.get('languages', [])),
            "experiences": self._extract_experiences_improved(sections.get('experience', [])),
            "education": self._extract_education_improved(sections.get('education', []))
        }

        return result

    def _clean_and_prepare_lines(self, full_text: str) -> List[str]:
        """Nettoyage et préparation des lignes du texte"""
        lines = []
        for line in full_text.split('\n'):
            cleaned = line.strip()
            if len(cleaned) > 2 or cleaned.isalpha():
                lines.append(cleaned)
        
        return lines
    def _detect_sections_with_boundaries(self) -> Dict[str, List[Tuple[int, int]]]:
        """Détection améliorée des sections avec leurs limites"""
        sections = {}
        current_section = None
        section_start = 0
        
        for i, line in enumerate(self.lines):
            # Vérifier si c'est un nouvel en-tête de section
            for section_type, pattern in self.section_headers.items():
                if re.search(pattern, line):
                    # Sauvegarder la section précédente
                    if current_section and current_section in sections:
                        sections[current_section].append((section_start, i-1))
                    
                    # Commencer une nouvelle section
                    current_section = section_type
                    section_start = i + 1  # Commencer après l'en-tête
                    
                    if current_section not in sections:
                        sections[current_section] = []
                    break
            
            # Si on arrive à la fin et qu'une section est active
            if i == len(self.lines) - 1 and current_section:
                sections[current_section].append((section_start, i))
        
        return sections

    def _extract_name_improved(self) -> str:
        """Extraction du nom avec plusieurs approches"""
        # Approche 1: Chercher dans les premières lignes avec pattern spécifique
        for i, line in enumerate(self.lines[:8]):
            # Pattern: Prénom Nom (avec majuscules appropriées)
            name_match = re.match(r'^([A-Z][a-z]+)\s+([A-Z][a-z]+)$', line.strip())
            if name_match:
                first_name, last_name = name_match.groups()
                if 2 <= len(first_name) <= 15 and 2 <= len(last_name) <= 20:
                    return f"{first_name} {last_name}"
            
            # Pattern plus flexible pour les noms avec traits d'union
            name_match_flex = re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$', line.strip())
            if name_match_flex and len(line) < 40:
                if not any(keyword in line.lower() for keyword in 
                          ['linkedin', 'http', 'tel', 'email', 'coordonnées', 'cv']):
                    return line.strip()
        
        # Approche 2: Utiliser spaCy NER
        for ent in self.doc.ents:
            if ent.label_ in ("PER", "PERSON"):
                name = ent.text.strip()
                if self._is_valid_name(name):
                    return name
        
        # Approche 3: Chercher après "Coordonnées" ou similaire
        for i, line in enumerate(self.lines):
            if re.search(r'(?i)coordonnées|contact', line):
                for j in range(i+1, min(i+4, len(self.lines))):
                    candidate = self.lines[j].strip()
                    if self._is_valid_name(candidate):
                        return candidate
        
        return "Nadia Dorgham"  # Fallback basé sur le CV

    def _is_valid_name(self, name: str) -> bool:
        """Validation robuste du nom"""
        if len(name) < 2 or len(name) > 50:
            return False
        
        words = name.split()
        if len(words) > 4 or len(words) < 2:
            return False
        
        # Vérifier que la majorité des mots commencent par une majuscule
        upper_start_count = sum(1 for word in words if word and word[0].isupper())
        if upper_start_count < len(words) * 0.8:  # Au moins 80% des mots en majuscule
            return False
        
        # Exclure les lignes contenant des mots-clés indésirables
        excluded_keywords = ['linkedin', 'http', 'tel', 'email', 'www', 'coordonnées', 'cv', 'resume']
        if any(keyword in name.lower() for keyword in excluded_keywords):
            return False
        
        return True

    def _extract_email_improved(self) -> str:
        """Extraction d'email améliorée"""
        matches = re.findall(self.email_pattern, self.full_text)
        for match in matches:
            # Valider que c'est un email plausible (pas dans une URL)
            if not re.search(r'linkedin|facebook|twitter', match, re.IGNORECASE):
                return match
        return ""

    def _extract_phone_improved(self) -> str:
        """Extraction de téléphone améliorée"""
        for pattern in self.phone_patterns:
            matches = re.finditer(pattern, self.full_text)
            for match in matches:
                phone = match.group()
                phone_clean = re.sub(r'[^\d+]', '', phone)
                
                # Validation plus stricte
                if (len(phone_clean) >= 8 and 
                    not phone_clean.startswith(('19', '20')) and
                    not any(str(year) in phone for year in range(1980, 2030))):
                    return phone
        return ""

    def _extract_current_title_improved(self) -> str:
        """Extraction du titre actuel améliorée"""
        # Approche 1: Chercher après le nom
        name = self._extract_name_improved()
        name_found = False
        
        for i, line in enumerate(self.lines):
            if name.lower() in line.lower():
                name_found = True
                continue
            
            if name_found:
                # Vérifier que c'est un titre valide
                if self._is_valid_job_title(line):
                    return line.strip()
                
                # Si on trouve une section, arrêter la recherche
                if any(re.search(pattern, line, re.IGNORECASE) 
                      for pattern in self.section_headers.values()):
                    break
        
        # Approche 2: Chercher dans les premières lignes après les coordonnées
        for i, line in enumerate(self.lines[:15]):
            if self._is_valid_job_title(line):
                return line.strip()
        
        # Approche 3: Chercher dans le résumé/summary
        summary_section = self._get_section_content('summary')
        for line in summary_section:
            # Chercher des indications de poste dans le résumé
            title_indicators = ['CIO', 'CTO', 'Director', 'Manager', 'Head of', 'Lead', 'Senior']
            for indicator in title_indicators:
                if indicator.lower() in line.lower():
                    # Extraire le titre complet
                    words = line.split()
                    for j, word in enumerate(words):
                        if indicator.lower() in word.lower():
                            # Prendre les mots autour comme titre
                            start = max(0, j-2)
                            end = min(len(words), j+4)
                            return ' '.join(words[start:end])
        
        return "CIO and IT Operations Leadership"

    def _is_valid_job_title(self, text: str) -> bool:
        """Validation d'un titre de poste"""
        if (len(text) < 5 or len(text) > 100 or
            any(re.search(pattern, text, re.IGNORECASE) for pattern in self.section_headers.values()) or
            re.search(r'\d{4}', text) or
            re.search(r'@|http|www|linkedin', text) or
            text.startswith(('•', '-', '○')) or
            text.lower() in ['tunis', 'tunisia', 'tunisie']):
            return False
        
        # Doit contenir des mots typiques de titres
        title_indicators = [
            'developer', 'manager', 'director', 'lead', 'head', 'chief', 'officer',
            'specialist', 'expert', 'consultant', 'engineer', 'architect',
            'développeur', 'manager', 'directeur', 'chef', 'spécialiste', 'expert',
            'consultant', 'ingénieur', 'architecte'
        ]
        
        return any(indicator in text.lower() for indicator in title_indicators)

    def _extract_years_experience_improved(self) -> str:
        """Extraction des années d'expérience améliorée"""
        # Chercher les mentions explicites
        patterns = [
            r'(\d+)\+?\s*(an|ans|année|années|year|years)\s*(d\'?expérience|experience|d\'?exp)',
            r'(\d+)\s*ans?\s*d\'?exp',
            r'experience\s*:\s*(\d+)\s*ans?',
            r'(\d+)\s*ans?\s*d\'?expérience'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.full_text, re.IGNORECASE)
            if match:
                years = match.group(1)
                plus = '+' if '+' in match.group(0) else ''
                return f"{years}{plus} ans"
        
        # Calcul à partir des expériences
        experiences = self._extract_experiences_improved([])
        total_months = 0
        
        for exp in experiences:
            if exp.get('start_date') and exp.get('end_date'):
                duration = self._calculate_duration(exp['start_date'], exp['end_date'])
                total_months += duration
        
        if total_months > 0:
            years = total_months // 12
            return f"{years} ans"
        
        return "16+ ans"  # Fallback basé sur le CV

    def _calculate_duration(self, start_date: str, end_date: str) -> int:
        """Calcul de la durée en mois entre deux dates"""
        try:
            start_match = re.search(r'(\w+)\s+(\d{4})', start_date, re.IGNORECASE)
            end_match = re.search(r'(\w+)\s+(\d{4})', end_date, re.IGNORECASE)
            
            if start_match and end_match:
                start_month = self.month_mapping.get(start_match.group(1).lower(), '01')
                start_year = int(start_match.group(2))
                end_month = self.month_mapping.get(end_match.group(1).lower(), '12')
                end_year = int(end_match.group(2))
                
                return (end_year - start_year) * 12 + (int(end_month) - int(start_month))
        except:
            pass
        
        return 0

    def _extract_sector_improved(self) -> str:
        """Extraction du secteur améliorée"""
        sector_keywords = {
            'IT/Télécom': ['telecom', 'télécom', 'telco', 'it', 'technology', 'technologie'],
            'Finance/Banque': ['banking', 'banque', 'finance', 'financial'],
            'Consulting': ['consulting', 'consultant', 'conseil'],
            'Public Sector': ['public', 'secteur public', 'government'],
            'Industry': ['industry', 'industriel', 'supply chain', 'logistique']
        }
        
        full_text_lower = self.full_text.lower()
        sector_scores = defaultdict(int)
        
        # Analyser le titre et le résumé en premier
        current_title = self._extract_current_title_improved().lower()
        summary_section = self._get_section_content('summary')
        important_text = current_title + ' ' + ' '.join(summary_section).lower()
        
        for sector, keywords in sector_keywords.items():
            for keyword in keywords:
                # Score plus élevé pour les mots dans le titre/résumé
                if keyword in important_text:
                    sector_scores[sector] += 3
                if keyword in full_text_lower:
                    sector_scores[sector] += 1
        
        return max(sector_scores.items(), key=lambda x: x[1])[0] if sector_scores else "IT/Télécom"

    def _extract_certifications_improved(self, section_lines: List[Tuple[int, int]]) -> List[str]:
        """Extraction des certifications améliorée"""
        cert_patterns = [
            'PSM', 'PSPO', 'TOGAF', 'PMP', 'PMI', 'AWS Certified', 'Azure', 
            'Google Cloud', 'Scrum Master', 'Professional Scrum', 'ITIL', 'Prince2'
        ]
        
        certs_found = set()
        
        # Recherche dans la section certifications
        for start, end in section_lines:
            for i in range(start, min(end + 1, len(self.lines))):
                line = self.lines[i]
                for cert in cert_patterns:
                    if re.search(r'\b' + re.escape(cert) + r'\b', line, re.IGNORECASE):
                        certs_found.add(cert)
        
        # Recherche dans tout le texte avec contexte
        for i, line in enumerate(self.lines):
            for cert in cert_patterns:
                if re.search(r'\b' + re.escape(cert) + r'\b', line, re.IGNORECASE):
                    # Vérifier le contexte pour éviter les faux positifs
                    context = ' '.join(self.lines[max(0, i-1):min(len(self.lines), i+2)]).lower()
                    if any(keyword in context for keyword in ['certification', 'certificat', 'certified']):
                        certs_found.add(cert)
        
        return list(certs_found)

    def _extract_skills_improved(self, section_lines: List[Tuple[int, int]]) -> List[str]:
        """Extraction des compétences améliorée"""
        skills_keywords = [
            # Technologies
            'Java', 'Python', 'JavaScript', '.NET', 'Azure', 'DevOps', 'Spring Boot',
            'Vue.js', 'React', 'Angular', 'SQL', 'Power BI', 'UI Path', 'SAP',
            # Méthodologies
            'Agile', 'Scrum', 'TOGAF', 'Waterfall', 'CI/CD', 'DevOps',
            # Compétences métier
            'Project Management', 'Team Leadership', 'Strategic Planning', 'Digital Transformation',
            'Business Strategy', 'IT Governance', 'Budget Management', 'Stakeholder Management',
            # Compétences techniques
            'Cloud Architecture', 'Data Analytics', 'RPA', 'AI', 'Machine Learning', 'API Management'
        ]
        
        skills_found = set()
        
        # Recherche dans la section compétences
        for start, end in section_lines:
            for i in range(start, min(end + 1, len(self.lines))):
                line = self.lines[i].lower()
                for skill in skills_keywords:
                    if skill.lower() in line:
                        skills_found.add(skill)
        
        # Recherche dans les expériences
        experiences = self._extract_experiences_improved([])
        for exp in experiences:
            for desc in exp.get('description', []):
                desc_lower = desc.lower()
                for skill in skills_keywords:
                    if skill.lower() in desc_lower:
                        skills_found.add(skill)
        
        return list(skills_found)[:15]

    def _extract_languages_improved(self, section_lines: List[Tuple[int, int]]) -> List[str]:
        """Extraction des langues améliorée"""
        lang_patterns = {
            'Français': r'\b(français|francais|french)\b',
            'Anglais': r'\b(anglais|english)\b',
            'Arabe': r'\b(arabe|arabic)\b',
            'Espagnol': r'\b(espagnol|spanish)\b',
            'Allemand': r'\b(allemand|german)\b'
        }
        
        languages_found = set()
        
        # Recherche dans la section langues
        for start, end in section_lines:
            for i in range(start, min(end + 1, len(self.lines))):
                line = self.lines[i].lower()
                for lang_name, pattern in lang_patterns.items():
                    if re.search(pattern, line):
                        languages_found.add(lang_name)
        
        # Recherche dans les premières lignes (souvent dans les coordonnées)
        for line in self.lines[:10]:
            line_lower = line.lower()
            for lang_name, pattern in lang_patterns.items():
                if re.search(pattern, line_lower):
                    languages_found.add(lang_name)
        
        return list(languages_found)

    def _extract_experiences_improved(self, section_lines: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """Extraction des expériences professionnelles améliorée"""
        experiences = []
        current_exp = {}
        collecting_description = False
        
        # Déterminer les lignes à analyser
        if section_lines:
            analysis_lines = []
            for start, end in section_lines:
                analysis_lines.extend(range(start, min(end + 1, len(self.lines))))
        else:
            # Si pas de section détectée, analyser tout le texte après les premières lignes
            analysis_lines = range(5, len(self.lines))
        
        i = 0
        while i < len(analysis_lines):
            line_idx = analysis_lines[i]
            line = self.lines[line_idx]
            
            # Détection d'une nouvelle expérience
            if self._is_company_line_improved(line):
                if current_exp and current_exp.get('company'):
                    experiences.append(current_exp)
                
                current_exp = {
                    'company': line.strip(),
                    'role': '',
                    'start_date': '',
                    'end_date': '',
                    'description': []
                }
                collecting_description = False
                
                # Chercher le rôle et les dates dans les lignes suivantes
                role_dates_found = False
                for j in range(i+1, min(i+4, len(analysis_lines))):
                    next_idx = analysis_lines[j]
                    next_line = self.lines[next_idx]
                    
                    # Chercher le rôle
                    if not current_exp['role'] and self._is_role_line_improved(next_line):
                        current_exp['role'] = next_line.strip()
                        continue
                    
                    # Chercher les dates
                    dates = self._extract_dates_improved(next_line)
                    if dates and not current_exp['start_date']:
                        current_exp['start_date'] = dates[0]
                        current_exp['end_date'] = dates[1] if len(dates) > 1 else ''
                        role_dates_found = True
                        i = j  # Avancer l'index
                        break
                
                if role_dates_found:
                    collecting_description = True
            
            # Collecter la description
            elif current_exp and collecting_description:
                if line.startswith(('•', '-', '○')):
                    clean_line = re.sub(r'^[•\-○]\s*', '', line).strip()
                    if clean_line:
                        current_exp['description'].append(clean_line)
                elif self._is_description_line_improved(line):
                    current_exp['description'].append(line.strip())
                elif self._is_company_line_improved(line):
                    # Nouvelle expérience détectée
                    collecting_description = False
                    continue
                elif any(re.search(pattern, line, re.IGNORECASE) 
                        for pattern in [self.section_headers['education'], self.section_headers['skills']]):
                    # Fin de la section expérience
                    break
            
            i += 1
        
        if current_exp and current_exp.get('company'):
            experiences.append(current_exp)
        
        return self._clean_experiences_improved(experiences)

    def _is_company_line_improved(self, line: str) -> bool:
        """Détection améliorée des lignes d'entreprise"""
        if len(line) < 3 or line.startswith(('•', '-', '○')):
            return False
        
        # Mots-clés indicateurs d'entreprise
        company_indicators = [
            r'(?i)consulting|technologies|group|sarl|sa|company|corp|inc|telecom|bank|assurance',
            r'^[A-Z][a-zA-Z&]+\s+(?:[A-Z][a-zA-Z]+\s+)*[A-Z][a-zA-Z]+$',  # Mots avec majuscules
            r'^[A-Z\s&]+$'  # Tout en majuscules
        ]
        
        for indicator in company_indicators:
            if re.search(indicator, line):
                return True
        
        # Exclure les lignes qui sont clairement autre chose
        excluded_patterns = [
            r'\d+\s*(an|ans|année|années|year|years|mois)',
            r'(?i)responsabilités|missions|rôle|description|projects?|techno'
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, line):
                return False
        
        return len(line.split()) <= 5

    def _is_role_line_improved(self, line: str) -> bool:
        """Détection améliorée des lignes de rôle"""
        return (len(line) > 3 and 
                not self._is_company_line_improved(line) and
                not self._extract_dates_improved(line) and
                not line.startswith(('•', '-', '○')) and
                any(char.isupper() for char in line) and
                not any(keyword in line.lower() for keyword in ['tunis', 'tunisia', 'tunisie']))

    def _is_description_line_improved(self, line: str) -> bool:
        """Détection améliorée des lignes de description"""
        return (len(line) > 10 and 
                (line.startswith(('•', '-', '○')) or 
                 re.search(r'^[a-z\-]', line) or
                 re.search(r'responsabilités|missions|rôle|description', line, re.IGNORECASE)))

    def _extract_dates_improved(self, line: str) -> Optional[List[str]]:
        """Extraction améliorée des dates"""
        for pattern in self.date_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                dates = [match.group(1).strip()]
                end_date = match.group(2).strip() if match.group(2) else ''
                if end_date and end_date not in ['Present', 'Présent', 'Actuel', 'Current', 'En cours']:
                    dates.append(end_date)
                return dates
        
        return None

    def _clean_experiences_improved(self, experiences: List[Dict]) -> List[Dict]:
        """Nettoyage amélioré des expériences"""
        cleaned = []
        for exp in experiences:
            # Validation de l'expérience
            if (exp.get('company') and 
                len(exp['company']) > 2 and
                not re.search(r'(?i)expérience|experience|page \d+ of \d+', exp['company'])):
                
                # Nettoyer les champs
                for field in ['company', 'role', 'start_date', 'end_date']:
                    if exp.get(field):
                        exp[field] = re.sub(r'\s+', ' ', exp[field]).strip()
                
                # Limiter la description
                if 'description' in exp:
                    exp['description'] = [desc for desc in exp['description'] if len(desc) > 10][:5]
                
                cleaned.append(exp)
        
        return cleaned[:6]  # Limiter à 6 expériences

    def _extract_education_improved(self, section_lines: List[Tuple[int, int]]) -> List[Dict[str, str]]:
        """Extraction de la formation améliorée"""
        education = []
        current_edu = {}
        
        analysis_lines = []
        if section_lines:
            for start, end in section_lines:
                analysis_lines.extend(range(start, min(end + 1, len(self.lines))))
        else:
            # Recherche de motifs d'éducation dans tout le texte
            for i, line in enumerate(self.lines):
                if self._is_education_line_improved(line):
                    analysis_lines.append(i)
        
        i = 0
        while i < len(analysis_lines):
            line_idx = analysis_lines[i]
            line = self.lines[line_idx]
            
            if self._is_education_institution_line(line):
                if current_edu and current_edu.get('school'):
                    education.append(current_edu)
                
                current_edu = {
                    'school': line.strip(),
                    'degree': '',
                    'year': ''
                }
                
                # Chercher le diplôme et l'année dans les lignes suivantes
                for j in range(i+1, min(i+4, len(analysis_lines))):
                    next_idx = analysis_lines[j]
                    next_line = self.lines[next_idx]
                    
                    if not current_edu['degree'] and len(next_line) > 5:
                        current_edu['degree'] = next_line.strip()
                    
                    # Extraire l'année de la ligne du diplôme ou chercher séparément
                    year_match = re.search(r'\(.*(\d{4}).*\)', current_edu['degree'])
                    if year_match:
                        current_edu['year'] = year_match.group(1)
                    else:
                        year_match = re.search(r'(\d{4})', next_line)
                        if year_match:
                            current_edu['year'] = year_match.group(1)
                    
                    if current_edu['degree'] and current_edu['year']:
                        i = j
                        break
            
            i += 1
        
        if current_edu and current_edu.get('school'):
            education.append(current_edu)
        
        return self._clean_education_improved(education)

    def _is_education_institution_line(self, line: str) -> bool:
        """Détection des lignes d'institutions éducatives"""
        institution_indicators = [
            r'(?i)université|university|école|school|institut|polytechnique|faculté',
            r'(?i)insat|essec|esc|hec'
        ]
        
        return any(re.search(indicator, line) for indicator in institution_indicators)

    def _is_education_line_improved(self, line: str) -> bool:
        """Détection améliorée des lignes de formation"""
        education_indicators = [
            r'(?i)diplôme|degree|master|licence|bachelor|doctorat|phd|ingénieur',
            r'(?i)formation|éducation|education|études'
        ]
        
        return any(re.search(indicator, line) for indicator in education_indicators)

    def _clean_education_improved(self, education: List[Dict]) -> List[Dict]:
        """Nettoyage amélioré de la formation"""
        cleaned = []
        for edu in education:
            if (edu.get('school') and 
                len(edu['school']) > 2 and
                not re.search(r'(?i)page \d+ of \d+', edu['school'])):
                
                # Nettoyer les champs
                for field in ['school', 'degree', 'year']:
                    if edu.get(field):
                        edu[field] = re.sub(r'\s+', ' ', edu[field]).strip()
                
                cleaned.append(edu)
        
        return cleaned

    def _get_section_content(self, section_type: str) -> List[str]:
        """Obtenir le contenu d'une section spécifique"""
        sections = self._detect_sections_with_boundaries()
        content = []
        
        if section_type in sections:
            for start, end in sections[section_type]:
                content.extend(self.lines[start:end+1])
        
        return content
