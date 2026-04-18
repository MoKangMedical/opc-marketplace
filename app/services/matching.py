"""
OPC Marketplace - 匹配服务
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.user import User, ClientProfile, ProviderProfile, ProviderSkill, IndustryExpertise
from app.models.project import Project, Skill, Match
from app.core.config import settings

class MatchingService:
    """智能匹配服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.weights = settings.MATCH_SCORE_WEIGHTS
    
    async def auto_match_project(self, project: Project) -> List[Dict[str, Any]]:
        """
        自动匹配项目
        
        Args:
            project: 项目对象
            
        Returns:
            匹配结果列表
        """
        # 获取可用的供给方
        providers = await self._get_available_providers(project)
        
        # 计算匹配分数
        matches = []
        for provider in providers:
            match_score = await self._calculate_match_score(project, provider)
            
            # 只返回分数大于阈值的匹配
            if match_score >= 50:
                match_reasons = await self._get_match_reasons(project, provider)
                
                matches.append({
                    "provider_id": str(provider.id),
                    "provider_name": provider.user.full_name if provider.user else "未知",
                    "professional_title": provider.professional_title,
                    "hourly_rate": float(provider.hourly_rate),
                    "match_score": match_score,
                    "match_reasons": match_reasons,
                    "skills": [ps.skill.name for ps in provider.skills] if provider.skills else [],
                    "availability": provider.availability
                })
        
        # 按匹配分数排序
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        # 限制返回数量
        return matches[:20]
    
    async def _get_available_providers(self, project: Project) -> List[ProviderProfile]:
        """获取可用的供给方"""
        # 构建查询
        query = (
            select(ProviderProfile)
            .options(
                selectinload(ProviderProfile.user),
                selectinload(ProviderProfile.skills).selectinload(ProviderSkill.skill),
                selectinload(ProviderProfile.industry_expertise)
            )
            .where(ProviderProfile.availability == "AVAILABLE")
        )
        
        # 地点偏好过滤
        if project.location_preference and project.location_preference != "ANY":
            # 这里简化处理，实际应该根据用户的位置信息进行匹配
            pass
        
        # 执行查询
        result = await self.db.execute(query)
        providers = result.scalars().all()
        
        return providers
    
    async def _calculate_match_score(self, project: Project, provider: ProviderProfile) -> float:
        """计算匹配分数"""
        score = 0.0
        
        # 1. 技能匹配 (35%)
        skill_score = await self._calculate_skill_match(project, provider)
        score += skill_score * self.weights["skill_match"]
        
        # 2. 经验匹配 (25%)
        experience_score = self._calculate_experience_match(project, provider)
        score += experience_score * self.weights["experience_match"]
        
        # 3. 预算匹配 (20%)
        budget_score = self._calculate_budget_match(project, provider)
        score += budget_score * self.weights["budget_match"]
        
        # 4. 地点匹配 (10%)
        location_score = self._calculate_location_match(project, provider)
        score += location_score * self.weights["location_match"]
        
        # 5. 可用性匹配 (10%)
        availability_score = self._calculate_availability_match(project, provider)
        score += availability_score * self.weights["availability_match"]
        
        return min(score, 100.0)
    
    async def _calculate_skill_match(self, project: Project, provider: ProviderProfile) -> float:
        """计算技能匹配分数"""
        if not project.required_skills or not provider.skills:
            return 50.0  # 默认分数
        
        # 获取项目所需技能
        project_skill_ids = set(project.required_skills)
        
        # 获取供给方技能
        provider_skill_ids = set(str(ps.skill_id) for ps in provider.skills)
        
        # 计算匹配比例
        if not project_skill_ids:
            return 50.0
        
        matched_skills = project_skill_ids.intersection(provider_skill_ids)
        match_ratio = len(matched_skills) / len(project_skill_ids)
        
        # 根据熟练度调整分数
        proficiency_bonus = 0
        for ps in provider.skills:
            if str(ps.skill_id) in matched_skills:
                if ps.proficiency_level == "EXPERT":
                    proficiency_bonus += 10
                elif ps.proficiency_level == "ADVANCED":
                    proficiency_bonus += 5
        
        # 限制熟练度加成
        proficiency_bonus = min(proficiency_bonus, 20)
        
        return min(match_ratio * 100 + proficiency_bonus, 100.0)
    
    def _calculate_experience_match(self, project: Project, provider: ProviderProfile) -> float:
        """计算经验匹配分数"""
        if not project.preferred_experience or not provider.years_of_experience:
            return 50.0  # 默认分数
        
        # 经验要求映射
        experience_map = {
            "JUNIOR": 1,
            "MID": 3,
            "SENIOR": 5,
            "EXPERT": 8
        }
        
        required_years = experience_map.get(project.preferred_experience, 0)
        actual_years = provider.years_of_experience or 0
        
        # 计算匹配分数
        if actual_years >= required_years:
            # 经验充足，分数基于超出程度
            excess_ratio = min((actual_years - required_years) / required_years, 1.0)
            return 70 + excess_ratio * 30  # 70-100分
        else:
            # 经验不足，分数基于差距
            deficit_ratio = (required_years - actual_years) / required_years
            return max(50 - deficit_ratio * 50, 0)  # 0-50分
    
    def _calculate_budget_match(self, project: Project, provider: ProviderProfile) -> float:
        """计算预算匹配分数"""
        if not project.budget_max or not provider.hourly_rate:
            return 50.0  # 默认分数
        
        # 估算项目工时
        # 假设项目预算基于小时费率
        estimated_hours = project.budget_max / provider.hourly_rate if provider.hourly_rate > 0 else 0
        
        # 合理工时范围：20-200小时
        if 20 <= estimated_hours <= 200:
            # 理想范围，高分
            if 40 <= estimated_hours <= 160:
                return 90.0
            else:
                return 70.0
        elif estimated_hours < 20:
            # 工时太少，可能不适合
            return 30.0
        else:
            # 工时太多，可能需要团队
            return 40.0
    
    def _calculate_location_match(self, project: Project, provider: ProviderProfile) -> float:
        """计算地点匹配分数"""
        if not project.location_preference or project.location_preference == "ANY":
            return 100.0  # 无地点要求
        
        # 这里简化处理，实际应该根据用户的位置信息进行匹配
        # 目前假设所有供给方都支持远程工作
        if project.location_preference == "REMOTE":
            return 100.0
        elif project.location_preference == "HYBRID":
            return 80.0
        else:  # ONSITE
            return 50.0
    
    def _calculate_availability_match(self, project: Project, provider: ProviderProfile) -> float:
        """计算可用性匹配分数"""
        if provider.availability == "AVAILABLE":
            return 100.0
        elif provider.availability == "BUSY":
            return 50.0
        else:  # UNAVAILABLE
            return 0.0
    
    async def _get_match_reasons(self, project: Project, provider: ProviderProfile) -> List[str]:
        """获取匹配原因"""
        reasons = []
        
        # 技能匹配原因
        if project.required_skills and provider.skills:
            project_skill_ids = set(project.required_skills)
            provider_skill_ids = set(str(ps.skill_id) for ps in provider.skills)
            matched_skills = project_skill_ids.intersection(provider_skill_ids)
            
            if matched_skills:
                # 获取技能名称
                skill_names = []
                for ps in provider.skills:
                    if str(ps.skill_id) in matched_skills:
                        skill_names.append(ps.skill.name)
                
                if skill_names:
                    reasons.append(f"掌握所需技能：{', '.join(skill_names[:3])}")
        
        # 经验匹配原因
        if project.preferred_experience and provider.years_of_experience:
            experience_map = {"JUNIOR": 1, "MID": 3, "SENIOR": 5, "EXPERT": 8}
            required_years = experience_map.get(project.preferred_experience, 0)
            
            if provider.years_of_experience >= required_years:
                reasons.append(f"拥有{provider.years_of_experience}年经验，超过要求的{required_years}年")
        
        # 预算匹配原因
        if project.budget_max and provider.hourly_rate:
            estimated_hours = project.budget_max / provider.hourly_rate if provider.hourly_rate > 0 else 0
            if 40 <= estimated_hours <= 160:
                reasons.append("预算与工作量匹配良好")
        
        # 可用性原因
        if provider.availability == "AVAILABLE":
            reasons.append("目前可用，可以立即开始")
        
        # 评分原因
        if provider.average_rating and provider.average_rating >= 4.5:
            reasons.append(f"平均评分{provider.average_rating}分，表现优秀")
        
        # 成功率原因
        if provider.success_rate and provider.success_rate >= 90:
            reasons.append(f"项目成功率{provider.success_rate}%，可靠性高")
        
        return reasons
    
    async def calculate_provider_match_score(self, project_id: str, provider_id: str) -> Optional[float]:
        """计算特定供给方与项目的匹配分数"""
        # 获取项目
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        
        if not project:
            return None
        
        # 获取供给方
        result = await self.db.execute(
            select(ProviderProfile)
            .options(
                selectinload(ProviderProfile.user),
                selectinload(ProviderProfile.skills).selectinload(ProviderSkill.skill),
                selectinload(ProviderProfile.industry_expertise)
            )
            .where(ProviderProfile.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            return None
        
        # 计算匹配分数
        return await self._calculate_match_score(project, provider)
    
    async def get_top_matches_for_provider(self, provider_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取供给方的最佳匹配项目"""
        # 获取供给方
        result = await self.db.execute(
            select(ProviderProfile)
            .options(
                selectinload(ProviderProfile.user),
                selectinload(ProviderProfile.skills).selectinload(ProviderSkill.skill),
                selectinload(ProviderProfile.industry_expertise)
            )
            .where(ProviderProfile.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            return []
        
        # 获取开放状态的项目
        result = await self.db.execute(
            select(Project)
            .where(Project.status == "OPEN")
            .order_by(Project.created_at.desc())
            .limit(100)  # 限制查询数量
        )
        projects = result.scalars().all()
        
        # 计算匹配分数
        matches = []
        for project in projects:
            match_score = await self._calculate_match_score(project, provider)
            
            if match_score >= 50:
                match_reasons = await self._get_match_reasons(project, provider)
                
                matches.append({
                    "project_id": str(project.id),
                    "project_title": project.title,
                    "project_type": project.project_type,
                    "budget_min": float(project.budget_min),
                    "budget_max": float(project.budget_max),
                    "match_score": match_score,
                    "match_reasons": match_reasons,
                    "deadline": project.deadline.isoformat() if project.deadline else None,
                    "is_urgent": project.is_urgent
                })
        
        # 按匹配分数排序
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        return matches[:limit]