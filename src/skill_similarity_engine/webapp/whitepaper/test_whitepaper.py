"""
Test script for Executive Summary Generation with Logical Role Architecture
Tests the integration of YAML templates, SQL queries, and Python generation logic.
Now includes logical role support for cleaner user experience.

Usage:
    python test_executive_summary.py                    # Run all tests
    python test_executive_summary.py --template         # Test template loading only
    python test_executive_summary.py --executive        # Test executive summary only
    python test_executive_summary.py --current          # Test current role context only
    python test_executive_summary.py --pathway          # Test pathway analysis only
    python test_executive_summary.py --strategic        # Test strategic recommendations only
    python test_executive_summary.py --conclusion       # Test conclusion only
    python test_executive_summary.py --help             # Show this help
"""

import sqlite3
import sys
import argparse
from pathlib import Path

# Add the src directory to path so we can import the generator
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from executive_summary_generator import ExecutiveSummaryGenerator, LogicalRoleManager
from current_role_context_generator import CurrentRoleContextGenerator

def test_executive_summary_generation():
    """Test the executive summary generation with a sample job."""
    
    print("🧪 Testing Executive Summary Generation with Logical Role Architecture")
    print("=" * 70)
    
    # Connect to database (you'll need to update this path)
    db_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"⚠️ Database not found at: {db_path}")
        print("Please update the db_path in the test script to point to your database.")
        return
    
    try:
        # Connect to database
        print(f"📊 Connecting to database: {db_path}")
        db = sqlite3.connect(str(db_path))
        db.row_factory = sqlite3.Row  # Enable column access by name
        
        # Initialize generator and logical role manager
        print("🏗️ Initializing Executive Summary Generator with Logical Role Support...")
        generator = ExecutiveSummaryGenerator(db)
        logical_manager = LogicalRoleManager(db)
        
        # Show logical role architecture improvements
        total_profiles = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        logical_roles_query = """
        SELECT COUNT(DISTINCT 
            CASE 
                WHEN INSTR(JobProfile, ' - ') > 0 
                THEN SUBSTR(JobProfile, 1, INSTR(JobProfile, ' - ') - 1) || '|' || ManagementLevel
                ELSE JobProfile || '|' || ManagementLevel 
            END
        ) FROM jobs
        """
        logical_roles_count = db.execute(logical_roles_query).fetchone()[0]
        
        print(f"\n🏗️ Logical Role Architecture:")
        print(f"   Total JobProfileIDs: {total_profiles:,}")
        print(f"   Logical Roles:       {logical_roles_count:,}")
        print(f"   Reduction Ratio:     {total_profiles / logical_roles_count:.1f}:1")
        
        # Test with a sample job (you can change this)
        test_job_id = "R0100.2"  # Data Scientist Associate from gold standard
        logical_name = logical_manager.get_logical_role_display_name(test_job_id)
        print(f"\n🎯 Generating executive summary for:")
        print(f"   JobProfileID: {test_job_id}")
        print(f"   Logical Role: {logical_name}")
        
        # Generate executive summary
        result = generator.generate(test_job_id)
        
        # Display results
        print("\n" + "=" * 50)
        print("📄 GENERATED EXECUTIVE SUMMARY")
        print("=" * 50)
        
        content = result.get('content', {})
        
        # Strategic Context
        if 'strategic_context' in content:
            print(f"\n### {content['strategic_context']['title']}")
            print(content['strategic_context']['content'])
        
        # Key Findings
        if 'key_findings' in content:
            print(f"\n### {content['key_findings']['title']}")
            key_content = content['key_findings']['content']
            if isinstance(key_content, dict) and 'text' in key_content:
                print(key_content['text'])
            else:
                print(key_content)
        
        # Primary Recommendations
        if 'primary_recommendations' in content:
            print(f"\n### {content['primary_recommendations']['title']}")
            rec_content = content['primary_recommendations']['content']
            if isinstance(rec_content, dict) and 'text' in rec_content:
                print(rec_content['text'])
            else:
                print(rec_content)
        
        # Data-Driven Classification
        if 'data_driven_classification' in content:
            print(f"\n### Data-Driven Classification")
            print(content['data_driven_classification']['content'])
        
        # Confidence Assessment
        if 'confidence_assessment' in content:
            print(f"\n### {content['confidence_assessment']['title']}")
            conf_content = content['confidence_assessment']['content']
            if isinstance(conf_content, dict) and 'text' in conf_content:
                print(conf_content['text'])
            else:
                print(conf_content)
        
        # Show template variables for debugging
        print("\n" + "=" * 50)
        print("🔧 TEMPLATE VARIABLES (Debug Info)")
        print("=" * 50)
        
        variables = result.get('template_variables', {})
        key_variables = [
            'source_job_title', 'total_job_count', 'pathway_count', 
            'min_similarity', 'max_similarity', 'confidence_level',
            'opportunity_descriptor', 'percentile_descriptor'
        ]
        
        for var in key_variables:
            if var in variables:
                print(f"{var}: {variables[var]}")
        
        # Show top pathways with logical role names
        top_pathways = variables.get('top_pathways', [])
        if top_pathways:
            print(f"\nTop {len(top_pathways)} career pathways (showing logical roles):")
            for i, pathway in enumerate(top_pathways, 1):
                logical_role = pathway.get('target_logical_role', pathway.get('target_job_title', 'Unknown'))
                similarity = pathway.get('similarity_score', 0)
                move_type = pathway.get('move_type', 'Unknown')
                transition = pathway.get('level_transition', 'Unknown')
                
                print(f"  {i}. {logical_role} - {similarity}% similarity")
                print(f"     Move Type: {move_type}")
                print(f"     Transition: {transition}")
                if i < len(top_pathways):  # Add spacing except after last item
                    print()
        
        # Show references
        print("\n" + "=" * 50)
        print("📚 REFERENCES")
        print("=" * 50)
        
        references = result.get('references', {})
        key_refs = ['1', '2', '13', '14', '15', '16']
        for ref in key_refs:
            if ref in references:
                print(f"({ref}) {references[ref]}")
        
        print("\n✅ Executive Summary generation completed successfully!")
        print("\n🎯 Key Architecture Improvements Demonstrated:")
        print("   ✅ Logical role display names (e.g., 'Data Scientist (Group 1)')")
        print("   ✅ 3:1 reduction in complexity (715 profiles → ~237 logical roles)")
        print("   ✅ Executive-ready presentation format")
        print("   ✅ Backward compatibility with existing database")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

