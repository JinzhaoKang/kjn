"""
LLM洞察生成演示脚本
展示如何使用简化的LLM洞察生成功能
"""
import asyncio
import os
import json
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.insights.llm_insight_generator import LLMInsightGenerator

async def run_demo():
    """运行演示"""
    print("=== LLM洞察生成演示 ===")
    print(f"开始时间: {datetime.now()}")
    
    # 配置LLM
    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        "openai_base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    }
    
    if config["openai_api_key"] == "your-api-key-here":
        print("⚠️  请设置环境变量 OPENAI_API_KEY")
        print("演示将使用模拟数据运行...")
        
    # 创建洞察生成器
    generator = LLMInsightGenerator(config)
    
    # 准备演示反馈数据
    demo_feedback = [
        {
            "id": "demo_1",
            "text": "登录页面加载太慢，经常超时，影响使用体验",
            "filter_result": {
                "sentiment": "negative",
                "category": "performance",
                "priority_score": 0.8,
                "extracted_keywords": ["登录", "加载", "超时", "性能"]
            }
        },
        {
            "id": "demo_2", 
            "text": "希望能增加暗黑模式，长时间使用眼睛很累",
            "filter_result": {
                "sentiment": "neutral",
                "category": "feature",
                "priority_score": 0.6,
                "extracted_keywords": ["暗黑模式", "护眼", "界面"]
            }
        },
        {
            "id": "demo_3",
            "text": "移动端界面太小，按钮点击困难，建议优化",
            "filter_result": {
                "sentiment": "negative",
                "category": "ui_ux",
                "priority_score": 0.7,
                "extracted_keywords": ["移动端", "界面", "按钮", "优化"]
            }
        },
        {
            "id": "demo_4",
            "text": "数据导出功能很好用，但希望支持更多格式",
            "filter_result": {
                "sentiment": "positive",
                "category": "feature",
                "priority_score": 0.5,
                "extracted_keywords": ["数据导出", "格式", "功能"]
            }
        },
        {
            "id": "demo_5",
            "text": "搜索功能不够智能，找不到想要的内容",
            "filter_result": {
                "sentiment": "negative", 
                "category": "functionality",
                "priority_score": 0.75,
                "extracted_keywords": ["搜索", "智能", "内容"]
            }
        },
        {
            "id": "demo_6",
            "text": "系统经常崩溃，严重影响工作效率",
            "filter_result": {
                "sentiment": "negative",
                "category": "stability",
                "priority_score": 0.9,
                "extracted_keywords": ["系统", "崩溃", "效率"]
            }
        },
        {
            "id": "demo_7",
            "text": "客服响应速度很快，解决问题很及时",
            "filter_result": {
                "sentiment": "positive",
                "category": "service",
                "priority_score": 0.3,
                "extracted_keywords": ["客服", "响应", "及时"]
            }
        },
        {
            "id": "demo_8",
            "text": "报表功能缺少自定义选项，希望能增加更多筛选条件",
            "filter_result": {
                "sentiment": "neutral",
                "category": "feature",
                "priority_score": 0.65,
                "extracted_keywords": ["报表", "自定义", "筛选"]
            }
        }
    ]
    
    print(f"\n📊 分析{len(demo_feedback)}条用户反馈...")
    
    try:
        # 第一步：生成洞察
        print("\n🔍 第一步：生成洞察...")
        insights = await generator.generate_insights_from_feedback(demo_feedback)
        
        if insights:
            print(f"✅ 成功生成{len(insights)}个洞察:")
            for i, insight in enumerate(insights, 1):
                print(f"\n洞察 {i}:")
                print(f"  标题: {insight.title}")
                print(f"  类型: {insight.insight_type}")
                print(f"  影响级别: {insight.impact_level}")
                print(f"  置信度: {insight.confidence_score:.2f}")
                print(f"  描述: {insight.description[:100]}...")
                print(f"  业务影响: {insight.business_impact[:100]}...")
        else:
            print("❌ 未能生成洞察")
            return
        
        # 第二步：生成执行计划
        print("\n📋 第二步：生成执行计划...")
        feedback_context = {
            "total_feedback": len(demo_feedback),
            "business_context": "产品用户体验优化",
            "analysis_date": datetime.now().isoformat(),
            "focus_areas": ["性能优化", "界面改进", "功能增强"]
        }
        
        action_plans = await generator.generate_action_plans_from_insights(insights, feedback_context)
        
        if action_plans:
            print(f"✅ 成功生成{len(action_plans)}个执行计划:")
            for i, plan in enumerate(action_plans, 1):
                print(f"\n执行计划 {i}:")
                print(f"  标题: {plan.title}")
                print(f"  优先级: {plan.priority}")
                print(f"  预估工作量: {plan.estimated_effort}")
                print(f"  时间线: {plan.timeline}")
                print(f"  负责团队: {plan.owner_team}")
                print(f"  概要: {plan.summary[:100]}...")
                print(f"  预期结果: {plan.expected_outcome[:100]}...")
                
                if plan.action_steps:
                    print(f"  执行步骤:")
                    for step in plan.action_steps[:3]:  # 显示前3个步骤
                        print(f"    {step.get('step', 'N/A')}: {step.get('description', 'N/A')}")
        else:
            print("❌ 未能生成执行计划")
            return
            
        # 第三步：生成综合报告
        print("\n📄 第三步：生成综合报告...")
        
        # 统计信息
        sentiment_stats = {}
        category_stats = {}
        priority_stats = {"high": 0, "medium": 0, "low": 0}
        
        for feedback in demo_feedback:
            # 情感统计
            sentiment = feedback["filter_result"]["sentiment"]
            sentiment_stats[sentiment] = sentiment_stats.get(sentiment, 0) + 1
            
            # 类别统计
            category = feedback["filter_result"]["category"]
            category_stats[category] = category_stats.get(category, 0) + 1
            
            # 优先级统计
            priority_score = feedback["filter_result"]["priority_score"]
            if priority_score >= 0.7:
                priority_stats["high"] += 1
            elif priority_score >= 0.5:
                priority_stats["medium"] += 1
            else:
                priority_stats["low"] += 1
        
        print("\n📈 反馈数据统计:")
        print(f"  情感分布: {sentiment_stats}")
        print(f"  类别分布: {category_stats}")
        print(f"  优先级分布: {priority_stats}")
        
        print(f"\n🎯 洞察分析结果:")
        insight_types = {}
        impact_levels = {}
        for insight in insights:
            insight_types[insight.insight_type] = insight_types.get(insight.insight_type, 0) + 1
            impact_levels[insight.impact_level] = impact_levels.get(insight.impact_level, 0) + 1
        
        print(f"  洞察类型分布: {insight_types}")
        print(f"  影响级别分布: {impact_levels}")
        
        print(f"\n📊 执行计划统计:")
        plan_priorities = {}
        team_distribution = {}
        for plan in action_plans:
            plan_priorities[plan.priority] = plan_priorities.get(plan.priority, 0) + 1
            team_distribution[plan.owner_team] = team_distribution.get(plan.owner_team, 0) + 1
        
        print(f"  优先级分布: {plan_priorities}")
        print(f"  团队分布: {team_distribution}")
        
        # 保存结果到文件
        print(f"\n💾 保存结果...")
        
        result_data = {
            "generation_time": datetime.now().isoformat(),
            "feedback_analyzed": len(demo_feedback),
            "insights_generated": len(insights),
            "action_plans_generated": len(action_plans),
            "statistics": {
                "sentiment_distribution": sentiment_stats,
                "category_distribution": category_stats,
                "priority_distribution": priority_stats,
                "insight_types": insight_types,
                "impact_levels": impact_levels,
                "plan_priorities": plan_priorities,
                "team_distribution": team_distribution
            },
            "insights": [
                {
                    "title": insight.title,
                    "description": insight.description,
                    "insight_type": insight.insight_type,
                    "confidence_score": insight.confidence_score,
                    "impact_level": insight.impact_level,
                    "business_impact": insight.business_impact,
                    "supporting_evidence": insight.supporting_evidence,
                    "affected_user_segments": insight.affected_user_segments
                }
                for insight in insights
            ],
            "action_plans": [
                {
                    "title": plan.title,
                    "summary": plan.summary,
                    "priority": plan.priority,
                    "estimated_effort": plan.estimated_effort,
                    "timeline": plan.timeline,
                    "owner_team": plan.owner_team,
                    "success_metrics": plan.success_metrics,
                    "action_steps": plan.action_steps,
                    "risk_assessment": plan.risk_assessment,
                    "expected_outcome": plan.expected_outcome
                }
                for plan in action_plans
            ]
        }
        
        # 保存到JSON文件
        output_file = f"llm_insights_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n=== 演示完成 ===")
    print(f"结束时间: {datetime.now()}")

def main():
    """主函数"""
    print("LLM洞察生成演示")
    print("这是一个简化的演示，展示如何使用LLM生成洞察和执行计划")
    print("\n要使用真实的LLM功能，请设置环境变量:")
    print("export OPENAI_API_KEY='your-api-key'")
    print("export OPENAI_BASE_URL='https://api.openai.com/v1'")
    print("\n开始演示...")
    
    # 运行异步演示
    asyncio.run(run_demo())

if __name__ == "__main__":
    main() 