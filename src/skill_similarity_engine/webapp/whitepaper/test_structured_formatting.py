#!/usr/bin/env python3
"""
Test script to demonstrate structured formatting approach.
This shows how the new system eliminates hardcoded keywords and works with any role comparison.
"""

from formatter import ContentFormatter


def test_structured_formatting():
    """Demonstrate structured formatting with different job roles."""
    
    print("🚀 Testing Structured Content Formatting")
    print("=" * 50)
    
    # Test 1: Data Scientist to Machine Learning Engineer
    print("\n📊 Test 1: Data Scientist Career Pathways")
    
    data_scientist_recommendations = [
        {
            'target_logical_role': 'Machine Learning Engineer (Group 2)',
            'similarity_score': 78.3,
            'move_type': 'Progression - Different_Role_Higher_Level',
            'strategic_context_explanation': 'Leverages existing analytical skills while expanding into production ML systems'
        },
        {
            'target_logical_role': 'Senior Data Analyst (Group 2)', 
            'similarity_score': 71.2,
            'move_type': 'Progression - Same_Role_Higher_Level',
            'strategic_context_explanation': 'Direct career progression within data analytics domain'
        }
    ]
    
    # Generate structured content for data scientist
    data_scientist_content = generate_recommendations_content(
        data_scientist_recommendations,
        bold_labels=['Move Type:', 'Strategic Context:']
    )
    
    print("Generated structured content:")
    print("Text:", data_scientist_content['text'])
    print("Formatting metadata:", data_scientist_content['formatting'])
    
    # Test 2: Software Engineer to DevOps Engineer  
    print("\n💻 Test 2: Software Engineer Career Pathways")
    
    software_engineer_recommendations = [
        {
            'target_logical_role': 'DevOps Engineer (Group 2)',
            'similarity_score': 69.8,
            'move_type': 'Lateral - Different_Role_Same_Level',
            'strategic_context_explanation': 'Applies coding skills to infrastructure automation and deployment'
        },
        {
            'target_logical_role': 'Technical Lead (Group 3)',
            'similarity_score': 65.4, 
            'move_type': 'Progression - Different_Role_Higher_Level',
            'strategic_context_explanation': 'Combines technical expertise with leadership responsibilities'
        }
    ]
    
    # Generate structured content for software engineer
    software_engineer_content = generate_recommendations_content(
        software_engineer_recommendations,
        bold_labels=['Move Type:', 'Strategic Context:']
    )
    
    print("Generated structured content:")
    print("Text:", software_engineer_content['text'])
    print("Formatting metadata:", software_engineer_content['formatting'])
    
    # Test 3: Custom labels for different domain
    print("\n🏦 Test 3: Financial Analyst with Custom Labels")
    
    financial_analyst_recommendations = [
        {
            'target_logical_role': 'Investment Advisor (Group 2)',
            'similarity_score': 72.1,
            'move_type': 'Lateral - Different_Role_Same_Level',
            'risk_assessment': 'Low transition risk with strong skill overlap',
            'training_required': 'Financial planning certification needed'
        }
    ]
    
    # Generate with custom labels for financial domain
    financial_content = generate_recommendations_content(
        financial_analyst_recommendations,
        bold_labels=['Move Type:', 'Risk Assessment:', 'Training Required:']
    )
    
    print("Generated structured content with custom labels:")
    print("Text:", financial_content['text'])
    print("Formatting metadata:", financial_content['formatting'])
    
    print("\n✅ Key Benefits of Structured Approach:")
    print("1. No hardcoded job titles or keywords")
    print("2. Works with any role comparison dynamically")
    print("3. Explicit formatting metadata from content generators")
    print("4. Consistent formatting regardless of content")
    print("5. Easy to extend with new label types")


def generate_recommendations_content(recommendations, bold_labels):
    """
    Generate structured recommendations content using the new ContentFormatter.
    This replaces the hardcoded keyword approach.
    """
    
    recommendation_items = []
    
    for i, recommendation in enumerate(recommendations, 1):
        # Create main recommendation header
        header = f"{recommendation.get('target_logical_role', 'Unknown Role')} - {recommendation.get('similarity_score', 0)}% similarity"
        
        # Create detail items dynamically based on available data
        details = []
        
        # Standard fields
        if 'move_type' in recommendation:
            details.append(f"Move Type: {recommendation['move_type']}")
        
        if 'strategic_context_explanation' in recommendation:
            details.append(f"Strategic Context: {recommendation['strategic_context_explanation']}")
        
        # Custom fields (demonstrates flexibility)
        if 'risk_assessment' in recommendation:
            details.append(f"Risk Assessment: {recommendation['risk_assessment']}")
            
        if 'training_required' in recommendation:
            details.append(f"Training Required: {recommendation['training_required']}")
        
        # Create the full recommendation text
        recommendation_text = header
        if details:
            detail_bullets = '\n'.join([f"- {detail}" for detail in details])
            recommendation_text += f"\n{detail_bullets}"
        
        recommendation_items.append(recommendation_text)
    
    # Create structured content
    if recommendation_items:
        # Combine all recommendations
        full_text = ""
        for i, item in enumerate(recommendation_items, 1):
            full_text += f"{i}. {item}"
            if i < len(recommendation_items):
                full_text += "\n\n"
        
        # Return structured content with explicit formatting metadata
        return ContentFormatter.create_formatted_content(
            full_text,
            {
                'content_type': 'mixed',
                'bold_labels': bold_labels,
                'bold_numbered_headers': True
            }
        )
    else:
        return ContentFormatter.create_paragraph(
            "No pathway recommendations available for this analysis.",
            []
        )


if __name__ == "__main__":
    test_structured_formatting() 