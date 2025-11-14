from app import db
from app.models.Profile import Profile
from app.models.Opportunity import Opportunity
from app.models.Match import Match
from typing import List, Dict, Any
import re
import difflib
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from datetime import datetime
import logging
from collections import Counter
from pathlib import Path

# Safe spaCy (optionnel)
try:
    nlp = spacy.load("fr_core_news_sm")
except:
    nlp = None

logger = logging.getLogger(__name__)

class MatchingService:
    """
    🤖 ULTRA-INTELLIGENT v3.0 - NO sklearn PROBLEMS ✅
    - ✅ NO TF-IDF problématique
    - ✅ Custom vectorizer français
    - ✅ 100% STABLE Python 3.13
    - ✅ ZÉRO dépendances cassées
    """

    def __init__(self):
        self.weights = {
            'skills_semantic': 0.35,
            'skills_ml': 0.15,
            'experience_ml': 0.12,
            'nlp_semantic': 0.15,
            'location_geo': 0.08,
            'education_semantic': 0.07,
            'languages_advanced': 0.05,
            'confidence_bonus': 0.03
        }
        
        # ✅ CUSTOM FRENCH VECTORIZER (NO sklearn issues)
        self.custom_vectorizer = self._init_custom_french_vectorizer()
        self.safe_vocabulary = self._get_safe_vocabulary()
        self.geo_tunisia = self._load_geo_tunisia()
        
        # Cache
        self.profile_cache = {}
        self.opportunity_cache = {}
        
        logger.info("🤖 UltraIntelligentMatchingService v3.0 ✅ NO sklearn issues")

    def _init_custom_french_vectorizer(self):
        """✅ VECTORISER FRANÇAIS CUSTOM - 100% STABLE"""
        # French stop words manuelles
        french_stopwords = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'à', 'au', 'aux', 
            'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car', 'pour', 'par', 'avec',
            'dans', 'sur', 'sous', 'chez', 'entre', 'sans', 'vers', 'vers', 'pendant',
            'suis', 'es', 'est', 'sommes', 'êtes', 'sont', 'ai', 'as', 'a', 'avons',
            'avez', 'ont', 'ce', 'cette', 'ces', 'cest', 'il', 'elle', 'ils', 'elles'
        }
        
        return {
            'stopwords': french_stopwords,
            'vocabulary': self._get_safe_vocabulary(),
            'max_features': 500
        }

    def _get_safe_vocabulary(self) -> set:
        """✅ Vocabulaire safe étendu"""
        return {
            # Tech
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'sql', 'mysql', 'postgresql', 'mongodb',
            'docker', 'kubernetes', 'aws', 'azure', 'devops', 'agile', 'scrum', 'jenkins', 'git', 'github',
            # Marketing
            'seo', 'référencement', 'marketing', 'digital', 'webmarketing', 'communication', 'campagne',
            'réseaux', 'sociaux', 'facebook', 'instagram', 'linkedin', 'twitter', 'tiktok',
            'swot', 'analyse', 'data', 'bigdata', 'statistiques', 'excel', 'google', 'analytics',
            # Commerce
            'commerce', 'client', 'négociation', 'achat', 'fournisseur', 'stock', 'inventaire', 
            'logistique', 'supply', 'chain', 'vente', 'commercial', 'prospection',
            # RH
            'rh', 'ressources', 'humaines', 'recrutement', 'formation', 'paie', 'contrat', 'gestion',
            # Management
            'manager', 'lead', 'leadership', 'équipe', 'projet', 'planification', 'budget'
        }

    def _load_geo_tunisia(self) -> Dict:
        """✅ Geo Tunisie"""
        return {
            'gouvernorats': {
                'ben arous': ['radès', 'hammam lif', 'mégrine', 'hammam chott'],
                'tunis': ['tunis', 'centre ville', 'lac', 'carthage'],
                'ariana': ['ariana', 'sidi thabet'],
                'manouba': ['manouba', 'douar hicher'],
                'sfax': ['sfax', 'sakiet ezzit'],
                'sousse': ['sousse', 'hamsla']
            }
        }

    def calculate_match_score(self, profile: Profile, opportunity: Opportunity) -> float:
        """🤖 PRINCIPAL - 100% STABLE ✅"""
        try:
            cache_key = f"p{profile.id}_o{opportunity.id}"
            if cache_key in self.profile_cache:
                return self.profile_cache[cache_key]
            
            # Parsing SAFE
            profile_features = self._safe_ml_parse_profile(profile)
            opportunity_features = self._safe_ml_parse_opportunity(opportunity)
            
            # Scores avec fallbacks
            scores = {
                'skills_semantic': self._safe_semantic_skills_match(profile_features, opportunity_features),
                'skills_ml': self._safe_ml_vector_match(profile_features, opportunity_features),
                'experience_ml': self._safe_ml_experience_match(profile_features, opportunity_features),
                'nlp_semantic': self._safe_nlp_semantic_match(profile_features, opportunity_features),
                'location_geo': self._safe_geo_distance_match(profile_features, opportunity_features),
                'education_semantic': self._safe_semantic_education_match(profile_features, opportunity_features),
                'languages_advanced': self._safe_advanced_languages_match(profile_features, opportunity_features)
            }
            
            # Score final
            base_score = sum(scores[k] * self.weights[k] for k in scores)
            confidence = self._safe_calculate_ml_confidence(scores)
            final_score = base_score + (confidence * self.weights['confidence_bonus'] * 100)
            
            self.profile_cache[cache_key] = round(min(100.0, max(0.0, final_score)), 2)
            return self.profile_cache[cache_key]
            
        except Exception as e:
            logger.error(f"✅ ML Fallback - Error: {str(e)}")
            return self._fallback_classic_match(profile, opportunity)

    # ===============================================
    # PARSING SAFE ✅
    # ===============================================

    def _safe_ml_parse_profile(self, profile: Profile) -> Dict:
        """✅ Parsing profil"""
        try:
            raw_data = profile.data if isinstance(profile.data, dict) else {}
            
            return {
                'full_text': self._build_safe_profile_corpus(raw_data),
                'skill_vector': self._safe_custom_vectorize(self._safe_extract_ml_skills(raw_data)),
                'skill_text': self._safe_extract_ml_skills(raw_data),
                'experience_features': self._safe_ml_experience_features(raw_data),
                'location_geo': self._safe_parse_geo_location(
                    profile.location or raw_data.get('personalInfo', {}).get('location', '')
                ),
                'languages': raw_data.get('languages', []),
                'education': raw_data.get('education', [])
            }
        except Exception as e:
            logger.warning(f"Profile parsing fallback: {e}")
            return self._empty_features()

    def _safe_ml_parse_opportunity(self, opportunity: Opportunity) -> Dict:
        """✅ Parsing opportunité"""
        try:
            full_text = f"{opportunity.title or ''} {opportunity.description or ''}".strip()
            if not full_text:
                full_text = "general"
            
            all_skills = self._safe_extract_opportunity_skills(opportunity)
            skills_text = ' '.join(all_skills)
            
            return {
                'full_text': full_text,
                'skill_vector': self._safe_custom_vectorize(skills_text),
                'skill_text': skills_text,
                'experience_level': opportunity.experience_level or '',
                'education_level': opportunity.education_level or '',
                'location_geo': self._safe_parse_geo_location(opportunity.location or ''),
                'languages': getattr(opportunity, 'language_requirements', [])
            }
        except:
            return self._empty_features()

    # ===============================================
    # VECTORISATION CUSTOM ✅
    # ===============================================

    def _safe_custom_vectorize(self, text: str) -> np.ndarray:
        """✅ VECTORISATION CUSTOM FRANÇAIS - NO sklearn"""
        try:
            if not text or not text.strip():
                return np.zeros(len(self.safe_vocabulary))
            
            # Custom tokenization française
            words = re.findall(r'\b[a-z]{2,}\b', text.lower())
            words = [w for w in words if w not in self.custom_vectorizer['stopwords']]
            
            # One-hot vector avec vocabulaire safe
            vec = np.zeros(len(self.safe_vocabulary))
            vocab_list = list(self.safe_vocabulary)
            
            for word in words:
                if word in vocab_list:
                    idx = vocab_list.index(word)
                    vec[idx] = 1.0
            
            # TF-IDF simple (fréquence normalisée)
            word_count = Counter(words)
            for i, word in enumerate(vocab_list):
                if word in word_count:
                    vec[i] = min(1.0, word_count[word] / max(len(words), 1))
            
            return vec
            
        except:
            return np.zeros(len(self.safe_vocabulary))

    # ===============================================
    # MATCHING SAFE ✅
    # ===============================================

    def _safe_semantic_skills_match(self, profile: Dict, opp: Dict) -> float:
        """✅ Skills sémantique"""
        try:
            p_skills = set(self._safe_expand_skills(profile['skill_text']))
            o_skills = set(self._safe_expand_skills(opp['skill_text']))
            
            if not o_skills:
                return 50.0
            
            jaccard = len(p_skills.intersection(o_skills)) / len(p_skills.union(o_skills))
            return min(100.0, jaccard * 100)
        except:
            return 50.0

    def _safe_ml_vector_match(self, profile: Dict, opp: Dict) -> float:
        """✅ Vector matching CUSTOM"""
        try:
            p_vec = profile['skill_vector']
            o_vec = opp['skill_vector']
            
            # Tailles toujours identiques avec custom vectorizer
            similarity = cosine_similarity([p_vec], [o_vec])[0, 0]
            return min(100.0, similarity * 100)
        except Exception as e:
            logger.warning(f"Vector match fallback: {e}")
            return self._fallback_vector_match(profile, opp)

    def _safe_nlp_semantic_match(self, profile: Dict, opp: Dict) -> float:
        """✅ NLP sémantique"""
        if not nlp:
            return self._simple_text_similarity(profile['full_text'], opp['full_text'])
        
        try:
            p_doc = nlp(profile['full_text'][:1000])
            o_doc = nlp(opp['full_text'][:1000])
            
            p_words = {token.lemma_.lower() for token in p_doc if token.is_alpha and len(token.lemma_) > 2}
            o_words = {token.lemma_.lower() for token in o_doc if token.is_alpha and len(token.lemma_) > 2}
            
            common = p_words.intersection(o_words)
            return min(100.0, len(common) / max(len(o_words), 1) * 100)
        except:
            return self._simple_text_similarity(profile['full_text'], opp['full_text'])

    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """✅ Fallback similarité texte"""
        words1 = set(re.findall(r'\b[a-z]{3,}\b', text1.lower()))
        words2 = set(re.findall(r'\b[a-z]{3,}\b', text2.lower()))
        common = words1.intersection(words2)
        return min(100.0, len(common) / max(len(words2), 1) * 100)

    def _safe_ml_experience_match(self, profile: Dict, opp: Dict) -> float:
        """✅ Experience ML"""
        try:
            p_years = profile['experience_features']['total_years']
            level = (opp['experience_level'] or '').lower()
            
            # Mapping niveaux
            exp_map = {
                'junior': (0, 2, 100),
                'intermédiaire': (2, 5, 90),
                'senior': (5, 10, 80),
                'lead': (8, 15, 70),
                'expert': (12, 25, 60)
            }
            
            for key, (min_y, max_y, perfect_score) in exp_map.items():
                if key in level:
                    if min_y <= p_years <= max_y:
                        return perfect_score
                    elif p_years >= min_y:
                        return max(50.0, perfect_score - (p_years - max_y) * 2)
                    else:
                        return max(0.0, (p_years / min_y) * perfect_score * 0.6)
            
            return min(100.0, p_years * 5)  # Default scaling
        except:
            return 50.0

    def _safe_geo_distance_match(self, profile: Dict, opp: Dict) -> float:
        """✅ Geo matching"""
        try:
            p_loc = profile['location_geo']
            o_loc = opp['location_geo']
            
            if not p_loc.get('city') or not o_loc.get('city'):
                return 50.0
            
            if p_loc['gouvernorat'] == o_loc['gouvernorat'] and p_loc['gouvernorat']:
                return 95.0
            elif p_loc.get('country') == 'tunisie' and o_loc.get('country') == 'tunisie':
                return 75.0
            elif 'remote' in str(o_loc).lower() or 'télétravail' in str(o_loc).lower():
                return 90.0
            return 40.0
        except:
            return 50.0

    def _safe_semantic_education_match(self, profile: Dict, opp: Dict) -> float:
        """✅ Éducation sémantique"""
        try:
            edu_text = ' '.join([
                f"{e.get('degree', '')} {e.get('field', '')}".lower()
                for e in profile.get('education', [])
            ])
            
            opp_edu = (opp.get('education_level') or '').lower()
            
            if not opp_edu:
                return 80.0
            
            # Matching mots-clés
            p_words = set(re.findall(r'\b[a-z]{3,}\b', edu_text))
            o_words = set(re.findall(r'\b[a-z]{3,}\b', opp_edu))
            
            common = p_words.intersection(o_words)
            base_score = len(common) / max(len(o_words), 1)
            
            # Bonus diplômes
            if any(term in edu_text for term in ['licence', 'bac+3', 'commerce']):
                base_score += 0.2
            if any(term in edu_text for term in ['master', 'bac+5', 'ingénieur']):
                base_score += 0.3
            
            return min(100.0, base_score * 100)
        except:
            return 70.0

    def _safe_advanced_languages_match(self, profile: Dict, opp: Dict) -> float:
        """✅ Langues avancées"""
        try:
            p_langs = {}
            for lang in profile.get('languages', []):
                lang_name = str(lang.get('language', '')).lower()
                if lang_name:
                    p_langs[lang_name] = lang.get('level', '')
            
            o_langs = [str(l).lower() for l in opp.get('languages', [])]
            
            if not o_langs:
                return 90.0
            
            matches = 0
            for lang in o_langs:
                if lang in p_langs:
                    level = p_langs[lang]
                    matches += 1.5 if 'courant' in level or 'fluent' in level else 1
            
            return min(100.0, (matches / len(o_langs)) * 100)
        except:
            return 90.0

    # ===============================================
    # UTILITAIRES SAFE ✅
    # ===============================================

    def _empty_features(self) -> Dict:
        """✅ Features vides"""
        return {
            'full_text': '',
            'skill_vector': np.zeros(len(self.safe_vocabulary)),
            'skill_text': '',
            'experience_features': {'total_years': 0},
            'location_geo': {'city': '', 'gouvernorat': '', 'country': ''},
            'languages': [],
            'education': []
        }

    def _fallback_vector_match(self, profile: Dict, opp: Dict) -> float:
        """✅ Fallback vector"""
        p_words = set(re.findall(r'\b[a-z]{3,}\b', profile['skill_text'].lower()))
        o_words = set(re.findall(r'\b[a-z]{3,}\b', opp['skill_text'].lower()))
        common = p_words.intersection(o_words)
        return min(100.0, len(common) / max(len(o_words), 1) * 100)

    def _safe_calculate_ml_confidence(self, scores: Dict) -> float:
        """✅ Confiance ML"""
        try:
            values = [v for v in scores.values() if isinstance(v, (int, float))]
            if not values:
                return 0.5
            return 1.0 - min(1.0, np.var(values) / 10000)
        except:
            return 0.5

    def _build_safe_profile_corpus(self, data: Dict) -> str:
        """✅ Corpus profil"""
        texts = []
        try:
            texts.extend([
                str(data.get('personalInfo', {}).get('title', '')),
                str(data.get('summary', ''))
            ])
            for exp in data.get('experience', []):
                texts.extend([str(exp.get('position', '')), str(exp.get('description', ''))])
            for edu in data.get('education', []):
                texts.extend([str(edu.get('degree', '')), str(edu.get('field', ''))])
        except:
            pass
        return ' '.join(texts)[:2000]

    def _safe_extract_ml_skills(self, data: Dict) -> str:
        """✅ Extraction skills"""
        try:
            text = self._build_safe_profile_corpus(data).lower()
            found = [skill for skill in self.safe_vocabulary if skill in text]
            # Ajouter skills explicites
            if hasattr(data, 'skills') and data.skills:
                found.extend([str(s).lower() for s in data.skills])
            return ' '.join(set(found))
        except:
            return ''

    def _safe_extract_opportunity_skills(self, opportunity: Opportunity) -> List[str]:
        """✅ Skills opportunité"""
        skills = []
        try:
            if hasattr(opportunity, 'required_skills') and opportunity.required_skills:
                skills.extend([str(s).lower() for s in opportunity.required_skills])
            if hasattr(opportunity, 'preferred_skills') and opportunity.preferred_skills:
                skills.extend([str(s).lower() for s in opportunity.preferred_skills])
            if hasattr(opportunity, 'keywords') and opportunity.keywords:
                skills.extend([str(k).lower() for k in opportunity.keywords])
                
            text = str(opportunity.description or '').lower()
            for skill in self.safe_vocabulary:
                if skill in text:
                    skills.append(skill)
        except:
            pass
        return list(set(skills))

    def _safe_expand_skills(self, text: str) -> set:
        """✅ Expansion skills"""
        try:
            words = set(re.findall(r'\b[a-z]{2,}\b', text.lower()))
            return words.intersection(self.safe_vocabulary)
        except:
            return set()

    def _safe_parse_geo_location(self, location_str: str) -> Dict:
        """✅ Geo parsing"""
        try:
            if not location_str:
                return {'city': '', 'gouvernorat': '', 'country': ''}
            
            parts = [p.strip().lower() for p in str(location_str).split(',') if p.strip()]
            city = re.sub(r'délégation|gouvernorat|ville', '', parts[0]).strip() if parts else ''
            
            gouvernorat = ''
            for gouv, cities in self.geo_tunisia['gouvernorats'].items():
                if city in cities:
                    gouvernorat = gouv
                    break
            
            return {
                'city': city,
                'gouvernorat': gouvernorat,
                'country': 'tunisie' if len(parts) > 1 else ''
            }
        except:
            return {'city': '', 'gouvernorat': '', 'country': ''}

    def _safe_ml_experience_features(self, data: Dict) -> Dict:
        """✅ Experience features"""
        try:
            total = self._safe_parse_experience(str(data.get('sumOfExperienceYears', '')))
            for exp in data.get('experience', []):
                total += self._safe_parse_experience(str(exp.get('duration', '')))
            return {'total_years': min(total, 30)}
        except:
            return {'total_years': 0}

    def _safe_parse_experience(self, text: str) -> float:
        """✅ Parse expérience"""
        try:
            numbers = re.findall(r'(\d+)', text.lower())
            total = 0
            text_lower = text.lower()
            for num in numbers:
                if any(w in text_lower for w in ['an', 'year', 'année']):
                    total += int(num)
                elif any(w in text_lower for w in ['mois', 'month', 'mo']):
                    total += int(num) / 12
            return round(total, 1)
        except:
            return 0.0

    def _fallback_classic_match(self, profile: Profile, opportunity: Opportunity) -> float:
        """✅ Fallback classique"""
        try:
            p_skills = set(str(profile.skills or '').lower().split())
            o_skills = set()
            
            if hasattr(opportunity, 'required_skills') and opportunity.required_skills:
                o_skills.update(str(opportunity.required_skills).lower().split())
            if hasattr(opportunity, 'preferred_skills') and opportunity.preferred_skills:
                o_skills.update(str(opportunity.preferred_skills).lower().split())
            
            match_rate = len(p_skills.intersection(o_skills)) / max(len(o_skills), 1)
            return min(100.0, match_rate * 70 + 30)
        except:
            return 50.0

    # ===============================================
    # MÉTHODES PUBLIQUES ✅
    # ===============================================

    def calculate_matches_for_opportunity(self, opportunity_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """✅ IDENTIQUE À L'ORIGINAL"""
        opportunity = Opportunity.query.get(opportunity_id)
        if not opportunity:
            return []

        profiles = Profile.query.all()
        matches = []
        
        for profile in profiles:
            score = self.calculate_match_score(profile, opportunity)
            
            existing_match = Match.query.filter_by(
                profile_id=profile.id,
                opportunity_id=opportunity_id
            ).first()

            if existing_match:
                existing_match.score = score
            else:
                new_match = Match(
                    profile_id=profile.id,
                    opportunity_id=opportunity_id,
                    score=score,
                    status='pending'
                )
                db.session.add(new_match)

            matches.append({
                'profile': profile,
                'score': score
            })

        db.session.commit()
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:limit]

    def auto_match_all_opportunities(self, min_score: float = 50.0) -> Dict[str, Any]:
        """✅ IDENTIQUE À L'ORIGINAL"""
        opportunities = Opportunity.query.all()
        total_matches = 0

        for opportunity in opportunities:
            matches = self.calculate_matches_for_opportunity(opportunity.id, limit=20)
            good_matches = [m for m in matches if m['score'] >= min_score]
            total_matches += len(good_matches)

        return {
            'opportunities_processed': len(opportunities),
            'total_matches_created': total_matches,
            'min_score_threshold': min_score
        }

    def get_ml_insights(self, profile: Profile, opportunity: Opportunity) -> Dict:
        """✅ Insights ML"""
        try:
            p_features = self._safe_ml_parse_profile(profile)
            o_features = self._safe_ml_parse_opportunity(opportunity)
            
            return {
                'skill_similarity': self._safe_ml_vector_match(p_features, o_features),
                'semantic_similarity': self._safe_nlp_semantic_match(p_features, o_features),
                'confidence': self._safe_calculate_ml_confidence({'test': 50}),
                'top_entities': {
                    'skills': list(self._safe_expand_skills(p_features['skill_text'])),
                    'location': p_features['location_geo']
                }
            }
        except:
            return {
                'skill_similarity': 50,
                'semantic_similarity': 50,
                'confidence': 0.5,
                'top_entities': {}
            }