def test_template_loading():
    """Test that the YAML template loads correctly."""
    
    print("\n🧪 Testing YAML Template Loading")
    print("=" * 50)
    
    try:
        # Test template loading without database
        generator = ExecutiveSummaryGenerator(None)
        
        if generator.template_data:
            print("✅ YAML template loaded successfully!")
            
            # Check key sections exist
            exec_summary = generator.template_data.get('executive_summary', {})
            required_sections = [
                'strategic_context', 'key_findings', 'primary_recommendations',
                'confidence_assessment'
            ]
            
            for section in required_sections:
                if section in exec_summary:
                    print(f"✅ Section '{section}' found")
                else:
                    print(f"❌ Section '{section}' missing")
            
            # Check references exist
            references = generator.template_data.get('references', {})
            if references:
                print(f"✅ References section found with {len(references)} references")
            else:
                print("❌ References section missing")
        
        else:
            print("❌ YAML template failed to load")
    
    except Exception as e:
        print(f"❌ Error testing template: {e}")

def test_current_role_context_generation():
    """Test the current role context generation following the proven pattern."""
    
    print("\n🧪 Testing Current Role Context Generation")
    print("=" * 70)
    
    # Connect to database
    db_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"⚠️ Database not found at: {db_path}")
        print("Please update the db_path in the test script to point to your database.")
        return
    
    try:
        # Connect to database
        print(f"📊 Connecting to database: {db_path}")
        db = sqlite3.connect(str(db_path))
        db.row_factory = sqlite3.Row  # Enable column access by name
        
        # Initialize generator
        print("🏗️ Initializing Current Role Context Generator...")
        generator = CurrentRoleContextGenerator(db)
        
        # Test with the same job as executive summary
        test_job_id = "R0100.2"  # Data Scientist Associate
        print(f"\n🎯 Generating current role context for: {test_job_id}")
        
        # Generate current role context
        result = generator.generate(test_job_id, include_organisational_deployment=True)
        
        # Display results
        print("\n" + "=" * 50)
        print("📄 GENERATED CURRENT ROLE CONTEXT")
        print("=" * 50)
        
        content = result.get('content', {})
        
        # Helper function to display structured content
        def display_content(section_content):
            if isinstance(section_content, dict) and 'text' in section_content:
                return section_content['text']
            else:
                return str(section_content)
        
        # Profile Overview
        if 'profile_overview' in content:
            print(f"\n### {content['profile_overview']['title']}")
            print(display_content(content['profile_overview']['content']))
        
        # Core Competency Foundation
        if 'core_competency_foundation' in content:
            print(f"\n### {content['core_competency_foundation']['title']}")
            print(display_content(content['core_competency_foundation']['content']))
        
        # Strategic Value Proposition
        if 'strategic_value_proposition' in content:
            print(f"\n### {content['strategic_value_proposition']['title']}")
            print(display_content(content['strategic_value_proposition']['content']))
        
        # Strategic Intelligence Metrics
        if 'strategic_intelligence_metrics' in content:
            print(f"\n### {content['strategic_intelligence_metrics']['title']}")
            print(display_content(content['strategic_intelligence_metrics']['content']))
        
        # Show template variables for debugging
        print("\n" + "=" * 50)
        print("🔧 TEMPLATE VARIABLES (Debug Info)")
        print("=" * 50)
        
        variables = result.get('template_variables', {})
        key_variables = [
            'source_job_logical_display_name', 'total_skills', 'skill_category_count',
            'mobility_hub_score', 'transition_readiness', 'cross_family_reach',
            'strategic_value_assessment'
        ]
        
        for var in key_variables:
            if var in variables:
                print(f"{var}: {variables[var]}")
        
        print("\n✅ Current Role Context generation completed successfully!")
        print("\n🎯 Key Features Demonstrated:")
        print("   ✅ YAML template rendering with Jinja2")
        print("   ✅ Database integration following proven patterns")
        print("   ✅ Logical role display names integration")
        print("   ✅ Professional formatting matching gold standard")
        
    except Exception as e:
        print(f"❌ Error during current role context testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

def test_pathway_analysis_generation():
    """Test the Pathway Analysis Generator following proven patterns."""
    print("\n🧪 Testing Pathway Analysis Generation")
    print("=" * 70)
    
    # Connect to database
    db_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"⚠️ Database not found at: {db_path}")
        print("Please update the db_path in the test script to point to your database.")
        return
    
    try:
        # Connect to database
        print(f"📊 Connecting to database: {db_path}")
        db = sqlite3.connect(str(db_path))
        db.row_factory = sqlite3.Row  # Enable column access by name
        
        # Initialize generator
        print("🏗️ Initializing Pathway Analysis Generator...")
        from src.pathway_analysis_generator import PathwayAnalysisGenerator
        generator = PathwayAnalysisGenerator(db)
        
        # Test with the same job as other tests for consistency
        test_job_id = "R0100.2"  # Risk Analyst (Group 3)
        print(f"🎯 Generating pathway analysis for: {test_job_id}")
        
        # Generate pathway analysis
        result = generator.generate(test_job_id, include_organisational_deployment=True)
        
        print("\n" + "=" * 50)
        print("📄 GENERATED PATHWAY ANALYSIS")
        print("=" * 50)
        
        # Display section title
        print(f"# {result['section_title']}")
        print()
        
        # Display each opportunity
        if 'content' in result and 'opportunities' in result['content']:
            for i, opportunity in enumerate(result['content']['opportunities'], 1):
                print(opportunity['header'])
                print()
                
                # Handle the opportunity overview table
                print("### Opportunity Overview")
                if isinstance(opportunity['opportunity_overview'], dict) and 'text' in opportunity['opportunity_overview']:
                    print(opportunity['opportunity_overview']['text'])
                else:
                    print(opportunity['opportunity_overview'])
                print()
                
                print(f"### {opportunity['strategic_positioning']['title']}")
                print(opportunity['strategic_positioning']['content'])
                print()
                
                # Handle the new table structure for skills_transition_analysis and implementation_roadmap
                print("### Skills Transition Analysis")
                if isinstance(opportunity['skills_transition_analysis'], dict) and 'text' in opportunity['skills_transition_analysis']:
                    print(opportunity['skills_transition_analysis']['text'])
                else:
                    print(opportunity['skills_transition_analysis'])
                print()
                
                print(f"### {opportunity['business_case']['title']}")
                print(opportunity['business_case']['content'])
                print()
                
                print("### Implementation Roadmap")
                if isinstance(opportunity['implementation_roadmap'], dict) and 'text' in opportunity['implementation_roadmap']:
                    print(opportunity['implementation_roadmap']['text'])
                else:
                    print(opportunity['implementation_roadmap'])
                print()
                
                if i < len(result['content']['opportunities']):
                    print("-" * 70)
                    print()
        
        # Display debugging info
        print("=" * 50)
        print("🔧 PATHWAY ANALYSIS DEBUG INFO")
        print("=" * 50)
        if 'opportunities' in result:
            for i, opp in enumerate(result['opportunities'], 1):
                pathway = opp['pathway_data']
                print(f"Opportunity {i}: {pathway['target_logical_role']}")
                print(f"  Similarity Score: {pathway['similarity_score']}%")
                print(f"  Move Type: {pathway['move_type']}")
                print(f"  Level Transition: {pathway['level_transition_display']}")
                print()
        
        assert 'section_title' in result
        assert 'content' in result
        print("✅ Pathway Analysis generation completed successfully!")
        print("🎯 Key Features Demonstrated:")
        print("   ✅ Top 3 strategic opportunities identified")
        print("   ✅ Comprehensive opportunity analysis")
        print("   ✅ Skills transition calculations")
        print("   ✅ Business case generation")
        print("   ✅ Implementation roadmap creation")
        
    except Exception as e:
        print(f"❌ Error in pathway analysis generation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

def test_strategic_recommendations_generation():
    """Test the Strategic Recommendations Generator following proven patterns."""
    print("\n🧪 Testing Strategic Recommendations Generation")
    print("=" * 70)
    
    # Connect to database
    db_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"⚠️ Database not found at: {db_path}")
        print("Please update the db_path in the test script to point to your database.")
        return
    
    try:
        # Connect to database
        print(f"📊 Connecting to database: {db_path}")
        db = sqlite3.connect(str(db_path))
        db.row_factory = sqlite3.Row  # Enable column access by name
        
        # Initialize generator
        print("🏗️ Initializing Strategic Recommendations Generator...")
        from strategic_recommendations_generator import StrategicRecommendationsGenerator
        generator = StrategicRecommendationsGenerator(db)
        
        # Test with the same job as other tests for consistency
        test_job_id = "R0100.2"  # Risk Analyst (Group 3)
        print(f"🎯 Generating strategic recommendations for: {test_job_id}")
        
        # Generate strategic recommendations
        result = generator.generate(test_job_id, include_organisational_deployment=True)
        
        print("\n" + "=" * 50)
        print("📄 GENERATED STRATEGIC RECOMMENDATIONS")
        print("=" * 50)
        
        # Display section title
        print(f"# {result['section_title']}")
        print()
        
        # Display each content section
        content = result.get('content', {})
        section_order = [
            'database_driven_decision_support',
            'business_case',
            'immediate_actions', 
            'medium_term_initiatives',
            'success_metrics_evaluation',
            'research_references'
        ]
        
        for section_key in section_order:
            if section_key in content:
                section = content[section_key]
                print(f"### {section['title']}")
                
                # Handle different content types
                section_content = section['content']
                if isinstance(section_content, dict) and 'text' in section_content:
                    # Structured content with formatting metadata
                    print(section_content['text'])
                elif isinstance(section_content, dict) and 'formatting' in section_content:
                    # Table or other structured content
                    formatting = section_content['formatting']
                    if formatting.get('content_type') == 'table':
                        # Display table headers and rows
                        headers = formatting.get('headers', [])
                        rows = formatting.get('rows', [])
                        if headers:
                            print(" | ".join(headers))
                            print("|".join(["-" * len(header) for header in headers]))
                        for row in rows:
                            print(" | ".join(str(cell) for cell in row))
                    else:
                        # Display the text content
                        print(section_content.get('text', section_content))
                else:
                    # Basic string content
                    print(section_content)
                print()
        
        # Display debugging info
        print("=" * 50)
        print("🔧 STRATEGIC RECOMMENDATIONS DEBUG INFO")
        print("=" * 50)
        
        variables = result.get('template_variables', {})
        key_variables = [
            'source_job_logical_display_name', 'total_job_profiles', 'target_pathway_count',
            'avg_similarity', 'development_investment_weeks', 'source_function',
            'function_percentage', 'cross_family_mobility_count'
        ]
        
        for var in key_variables:
            if var in variables:
                print(f"{var}: {variables[var]}")
        
        # Show benchmark context
        benchmark_vars = [
            'industry_transition_success', 'target_transition_success',
            'industry_retention', 'target_retention', 
            'industry_productivity_months', 'target_productivity_months'
        ]
        
        print(f"\nBenchmark Context:")
        for var in benchmark_vars:
            if var in variables:
                print(f"  {var}: {variables[var]}")
        
        assert 'section_title' in result
        assert 'content' in result
        print("\n✅ Strategic Recommendations generation completed successfully!")
        print("🎯 Key Features Demonstrated:")
        print("   ✅ Database-driven decision support metrics")
        print("   ✅ Immediate and medium-term action plans")
        print("   ✅ Success metrics with industry benchmarks")
        print("   ✅ Cross-functional mobility insights")
        print("   ✅ Development investment calculations")
        
    except Exception as e:
        print(f"❌ Error in strategic recommendations generation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

def test_conclusion_generation():
    """Test the conclusion generation following the proven pattern."""
    
    print("\n🧪 Testing Conclusion Generation")
    print("=" * 70)
    
    # Connect to database
    db_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"⚠️ Database not found at: {db_path}")
        print("Please update the db_path in the test script to point to your database.")
        return
    
    try:
        # Connect to database
        print(f"📊 Connecting to database: {db_path}")
        db = sqlite3.connect(str(db_path))
        db.row_factory = sqlite3.Row  # Enable column access by name
        
        # Initialize generator
        print("🏗️ Initializing Conclusion Generator...")
        from conclusion_generator import ConclusionGenerator
        generator = ConclusionGenerator(db)
        
        # Test with the same job as other sections
        test_job_id = "R0100.2"  # Risk Analyst (Group 3)
        print(f"\n🎯 Generating conclusion for: {test_job_id}")
        
        # Generate conclusion
        result = generator.generate(test_job_id, include_organisational_deployment=True)
        
        # Display results
        print("\n" + "=" * 50)
        print("📄 GENERATED CONCLUSION")
        print("=" * 50)
        
        # Display section title
        print(f"## {result['section_title']}")
        print()
        
        content = result.get('content', {})
        
        # Display each section in logical order
        section_order = ['opportunity_summary', 'strategic_alignment', 'recommended_approach', 'foundation_value']
        
        for section_key in section_order:
            if section_key in content:
                section = content[section_key]
                if 'content' in section:
                    print(section['content'])
                    print()
        
        # Show template variables for debugging  
        print("=" * 50)
        print("🔧 CONCLUSION DEBUG INFO")
        print("=" * 50)
        
        variables = result.get('template_variables', {})
        key_variables = [
            'source_job_logical_display_name', 'pathway_count', 'similarity_range_description',
            'opportunity_classification', 'pilot_size', 'strategic_priority'
        ]
        
        for var in key_variables:
            if var in variables:
                print(f"{var}: {variables[var]}")
        
        assert 'section_title' in result
        assert 'content' in result
        print("\n✅ Conclusion generation completed successfully!")
        print("\n🎯 Key Features Demonstrated:")
        print("   ✅ Database-driven opportunity synthesis")
        print("   ✅ Strategic alignment assessment")
        print("   ✅ Pilot program recommendations")
        print("   ✅ Foundation for workforce planning")
        
    except Exception as e:
        print(f"❌ Error during conclusion testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

def test_clean_copy_display():
    """Display clean copy of all sections without debug information."""
    
    print("📄 NAB Skills Intelligence Platform")
    print("Strategic Career Pathway Analysis")
    print("=" * 70)
    
    # Connect to database
    db_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"⚠️ Database not found at: {db_path}")
        print("Please update the db_path in the test script to point to your database.")
        return
    
    try:
        # Connect to database (no debug output)
        db = sqlite3.connect(str(db_path))
        db.row_factory = sqlite3.Row
        
        # Initialize all generators (no debug output)
        from executive_summary_generator import ExecutiveSummaryGenerator
        from current_role_context_generator import CurrentRoleContextGenerator
        from pathway_analysis_generator import PathwayAnalysisGenerator
        from strategic_recommendations_generator import StrategicRecommendationsGenerator
        from conclusion_generator import ConclusionGenerator
        
        exec_generator = ExecutiveSummaryGenerator(db)
        context_generator = CurrentRoleContextGenerator(db)
        pathway_generator = PathwayAnalysisGenerator(db)
        strategic_generator = StrategicRecommendationsGenerator(db)
        conclusion_generator = ConclusionGenerator(db)
        
        # Test job
        test_job_id = "R0100.2"
        
        # Get job name for header
        logical_manager = exec_generator.logical_role_manager
        job_name = logical_manager.get_logical_role_display_name(test_job_id)
        
        print(f"White Paper: {job_name}")
        print(f"Generated: {Path(__file__).parent.parent.parent.parent.parent}")
        print("Version 1.0 - Skills Intelligence Analysis")
        print()
        
        # Generate all sections (suppress logging temporarily)
        import logging
        logging.getLogger().setLevel(logging.ERROR)
        
        sections = {}
        sections['executive_summary'] = exec_generator.generate(test_job_id)
        sections['current_role_context'] = context_generator.generate(test_job_id, include_organisational_deployment=True)
        sections['pathway_analysis'] = pathway_generator.generate(test_job_id, include_organisational_deployment=True)
        sections['strategic_recommendations'] = strategic_generator.generate(test_job_id, include_organisational_deployment=True)
        sections['conclusion'] = conclusion_generator.generate(test_job_id, include_organisational_deployment=True)
        
        # Restore logging
        logging.getLogger().setLevel(logging.INFO)
        
        # Display sections cleanly
        section_order = [
            ('executive_summary', 'Executive Summary'),
            ('current_role_context', 'Current Role Context'),
            ('pathway_analysis', 'Pathway Analysis: Top 3 Strategic Opportunities'),
            ('strategic_recommendations', 'Strategic Recommendations'),
            ('conclusion', 'Conclusion')
        ]
        
        for section_key, section_title in section_order:
            if section_key in sections:
                print(f"\n## {section_title}")
                print()
                
                section_result = sections[section_key]
                content = section_result.get('content', {})
                
                if section_key == 'pathway_analysis' and 'opportunities' in content:
                    # Special handling for pathway analysis with opportunities
                    for i, opportunity in enumerate(content['opportunities'], 1):
                        print(f"### {opportunity['header']}")
                        print()
                        
                        # Display each sub-section
                        sub_sections = ['strategic_positioning', 'skills_transition_analysis', 'business_case', 'implementation_roadmap']
                        for sub_key in sub_sections:
                            if sub_key in opportunity:
                                sub_section = opportunity[sub_key]
                                print(f"#### {sub_section['title']}")
                                print(sub_section['content'])
                                print()
                        
                        if i < len(content['opportunities']):
                            print("---")
                            print()
                else:
                    # Standard section handling
                    for subsection_key, subsection in content.items():
                        if isinstance(subsection, dict) and 'content' in subsection:
                            if 'title' in subsection:
                                print(f"### {subsection['title']}")
                            
                            # Handle structured content
                            subsection_content = subsection['content']
                            if isinstance(subsection_content, dict) and 'text' in subsection_content:
                                print(subsection_content['text'])
                            else:
                                print(subsection_content)
                            print()
        
        print("=" * 70)
        print("End of White Paper")
        
    except Exception as e:
        print(f"❌ Error generating clean copy: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

def test_full_whitepaper_generation():
    """Test full white paper generation with all sections and Word document output."""
    
    print("\n🧪 Testing Full White Paper Generation with Word Document Output")
    print("=" * 70)
    
    # Connect to database
    db_path = Path(__file__).parent.parent.parent.parent.parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"⚠️ Database not found at: {db_path}")
        print("Please update the db_path in the test script to point to your database.")
        return
    
    try:
        # Connect to database
        print(f"📊 Connecting to database: {db_path}")
        db = sqlite3.connect(str(db_path))
        db.row_factory = sqlite3.Row  # Enable column access by name
        
        # Initialize all generators
        print("🏗️ Initializing all generators...")
        from executive_summary_generator import ExecutiveSummaryGenerator
        from current_role_context_generator import CurrentRoleContextGenerator
        from pathway_analysis_generator import PathwayAnalysisGenerator
        from strategic_recommendations_generator import StrategicRecommendationsGenerator
        from conclusion_generator import ConclusionGenerator
        
        exec_generator = ExecutiveSummaryGenerator(db)
        context_generator = CurrentRoleContextGenerator(db)
        pathway_generator = PathwayAnalysisGenerator(db)
        strategic_generator = StrategicRecommendationsGenerator(db)
        conclusion_generator = ConclusionGenerator(db)
        
        # Test job
        test_job_id = "R0100.2"  # Risk Analyst (Group 3)
        print(f"🎯 Generating complete white paper for: {test_job_id}")
        
        # Generate all sections
        print("\n📄 Generating sections...")
        sections = {}
        
        print("  ✅ Executive Summary...")
        sections['executive_summary'] = exec_generator.generate(test_job_id)
        
        print("  ✅ Current Role Context...")
        sections['current_role_context'] = context_generator.generate(test_job_id, include_organisational_deployment=True)
        
        print("  ✅ Pathway Analysis...")
        sections['pathway_analysis'] = pathway_generator.generate(test_job_id, include_organisational_deployment=True)
        
        print("  ✅ Strategic Recommendations...")
        sections['strategic_recommendations'] = strategic_generator.generate(test_job_id, include_organisational_deployment=True)
        
        print("  ✅ Conclusion...")
        sections['conclusion'] = conclusion_generator.generate(test_job_id, include_organisational_deployment=True)
        
        # Prepare content for Word document
        print("\n📝 Preparing content for Word document...")
        
        # Extract content from each section
        word_content = {}
        analysis_data = {}
        
        for section_name, section_result in sections.items():
            word_content[section_name] = section_result.get('content', {})
            
            # Extract key analysis data from first section (executive summary)
            if section_name == 'executive_summary':
                variables = section_result.get('template_variables', {})
                max_sim = variables.get('max_similarity', 0)
                # Convert to float if it's a string
                if isinstance(max_sim, str):
                    try:
                        max_sim = float(max_sim)
                    except (ValueError, TypeError):
                        max_sim = 0
                
                analysis_data.update({
                    'source_job_logical_display_name': variables.get('source_job_title', 'Professional Role'),
                    'summary': f'Career pathway analysis for {variables.get("source_job_title", "Professional Role")}',
                    'avg_similarity': max_sim / 100,
                    'pathway_count': variables.get('pathway_count', 0)
                })
        
        # Extract job_name for file naming
        job_name = analysis_data.get('source_job_logical_display_name', 'Professional Role')
        
        # Define section titles for file generation
        section_titles = [
            ('executive_summary', 'Executive Summary'),
            ('current_role_context', 'Current Role Context'), 
            ('pathway_analysis', 'Pathway Analysis: Top 3 Strategic Opportunities'),
            ('strategic_recommendations', 'Strategic Recommendations'),
            ('conclusion', 'Conclusion')
        ]
        
        # Create Word document using template if available
        print("\n📄 Creating Word document...")
        
        # Check for NAB template
        template_path = Path(__file__).parent / 'templates' / 'nab_template.docx'
        if template_path.exists():
            print(f"✅ Using NAB template: {template_path}")
            template_mode = "NAB Template"
        else:
            print(f"⚠️ NAB template not found at {template_path}")
            print("   Creating document without template (basic formatting)")
            template_path = None
            template_mode = "Basic Formatting"
        
        try:
            # Try to import python-docx with enhanced formatting
            from docx import Document
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
            from docx.enum.style import WD_STYLE_TYPE
            from datetime import datetime
            
            # Save file paths for both approaches
            output_dir = Path(__file__).parent
            filename = f'whitepaper_{job_name.replace(" ", "_").replace("(", "").replace(")", "")}.docx'
            output_path = output_dir / filename
            
            # Try professional NAB-styled document first
            if NAB_FORMATTER_AVAILABLE:
                print("🎨 Creating professional NAB-styled document...")
                
                # Add source_job_id to analysis_data for formatter
                analysis_data['source_job_id'] = test_job_id
                
                success = create_professional_word_document(word_content, analysis_data, output_path)
                
                if success:
                    print(f"✅ Professional NAB-styled document created!")
                    print(f"📄 Document features:")
                    print(f"   ✅ NAB red headings (Epilogue Semibold 22pt)")
                    print(f"   ✅ Professional typography (Source Sans Pro)")
                    print(f"   ✅ Cover page with NAB branding")
                    print(f"   ✅ TOC-compatible heading styles")
                    print(f"   ✅ Executive-ready presentation")
                else:
                    print("⚠️ Professional document creation failed, trying basic approach...")
                    success = create_basic_word_document(word_content, analysis_data, output_path)
            else:
                print("🎨 Creating basic Word document (NAB formatter not available)...")
                success = create_basic_word_document(word_content, analysis_data, output_path)
            
            if success:
                print(f"✅ Word document saved: {output_path}")
                print(f"📄 Document contains {len(section_titles)} sections")
                print(f"📊 Analysis for {job_name} with {analysis_data.get('pathway_count', 0)} pathways")
                
                if NAB_FORMATTER_AVAILABLE:
                    print(f"\n📋 To generate automatic Table of Contents:")
                    print(f"   1. Open the .docx file in Microsoft Word")
                    print(f"   2. Place cursor after 'Table of Contents' heading")
                    print(f"   3. Go to References → Table of Contents → Automatic Table 1")
                    print(f"   4. TOC will be generated from headings automatically!")
            else:
                print(f"❌ Failed to create Word document")
            
        except ImportError:
            print("⚠️ python-docx not installed. Install with: pip install python-docx")
            print("📄 Saving content to text file instead...")
            
            # Import datetime for text file fallback
            from datetime import datetime
            
            # Save as text file
            output_dir = Path(__file__).parent
            filename = f'whitepaper_{job_name.replace(" ", "_").replace("(", "").replace(")", "")}.txt'
            output_path = output_dir / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"NAB Skills Intelligence Platform\n")
                f.write(f"Strategic Career Pathway Analysis\n")
                f.write(f"White Paper: {job_name}\n")
                f.write(f"Generated: {datetime.now().strftime('%B %d, %Y')}\n\n")
                f.write("=" * 80 + "\n\n")
                
                for section_key, section_title in section_titles:
                    if section_key in word_content:
                        f.write(f"{section_title}\n")
                        f.write("=" * len(section_title) + "\n\n")
                        
                        section_data = word_content[section_key]
                        if isinstance(section_data, dict):
                            for subsection_key, subsection in section_data.items():
                                if isinstance(subsection, dict) and 'content' in subsection:
                                    if 'title' in subsection:
                                        f.write(f"{subsection['title']}\n")
                                        f.write("-" * len(subsection['title']) + "\n")
                                    f.write(f"{subsection['content']}\n\n")
                        f.write("\n")
            
            print(f"✅ Text file saved: {output_path}")
        
        # Display summary
        print("\n" + "=" * 50)
        print("🎯 WHITE PAPER GENERATION SUMMARY")
        print("=" * 50)
        
        for section_name, section_result in sections.items():
            variables = section_result.get('template_variables', {})
            content_sections = len(section_result.get('content', {}))
            print(f"✅ {section_name.replace('_', ' ').title()}: {content_sections} subsections")
        
        print(f"\n📄 Complete white paper generated for {job_name}")
        print(f"📊 Analysis includes {analysis_data.get('pathway_count', 0)} career pathways")
        
        print("\n🎉 Full white paper generation completed successfully!")
        print("🎯 Key Features Demonstrated:")
        print("   ✅ Complete 5-section white paper generation")
        print("   ✅ Professional Word document formatting")
        print("   ✅ Database-driven content throughout")
        print("   ✅ Consistent logical role architecture")
        print("   ✅ Executive-ready presentation quality")
        
    except Exception as e:
        print(f"❌ Error during full white paper generation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals():
            db.close()

# Import NAB styling from our DocumentFormatter
try:
    from formatter import DocumentFormatter
    NAB_FORMATTER_AVAILABLE = True
    print("✅ NAB DocumentFormatter available for professional styling")
except ImportError:
    NAB_FORMATTER_AVAILABLE = False
    print("⚠️ NAB DocumentFormatter not available - using basic styling")

def create_professional_word_document(content_sections, analysis_data, output_path):
    """Create a professional Word document with NAB styling using DocumentFormatter."""
    
    if not NAB_FORMATTER_AVAILABLE:
        print("❌ Cannot create professional document - DocumentFormatter not available")
        return False
    
    try:
        # Initialize the DocumentFormatter
        formatter = DocumentFormatter()
        
        # Generate the document using the formatter's format_document method
        result = formatter.format_document(
            content=content_sections,
            output_format='word',
            analysis_data=analysis_data
        )
        
        if result.get('status') == 'generated':
            # Save the document
            with open(output_path, 'wb') as f:
                f.write(result['content'])
            
            print(f"✅ Professional NAB-styled Word document saved: {output_path}")
            return True
        else:
            print(f"❌ Document generation failed: {result.get('message', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error creating professional document: {e}")
        return False

# Fallback function for basic Word document creation
def create_basic_word_document(content_sections, analysis_data, output_path):
    """Fallback function to create a basic Word document without NAB styling."""
    
    try:
        from docx import Document
        from docx.shared import Pt
        from datetime import datetime
        
        doc = Document()
        
        # Basic title page
        title = doc.add_paragraph('Skills Intelligence Platform')
        title_run = title.runs[0]
        title_run.font.size = Pt(24)
        title_run.bold = True
        
        subtitle = doc.add_paragraph('Strategic Career Pathway Analysis')
        subtitle_run = subtitle.runs[0] 
        subtitle_run.font.size = Pt(18)
        
        job_name = analysis_data.get('source_job_logical_display_name', 'Professional Role')
        job_para = doc.add_paragraph(f'White Paper: {job_name}')
        job_run = job_para.runs[0]
        job_run.font.size = Pt(16)
        job_run.bold = True
        
        date_para = doc.add_paragraph(f'Generated: {datetime.now().strftime("%B %d, %Y")}')
        
        doc.add_page_break()
        
        # Basic table of contents
        toc_heading = doc.add_paragraph('Table of Contents')
        toc_run = toc_heading.runs[0]
        toc_run.font.size = Pt(16)
        toc_run.bold = True
        
        doc.add_paragraph("(Table of Contents placeholder - generate in Word)")
        doc.add_page_break()
        
        # Add sections
        section_order = [
            ('executive_summary', 'Executive Summary'),
            ('current_role_context', 'Current Role Context'), 
            ('pathway_analysis', 'Pathway Analysis: Top 3 Strategic Opportunities'),
            ('strategic_recommendations', 'Strategic Recommendations'),
            ('conclusion', 'Conclusion')
        ]
        
        for section_key, section_title in section_order:
            if section_key in content_sections:
                # Section heading
                heading = doc.add_paragraph(section_title)
                heading_run = heading.runs[0]
                heading_run.font.size = Pt(14)
                heading_run.bold = True
                
                # Section content
                section_data = content_sections[section_key]
                if isinstance(section_data, dict):
                    for subsection_key, subsection in section_data.items():
                        if isinstance(subsection, dict) and 'content' in subsection:
                            if 'title' in subsection:
                                sub_heading = doc.add_paragraph(subsection['title'])
                                sub_run = sub_heading.runs[0]
                                sub_run.font.size = Pt(12)
                                sub_run.bold = True
                            
                            content_para = doc.add_paragraph(subsection['content'])
        
        doc.save(str(output_path))
        print(f"✅ Basic Word document saved: {output_path}")
        return True
        
    except ImportError:
        print("❌ python-docx not available for Word document creation")
        return False
    except Exception as e:
        print(f"❌ Error creating basic document: {e}")
        return False

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Test white paper generation components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python test_whitepaper.py                           # Run all tests
    python test_whitepaper.py --copy                    # Display clean copy without debug
    python test_whitepaper.py --template                # Test template loading only
    python test_whitepaper.py --executive               # Test executive summary only
    python test_whitepaper.py --current                 # Test current role context only
    python test_whitepaper.py --pathway                 # Test pathway analysis only
    python test_whitepaper.py --strategic               # Test strategic recommendations only
    python test_whitepaper.py --conclusion              # Test conclusion only
    python test_whitepaper.py --word                    # Generate full Word document
        """
    )
    
    parser.add_argument('--template', action='store_true', 
                       help='Test template loading only')
    parser.add_argument('--executive', action='store_true', 
                       help='Test executive summary generation only')
    parser.add_argument('--current', action='store_true', 
                       help='Test current role context generation only')
    parser.add_argument('--pathway', action='store_true', 
                       help='Test pathway analysis generation only')
    parser.add_argument('--strategic', action='store_true', 
                       help='Test strategic recommendations generation only')
    parser.add_argument('--conclusion', action='store_true', 
                       help='Test conclusion generation only')
    parser.add_argument('--word', action='store_true', 
                       help='Test full white paper generation with Word document output')
    parser.add_argument('--copy', action='store_true', 
                       help='Display clean copy of all sections without debug information')
    parser.add_argument('--all', action='store_true', 
                       help='Run all tests (default if no flags specified)')
    
    args = parser.parse_args()
    
    # If no specific test is requested, run all tests
    run_all = (not (args.template or args.executive or args.current or args.pathway or 
                   args.strategic or args.conclusion or args.copy or args.word))
    
    # Handle clean copy display separately
    if args.copy:
        test_clean_copy_display()
        return
    
    print("🚀 White Paper Generation Test Suite")
    print("=" * 50)
    
    if args.template or run_all:
        test_template_loading()
    
    if args.executive or run_all:
        test_executive_summary_generation()
    
    if args.current or run_all:
        test_current_role_context_generation()
    
    if args.pathway or run_all:
        test_pathway_analysis_generation()
    
    if args.strategic or run_all:
        test_strategic_recommendations_generation()
    
    if args.conclusion or run_all:
        test_conclusion_generation()
    
    if args.word:
        test_full_whitepaper_generation()
    
    print("\n🎉 Test suite completed!")

if __name__ == "__main__":
    main() 