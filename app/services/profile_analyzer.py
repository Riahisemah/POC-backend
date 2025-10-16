from datetime import datetime

class ProfileAnalyzer:
    def __init__(self):
        self.skill_weights = {
            "python": 2, "java": 2, "javascript": 2, "react": 1.5, "angular": 1.5,
            "node.js": 1.5, "aws": 1.5, "docker": 1.5, "kubernetes": 1.5,
            "machine learning": 2, "ai": 2, "data science": 2
        }
    
    def analyze_profile(self, profile):
        """Analyze and score a profile"""
        analysis = {
            "score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "experience_level": "",
            "skill_gaps": []
        }
        
        # Calcul du score
        analysis["score"] = self._calculate_score(profile)
        
        # Points forts
        analysis["strengths"] = self._identify_strengths(profile)
        
        # Points faibles
        analysis["weaknesses"] = self._identify_weaknesses(profile)
        
        # Recommandations
        analysis["recommendations"] = self._generate_recommendations(profile)
        
        # Niveau d'expérience
        analysis["experience_level"] = self._determine_experience_level(profile)
        
        # Compétences manquantes (par secteur)
        analysis["skill_gaps"] = self._identify_skill_gaps(profile)
        
        return analysis
    
    def _calculate_score(self, profile):
        """Calculate profile score (0-100)"""
        score = 0
        
        # Expérience (max 40 points)
        years_exp = profile.get("years_experience", 0)
        score += min(40, years_exp * 4)
        
        # Compétences (max 30 points)
        skills = profile.get("skills", [])
        skill_score = sum(self.skill_weights.get(skill.lower(), 1) for skill in skills)
        score += min(30, skill_score)
        
        # Éducation (max 15 points)
        education = profile.get("education", [])
        if any("master" in deg.lower() or "mba" in deg.lower() for deg in education):
            score += 15
        elif any("licence" in deg.lower() or "bachelor" in deg.lower() for deg in education):
            score += 10
        elif education:
            score += 5
        
        # Langues (max 15 points)
        languages = profile.get("languages", [])
        if any("anglais" in lang.lower() and any(lvl in lang.lower() for lvl in ["avancé", "bilingue", "c1", "c2"]) for lang in languages):
            score += 10
        elif any("anglais" in lang.lower() for lang in languages):
            score += 5
        
        if len(languages) > 1:
            score += 5
        
        return min(100, round(score))
    
    def _identify_strengths(self, profile):
        """Identify profile strengths"""
        strengths = []
        years_exp = profile.get("years_experience", 0)
        skills = profile.get("skills", [])
        
        if years_exp >= 5:
            strengths.append(f"Expérience significative ({years_exp} ans)")
        
        if len(skills) >= 8:
            strengths.append("Large éventail de compétences techniques")
        
        if any("manager" in exp.get("role", "").lower() for exp in profile.get("experiences", [])):
            strengths.append("Expérience managériale")
        
        if any("master" in deg.get("degree", "").lower() or "mba" in deg.get("degree", "").lower() for deg in profile.get("education", [])):
            strengths.append("Formation avancée")
        
        return strengths
    
    def _identify_weaknesses(self, profile):
        """Identify profile weaknesses"""
        weaknesses = []
        skills = [s.lower() for s in profile.get("skills", [])]
        
        # Vérifier les compétences manquantes par secteur
        sector = profile.get("sector", "").lower()
        
        if sector in ["informatique", "technologie"]:
            if not any(s in skills for s in ["git", "version control"]):
                weaknesses.append("Maitrise des outils de versioning (Git)")
            if not any(s in skills for s in ["test", "testing", "qa"]):
                weaknesses.append("Expérience en tests logiciels")
        
        if len(profile.get("experiences", [])) < 2:
            weaknesses.append("Expérience professionnelle limitée")
        
        return weaknesses
    
    def _generate_recommendations(self, profile):
        """Generate career recommendations"""
        recommendations = []
        score = self._calculate_score(profile)
        sector = profile.get("sector", "").lower()
        
        if score < 60:
            recommendations.append("Envisager des formations complémentaires dans votre domaine")
        
        if sector == "informatique" and not any(s in profile.get("skills", []) for s in ["cloud", "aws", "azure", "gcp"]):
            recommendations.append("Développer des compétences cloud (AWS, Azure, GCP)")
        
        if len(profile.get("languages", [])) < 2:
            recommendations.append("Améliorer les compétences linguistiques, particulièrement en anglais")
        
        if not any("certification" in cert.lower() for cert in profile.get("certifications", [])):
            recommendations.append("Obtenir des certifications professionnelles reconnues")
        
        return recommendations
    
    def _determine_experience_level(self, profile):
        """Determine experience level"""
        years_exp = profile.get("years_experience", 0)
        
        if years_exp < 2:
            return "Débutant"
        elif years_exp < 5:
            return "Intermédiaire"
        elif years_exp < 10:
            return "Expérimenté"
        else:
            return "Expert"
    
    def _identify_skill_gaps(self, profile):
        """Identify skill gaps based on sector"""
        sector = profile.get("sector", "").lower()
        current_skills = [s.lower() for s in profile.get("skills", [])]
        skill_gaps = []
        
        sector_required_skills = {
            "informatique": ["git", "agile", "sql", "linux", "debugging"],
            "marketing": ["analytics", "seo", "content marketing", "social media", "google analytics"],
            "finance": ["excel", "financial modeling", "analysis", "accounting", "risk management"],
            "rh": ["recruitment", "onboarding", "training", "hr policies", "employee relations"]
        }
        
        if sector in sector_required_skills:
            for skill in sector_required_skills[sector]:
                if skill not in current_skills:
                    skill_gaps.append(skill)
        
        return skill_gaps